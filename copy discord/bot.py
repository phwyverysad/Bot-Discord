import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import asyncio
import aiohttp
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อม
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ตั้งค่าบอต Intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ตรวจสอบการสร้างโฟลเดอร์สำหรับแบคอัพ
os.makedirs("backups", exist_ok=True)

# พจนานุกรมเก็บงานที่กำลังรันอยู่แยกตามเซิร์ฟเวอร์ (สำหรับใช้ยกเลิก/หยุดคัดลอก)
active_clones = {}

# ฟังก์ชันดาวน์โหลดภาพโปรไฟล์ / แบนเนอร์
async def download_image(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดาวน์โหลดรูปภาพจาก {url}: {e}")
    return None

# ฟังก์ชันแปลงข้อมูลเซิร์ฟเวอร์เป็น Dictionary สำหรับแบคอัพ
def guild_to_dict(guild: discord.Guild) -> dict:
    data = {
        "name": guild.name,
        "verification_level": str(guild.verification_level),
        "icon_url": guild.icon.url if guild.icon else None,
        "banner_url": guild.banner.url if guild.banner else None,
        "roles": [],
        "categories": []
    }
    
    # บันทึก Roles
    for role in guild.roles:
        if role.is_default() or role.managed:
            continue
        data["roles"].append({
            "id": role.id,
            "name": role.name,
            "permissions": role.permissions.value,
            "color": role.color.value,
            "hoist": role.hoist,
            "mentionable": role.mentionable,
            "position": role.position
        })
        
    # จัดกลุ่ม Channels ตามหมวดหมู่ (Categories)
    categories = [c for c in guild.channels if isinstance(c, discord.CategoryChannel)]
    category_map = {}
    
    for cat in categories:
        cat_data = {
            "name": cat.name,
            "position": cat.position,
            "id": cat.id,
            "channels": [],
            "overwrites": []
        }
        # บันทึกสิทธิ์หมวดหมู่
        for target, overwrite in cat.overwrites.items():
            allow, deny = overwrite.pair()
            ow_data = {"allow": allow.value, "deny": deny.value}
            if isinstance(target, discord.Role):
                ow_data["type"] = "default" if target.is_default() else "role"
                ow_data["name"] = target.name
                ow_data["id"] = target.id
            elif isinstance(target, discord.Member):
                ow_data["type"] = "member"
                ow_data["id"] = target.id
            cat_data["overwrites"].append(ow_data)
            
        category_map[cat.id] = cat_data
        data["categories"].append(cat_data)
        
    # ช่องแชทที่ไม่อยู่ในหมวดหมู่ใด ๆ
    uncategorized = {
        "name": None,
        "position": 0,
        "id": None,
        "channels": []
    }
    data["categories"].append(uncategorized)
    
    # บันทึกห้องแชทและสิทธิ์
    for channel in guild.channels:
        if isinstance(channel, discord.CategoryChannel):
            continue
            
        ch_data = {
            "name": channel.name,
            "position": channel.position,
            "type": "text" if isinstance(channel, discord.TextChannel) else "voice" if isinstance(channel, discord.VoiceChannel) else "text",
            "nsfw": getattr(channel, "nsfw", False),
            "slowmode_delay": getattr(channel, "slowmode_delay", 0),
            "topic": getattr(channel, "topic", None),
            "overwrites": []
        }
        
        for target, overwrite in channel.overwrites.items():
            allow, deny = overwrite.pair()
            ow_data = {"allow": allow.value, "deny": deny.value}
            if isinstance(target, discord.Role):
                ow_data["type"] = "default" if target.is_default() else "role"
                ow_data["name"] = target.name
                ow_data["id"] = target.id
            elif isinstance(target, discord.Member):
                ow_data["type"] = "member"
                ow_data["id"] = target.id
            ch_data["overwrites"].append(ow_data)
            
        if channel.category_id in category_map:
            category_map[channel.category_id]["channels"].append(ch_data)
        else:
            uncategorized["channels"].append(ch_data)
            
    return data

# คัดลอกสิทธิ์การใช้งานลงในห้องแชทเป้าหมาย
async def apply_channel_overwrites_from_dict(ch_overwrites, target_ch, target_guild, role_map):
    overwrites = {}
    for ow in ch_overwrites:
        allow = discord.Permissions(ow["allow"])
        deny = discord.Permissions(ow["deny"])
        ow_pair = discord.PermissionOverwrite.from_pair(allow, deny)
        
        if ow["type"] == "default":
            overwrites[target_guild.default_role] = ow_pair
        elif ow["type"] == "role":
            # ค้นหายศที่สร้างขึ้นใหม่โดยเทียบตามชื่อ
            role = role_map.get(ow["name"])
            if role:
                overwrites[role] = ow_pair
        elif ow["type"] == "member":
            member = target_guild.get_member(ow["id"])
            if member:
                overwrites[member] = ow_pair
                
    if overwrites:
        try:
            await target_ch.edit(overwrites=overwrites)
        except Exception as e:
            print(f"ไม่สามารถกำหนดสิทธิ์ให้กับห้อง {target_ch.name} ได้: {e}")

# ใช้สำหรับบอตไลฟ์คัดลอกจาก Guild ไปยัง Guild
async def apply_channel_overwrites(source_ch, target_ch, target_guild, role_map):
    overwrites = {}
    for target, ow in source_ch.overwrites.items():
        if isinstance(target, discord.Role):
            if target.is_default():
                overwrites[target_guild.default_role] = ow
            else:
                new_role = role_map.get(target.id)
                if new_role:
                    overwrites[new_role] = ow
        elif isinstance(target, discord.Member):
            member = target_guild.get_member(target.id)
            if member:
                overwrites[member] = ow
                
    if overwrites:
        try:
            await target_ch.edit(overwrites=overwrites)
        except Exception as e:
            print(f"ไม่สามารถกำหนดสิทธิ์ให้กับห้อง {target_ch.name} ได้: {e}")

# อัปเดตและแสดงความคืบหน้าการทำงานเป็นภาษาไทย
async def update_progress_embed(interaction: discord.Interaction, title: str, step: str, current: int, total: int, details: str = "", color=discord.Color.gold()):
    try:
        bar_len = 15
        filled = int(bar_len * current / total) if total > 0 else bar_len
        bar = "█" * filled + "░" * (bar_len - filled)
        pct = int(current / total * 100) if total > 0 else 100
        
        emb = discord.Embed(
            title=title,
            description=f"**ขั้นตอนปัจจุบัน**: {step}\n`{bar}` **{pct}%** ({current}/{total})\n\n{details}",
            color=color
        )
        emb.set_footer(text="บอตกำลังทำงานแบบคู่ขนานเพื่อความรวดเร็วสูงสุด...")
        await interaction.edit_original_response(content=None, embed=emb)
    except Exception as e:
        print(f"พบข้อผิดพลาดในการอัปเดตหน้าความคืบหน้า: {e}")

# ฟังก์ชันประมวลผลการโคลนแบบคู่ขนาน (Concurrent Cloning)
async def run_clone(interaction: discord.Interaction, bot, source_guild, target_guild, config):
    try:
        # 1. แบคอัพข้อมูลเซิร์ฟเวอร์เดิมไว้ก่อน
        await update_progress_embed(interaction, "⚡ กำลังคัดลอกเซิร์ฟเวอร์...", "สร้างจุดกู้คืนความปลอดภัย (Backup Snapshot)", 0, 1, "บันทึกข้อมูลยศและห้องเดิม...")
        backup_data = guild_to_dict(target_guild)
        with open(f"backups/{target_guild.id}_undo.json", "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=4, ensure_ascii=False)
        await update_progress_embed(interaction, "⚡ กำลังคัดลอกเซิร์ฟเวอร์...", "สร้างจุดกู้คืนความปลอดภัย (Backup Snapshot)", 1, 1, "บันทึกข้อมูลเรียบร้อยแล้ว!")
        await asyncio.sleep(1)

        # 2. ทำการเคลียร์ห้องและยศเดิม (ยกเว้นห้องที่ใช้รันคำสั่ง) - ในที่นี้ระบบการโคลนปกติเราปิดการลบไว้ตามคำขอ แต่ใส่ระบบเผื่อไว้
        if config["clean_target"]:
            channels_to_del = [c for c in target_guild.channels if c.id != interaction.channel_id]
            roles_to_del = [r for r in target_guild.roles if not r.is_default() and not r.managed]
            
            await update_progress_embed(interaction, "⚡ กำลังเคลียร์เซิร์ฟเวอร์...", "ลบข้อมูลห้องและยศเดิมพร้อมกันทั้งหมด...", 0, 1, f"กำลังลบช่องแชท {len(channels_to_del)} ช่อง และยศ {len(roles_to_del)} ยศ...")
            
            async def delete_channel_task(ch):
                try:
                    await ch.delete()
                except:
                    pass
            async def delete_role_task(r):
                try:
                    await r.delete()
                except:
                    pass
            
            await asyncio.gather(
                *(delete_channel_task(ch) for ch in channels_to_del),
                *(delete_role_task(r) for r in roles_to_del)
            )

        # 3. คัดลอกเอกลักษณ์ (รูป/แบนเนอร์/ชื่อ)
        if config["copy_identity"]:
            await update_progress_embed(interaction, "⚡ กำลังคัดลอกเซิร์ฟเวอร์...", "คัดลอกรูปภาพและชื่อเซิร์ฟเวอร์", 0, 1, "กำลังตั้งค่ารูปโปรไฟล์และแบนเนอร์...")
            try:
                guild_kwargs = {"name": source_guild.name}
                if source_guild.icon:
                    icon_bytes = await download_image(source_guild.icon.url)
                    if icon_bytes:
                        guild_kwargs["icon"] = icon_bytes
                if source_guild.banner:
                    banner_bytes = await download_image(source_guild.banner.url)
                    if banner_bytes:
                        guild_kwargs["banner"] = banner_bytes
                await target_guild.edit(**guild_kwargs)
            except Exception as e:
                print(f"ไม่สามารถแก้ไขโปรไฟล์เซิร์ฟเวอร์ได้: {e}")

        # 4. สร้างยศและหมวดหมู่แบบคู่ขนานสูงสุด (เฟสที่ 1)
        role_tasks = []
        roles_to_create = []
        if config["copy_roles"]:
            roles_to_create = [r for r in source_guild.roles if not r.is_default() and not r.managed]
            async def create_role_task(role):
                try:
                    new_role = await target_guild.create_role(
                        name=role.name,
                        permissions=role.permissions,
                        color=role.color,
                        hoist=role.hoist,
                        mentionable=role.mentionable
                    )
                    role_map[role.id] = new_role
                except Exception as e:
                    print(f"สร้างยศ {role.name} ล้มเหลว: {e}")
            for r in roles_to_create:
                role_tasks.append(create_role_task(r))

        cat_tasks = []
        categories = []
        if config["copy_channels"]:
            categories = sorted([c for c in source_guild.channels if isinstance(c, discord.CategoryChannel)], key=lambda x: x.position)
            async def create_cat_task(cat):
                try:
                    new_cat = await target_guild.create_category(name=cat.name, position=cat.position)
                    category_map[cat.id] = new_cat
                except Exception as e:
                    print(f"สร้างหมวดหมู่ {cat.name} ล้มเหลว: {e}")
            for cat in categories:
                cat_tasks.append(create_cat_task(cat))

        if role_tasks or cat_tasks:
            await update_progress_embed(interaction, "⚡ กำลังคัดลอกเซิร์ฟเวอร์...", "สร้างยศและหมวดหมู่ทั้งหมดในเวลาเดียวกัน", 0, 1, f"กำลังสร้างยศ {len(role_tasks)} ยศ และหมวดหมู่ {len(cat_tasks)} หมวดหมู่...")
            await asyncio.gather(*role_tasks, *cat_tasks)

            # อัปเดตสิทธิ์ (Overwrites) ของหมวดหมู่หลังจากได้ยศครบแล้ว
            if config["copy_channels"] and categories:
                cat_overwrite_tasks = []
                async def apply_cat_ow(cat):
                    new_cat = category_map.get(cat.id)
                    if new_cat:
                        await apply_channel_overwrites(cat, new_cat, target_guild, role_map)
                for cat in categories:
                    cat_overwrite_tasks.append(apply_cat_ow(cat))
                await asyncio.gather(*cat_overwrite_tasks)

        # 5. สร้างช่องแชทและช่องคุยเสียงพร้อมสิทธิ์แบบคู่ขนานสูงสุด (เฟสที่ 2)
        if config["copy_channels"]:
            text_channels = sorted([c for c in source_guild.channels if isinstance(c, discord.TextChannel)], key=lambda x: x.position)
            voice_channels = sorted([c for c in source_guild.channels if isinstance(c, discord.VoiceChannel)], key=lambda x: x.position)
            total_channels_to_create = len(text_channels) + len(voice_channels) - (1 if any(ch.id == interaction.channel_id for ch in text_channels) else 0)

            await update_progress_embed(interaction, "⚡ กำลังคัดลอกเซิร์ฟเวอร์...", "สร้างช่องแชทและช่องคุยเสียงทั้งหมดพร้อมกันในทีเดียว", 0, 1, f"กำลังสร้างห้องแชทและช่องคุยเสียงทั้งหมด {total_channels_to_create} ช่อง...")

            async def create_channel_task(ch, is_text):
                try:
                    parent_cat = category_map.get(ch.category_id) if ch.category_id else None
                    if is_text:
                        new_ch = await target_guild.create_text_channel(
                            name=ch.name,
                            category=parent_cat,
                            position=ch.position,
                            topic=ch.topic,
                            nsfw=ch.nsfw,
                            slowmode_delay=ch.slowmode_delay
                        )
                    else:
                        new_ch = await target_guild.create_voice_channel(
                            name=ch.name,
                            category=parent_cat,
                            position=ch.position
                        )
                    await apply_channel_overwrites(ch, new_ch, target_guild, role_map)
                except Exception as e:
                    print(f"สร้างห้อง {ch.name} ล้มเหลว: {e}")

            tasks = []
            for ch in text_channels:
                if ch.id == interaction.channel_id:
                    continue
                tasks.append(create_channel_task(ch, is_text=True))
            for ch in voice_channels:
                tasks.append(create_channel_task(ch, is_text=False))
                
            await asyncio.gather(*tasks)

        # ทำงานเสร็จสมบูรณ์
        active_clones.pop(target_guild.id, None)
        embed = discord.Embed(
            title="🎉 คัดลอกเซิร์ฟเวอร์เสร็จสมบูรณ์!",
            description="บอตได้ดำเนินการย้ายและสร้างโครงสร้างเซิร์ฟเวอร์เป้าหมายเรียบร้อยแล้ว",
            color=discord.Color.green()
        )
        embed.add_field(name="การย้อนกลับ (Rollback)", value="หากมีบางอย่างผิดพลาด คุณสามารถพิมพ์คำสั่ง `/undo` เพื่อคืนค่าทั้งหมดได้ทันที", inline=False)
        await interaction.edit_original_response(embed=embed, view=None)

    except asyncio.CancelledError:
        # จัดการกรณีผู้ใช้กดปุ่ม หยุด (Stop)
        active_clones.pop(target_guild.id, None)
        embed = discord.Embed(
            title="🛑 การคัดลอกถูกหยุดทำงาน!",
            description="กระบวนการคัดลอกถูกขัดจังหวะและยุติการทำงานตามคำสั่งของผู้ใช้งานเรียบร้อยแล้ว",
            color=discord.Color.red()
        )
        embed.add_field(name="ข้อมูลการสำรอง", value="คุณสามารถใช้คำสั่ง `/undo` เพื่อกู้คืนสถานะเซิร์ฟเวอร์กลับไปก่อนเริ่มงานได้", inline=False)
        await interaction.edit_original_response(embed=embed, view=None)

    except Exception as e:
        active_clones.pop(target_guild.id, None)
        emb = discord.Embed(
            title="❌ เกิดข้อผิดพลาดในการคัดลอก",
            description=f"เกิดปัญหาระหว่างคัดลอกเซิร์ฟเวอร์: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=emb, view=None)

# ฟังก์ชันประมวลผลย้อนกลับ/กู้คืนแบบคู่ขนาน (Concurrent Undo)
async def run_undo(interaction: discord.Interaction, bot, target_guild):
    try:
        backup_path = f"backups/{target_guild.id}_undo.json"
        if not os.path.exists(backup_path):
            await interaction.edit_original_response(content="❌ ไม่พบไฟล์ประวัติการแบคอัพสำรองของเซิร์ฟเวอร์นี้", embed=None, view=None)
            return

        with open(backup_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        await update_progress_embed(interaction, "🔄 กำลังย้อนกลับสถานะเซิร์ฟเวอร์...", "อ่านไฟล์สำรองข้อมูล", 0, 1, "กำลังเตรียมข้อมูลสำหรับกู้คืน...")
        await asyncio.sleep(1)

        # 1. เคลียร์ข้อมูลทั้งหมดในเซิร์ฟเวอร์เป้าหมายยกเว้นห้องสั่งงาน (แบบคู่ขนานสูงสุด)
        channels_to_del = [c for c in target_guild.channels if c.id != interaction.channel_id]
        roles_to_del = [r for r in target_guild.roles if not r.is_default() and not r.managed]
        
        await update_progress_embed(interaction, "🔄 กำลังย้อนกลับสถานะเซิร์ฟเวอร์...", "ล้างข้อมูลยศและห้องแชทเดิมทั้งหมดพร้อมกัน", 0, 1, f"กำลังลบห้อง {len(channels_to_del)} ห้อง และยศ {len(roles_to_del)} ยศ...")
        
        async def delete_channel_task(ch):
            try:
                await ch.delete()
            except:
                pass
        async def delete_role_task(r):
            try:
                await r.delete()
            except:
                pass
                
        await asyncio.gather(
            *(delete_channel_task(ch) for ch in channels_to_del),
            *(delete_role_task(r) for r in roles_to_del)
        )

        # 2. กู้คืนรูปภาพ/ชื่อเซิร์ฟเวอร์
        try:
            guild_kwargs = {"name": data["name"]}
            if data.get("icon_url"):
                icon_bytes = await download_image(data["icon_url"])
                if icon_bytes:
                    guild_kwargs["icon"] = icon_bytes
            else:
                guild_kwargs["icon"] = None
                
            if data.get("banner_url"):
                banner_bytes = await download_image(data["banner_url"])
                if banner_bytes:
                    guild_kwargs["banner"] = banner_bytes
            else:
                guild_kwargs["banner"] = None
                
            await target_guild.edit(**guild_kwargs)
        except Exception as e:
            print(f"ไม่สามารถกู้คืนภาพโปรไฟล์ได้: {e}")

        # 3. กู้คืนยศและหมวดหมู่แบบคู่ขนานสูงสุด (เฟสที่ 1)
        role_map = {}
        role_tasks = []
        async def create_role_task(role_data):
            try:
                new_role = await target_guild.create_role(
                    name=role_data["name"],
                    permissions=discord.Permissions(role_data["permissions"]),
                    color=discord.Color(role_data["color"]),
                    hoist=role_data["hoist"],
                    mentionable=role_data["mentionable"]
                )
                role_map[role_data["name"]] = new_role
            except Exception as e:
                print(f"สร้างยศกู้คืนล้มเหลว {role_data['name']}: {e}")
        for r in data["roles"]:
            role_tasks.append(create_role_task(r))

        category_map = {}
        cat_tasks = []
        categories = [cat for cat in data["categories"] if cat["name"]]
        async def create_cat_task(cat_data):
            try:
                new_cat = await target_guild.create_category(name=cat_data["name"], position=cat_data["position"])
                category_map[cat_data["name"]] = new_cat
            except Exception as e:
                print(f"สร้างหมวดหมู่กู้คืนล้มเหลว {cat_data['name']}: {e}")
        for cat in categories:
            cat_tasks.append(create_cat_task(cat))

        if role_tasks or cat_tasks:
            await update_progress_embed(interaction, "🔄 กำลังย้อนกลับสถานะเซิร์ฟเวอร์...", "กู้คืนยศและหมวดหมู่เดิมทั้งหมดพร้อมกัน", 0, 1, f"กำลังกู้คืนยศ {len(role_tasks)} ยศ และหมวดหมู่ {len(cat_tasks)} หมวดหมู่...")
            await asyncio.gather(*role_tasks, *cat_tasks)

            # อัปเดตสิทธิ์ (Overwrites) ของหมวดหมู่หลังจากได้ยศครบแล้ว
            cat_overwrite_tasks = []
            async def apply_cat_ow(cat_data):
                new_cat = category_map.get(cat_data["name"])
                if new_cat:
                    await apply_channel_overwrites_from_dict(cat_data["overwrites"], new_cat, target_guild, role_map)
            for cat in categories:
                cat_overwrite_tasks.append(apply_cat_ow(cat))
            await asyncio.gather(*cat_overwrite_tasks)

        # 4. กู้คืนห้องแชทและสิทธิ์แบบคู่ขนานสูงสุด (เฟสที่ 2)
        total_channels = sum(len(cat["channels"]) for cat in data["categories"])
        await update_progress_embed(interaction, "🔄 กำลังย้อนกลับสถานะเซิร์ฟเวอร์...", "กู้คืนช่องแชทและช่องคุยเสียงเดิมพร้อมกันในทีเดียว", 0, 1, f"กำลังกู้คืนห้องแชททั้งหมด {total_channels} ช่อง...")

        async def create_channel_task(ch, parent_cat_name, is_text):
            try:
                parent_cat = category_map.get(parent_cat_name) if parent_cat_name else None
                if is_text:
                    new_ch = await target_guild.create_text_channel(
                        name=ch["name"],
                        category=parent_cat,
                        position=ch["position"],
                        topic=ch.get("topic"),
                        nsfw=ch.get("nsfw", False),
                        slowmode_delay=ch.get("slowmode_delay", 0)
                    )
                else:
                    new_ch = await target_guild.create_voice_channel(
                        name=ch["name"],
                        category=parent_cat,
                        position=ch["position"]
                    )
                await apply_channel_overwrites_from_dict(ch["overwrites"], new_ch, target_guild, role_map)
            except Exception as e:
                print(f"สร้างห้องกู้คืนล้มเหลว {ch['name']}: {e}")

        tasks = []
        for cat in data["categories"]:
            for ch in cat["channels"]:
                # หลีกเลี่ยงข้อขัดแย้งในกรณีที่ห้องสั่งงานเดิมชื่อตรงกัน
                if ch["name"] == interaction.channel.name and cat["name"] is None:
                    continue
                tasks.append(create_channel_task(ch, cat["name"], ch["type"] == "text"))
                
        await asyncio.gather(*tasks)

        embed = discord.Embed(
            title="🎉 ดำเนินการย้อนกลับสถานะเซิร์ฟเวอร์สำเร็จ!",
            description="โครงสร้าง ยศ และสิทธิ์การใช้งานได้รับการกู้คืนกลับมาเหมือนเดิมแล้วครับ",
            color=discord.Color.green()
        )
        await interaction.edit_original_response(embed=embed, view=None)

    except Exception as e:
        emb = discord.Embed(
            title="❌ การย้อนกลับล้มเหลว",
            description=f"เกิดปัญหาระหว่างย้อนกลับสถานะ: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=emb, view=None)

# เมนูตัวเลือกรายชื่อเซิร์ฟเวอร์ที่จะคัดลอก
class GuildSelect(discord.ui.Select):
    def __init__(self, bot, member_id, target_guild_id):
        options = []
        for guild in bot.guilds:
            if guild.id == target_guild_id:
                continue
            
            # บอตจะเสนอเฉพาะเซิร์ฟเวอร์ที่ผู้ใช้เป็นผู้ดูแลระบบ (Admin)
            member = guild.get_member(member_id)
            if member and member.guild_permissions.administrator:
                options.append(discord.SelectOption(
                    label=guild.name[:25],
                    value=str(guild.id),
                    description=f"สมาชิก: {guild.member_count} คน | ยศ: {len(guild.roles)} ยศ",
                    emoji="⚙️"
                ))
                
        if not options:
            options.append(discord.SelectOption(
                label="ไม่พบเซิร์ฟเวอร์ที่คุณมีสิทธิ์ผู้ดูแลระบบ",
                value="none",
                description="กรุณาตรวจสอบว่าคุณเป็น Admin ทั้งสองแห่ง",
                disabled=True
            ))
            
        super().__init__(placeholder="เลือกเซิร์ฟเวอร์ต้นทางที่ต้องการคัดลอก...", min_values=1, max_values=1, options=options)

# คลาสวิวตั้งค่าและเลือกตัวเลือกต่างๆ ในคำสั่ง /copy
class CloneConfigView(discord.ui.View):
    def __init__(self, bot, user, target_guild):
        super().__init__(timeout=180)
        self.bot = bot
        self.user = user
        self.target_guild = target_guild
        self.source_guild = None
        
        self.copy_roles = True
        self.copy_channels = True
        self.copy_identity = True
        self.clean_target = False
        
        self.select_menu = GuildSelect(bot, user.id, target_guild.id)
        self.select_menu.callback = self.on_select_guild
        self.add_item(self.select_menu)
        
        self.btn_roles = discord.ui.Button(label="คัดลอกยศ: เปิด", style=discord.ButtonStyle.green, row=1, disabled=True)
        self.btn_roles.callback = self.toggle_roles
        
        self.btn_channels = discord.ui.Button(label="คัดลอกช่องแชท: เปิด", style=discord.ButtonStyle.green, row=1, disabled=True)
        self.btn_channels.callback = self.toggle_channels
        
        self.btn_identity = discord.ui.Button(label="คัดลอกภาพ/โปรไฟล์: เปิด", style=discord.ButtonStyle.green, row=1, disabled=True)
        self.btn_identity.callback = self.toggle_identity
        
        self.btn_confirm = discord.ui.Button(label="เริ่มทำการคัดลอก", style=discord.ButtonStyle.danger, row=3, disabled=True)
        self.btn_confirm.callback = self.on_confirm
        
        self.btn_cancel = discord.ui.Button(label="ยกเลิกการทำงาน", style=discord.ButtonStyle.secondary, row=3)
        self.btn_cancel.callback = self.on_cancel
        
        self.add_item(self.btn_roles)
        self.add_item(self.btn_channels)
        self.add_item(self.btn_identity)
        self.add_item(self.btn_confirm)
        self.add_item(self.btn_cancel)

    async def on_select_guild(self, interaction: discord.Interaction):
        if self.select_menu.values[0] == "none":
            return
        guild_id = int(self.select_menu.values[0])
        self.source_guild = self.bot.get_guild(guild_id)
        
        self.btn_roles.disabled = False
        self.btn_channels.disabled = False
        self.btn_identity.disabled = False
        self.btn_confirm.disabled = False
        
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    async def toggle_roles(self, interaction: discord.Interaction):
        self.copy_roles = not self.copy_roles
        self.btn_roles.label = f"คัดลอกยศ: {'เปิด' if self.copy_roles else 'ปิด'}"
        self.btn_roles.style = discord.ButtonStyle.green if self.copy_roles else discord.ButtonStyle.grey
        await interaction.response.edit_message(embed=self.make_embed(), view=self)
        
    async def toggle_channels(self, interaction: discord.Interaction):
        self.copy_channels = not self.copy_channels
        self.btn_channels.label = f"คัดลอกช่องแชท: {'เปิด' if self.copy_channels else 'ปิด'}"
        self.btn_channels.style = discord.ButtonStyle.green if self.copy_channels else discord.ButtonStyle.grey
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    async def toggle_identity(self, interaction: discord.Interaction):
        self.copy_identity = not self.copy_identity
        self.btn_identity.label = f"คัดลอกภาพ/โปรไฟล์: {'เปิด' if self.copy_identity else 'ปิด'}"
        self.btn_identity.style = discord.ButtonStyle.green if self.copy_identity else discord.ButtonStyle.grey
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    async def on_confirm(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("คุณต้องเป็นผู้ดูแลระบบของเซิร์ฟเวอร์นี้จึงจะใช้งานได้", ephemeral=True)
            return

        # สร้างวิวใหม่สำหรับแสดงปุ่มหยุดคัดลอก (Stop Button)
        progress_view = CloneProgressView(self.target_guild.id)
        await interaction.response.edit_message(content="🔄 กำลังเริ่มกระบวนการจัดเตรียมระบบ...", embed=self.make_embed(), view=progress_view)
        
        # รันการคัดลอกแบบอะซิงโครนัสใน Task แยก เพื่อให้ผู้ใช้สามารถกดปุ่มหยุดได้แบบทันที
        task = asyncio.create_task(run_clone(interaction, self.bot, self.source_guild, self.target_guild, {
            "copy_roles": self.copy_roles,
            "copy_channels": self.copy_channels,
            "copy_identity": self.copy_identity,
            "clean_target": self.clean_target
        }))
        active_clones[self.target_guild.id] = task

    async def on_cancel(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="❌ ยกเลิกการคัดลอกแล้ว", embed=None, view=None)

    def make_embed(self):
        embed = discord.Embed(
            title="⚙️ ตั้งค่าระบบคัดลอกเซิร์ฟเวอร์ (Server Cloner)",
            description="กรุณาตั้งค่าความต้องการของคุณโดยกดปุ่มด้านล่าง จากนั้นกดเริ่มคัดลอก",
            color=discord.Color.blurple()
        )
        if self.source_guild:
            embed.add_field(name="เซิร์ฟเวอร์ต้นทาง (Source)", value=f"**ชื่อ**: {self.source_guild.name}\n**สมาชิก**: {self.source_guild.member_count} คน\n**ยศทั้งหมด**: {len(self.source_guild.roles)} ยศ\n**ช่องแชททั้งหมด**: {len(self.source_guild.channels)} ช่อง", inline=True)
            embed.add_field(name="เซิร์ฟเวอร์ปลายทาง (Target)", value=f"**ชื่อ**: {self.target_guild.name}\n**สมาชิก**: {self.target_guild.member_count} คน", inline=True)
            
            settings_summary = (
                f"• **คัดลอกยศและสิทธิ์การใช้งาน**: {'✅ เปิด' if self.copy_roles else '❌ ปิด'}\n"
                f"• **คัดลอกหมวดหมู่และช่องแชท**: {'✅ เปิด' if self.copy_channels else '❌ ปิด'}\n"
                f"• **คัดลอกเอกลักษณ์ (รูปภาพ/แบนเนอร์)**: {'✅ เปิด' if self.copy_identity else '❌ ปิด'}"
            )
            embed.add_field(name="รายละเอียดการคัดลอกในเซิร์ฟเวอร์นี้", value=settings_summary, inline=False)
        else:
            embed.add_field(name="เซิร์ฟเวอร์ปลายทาง (Target)", value=self.target_guild.name, inline=True)
            embed.add_field(name="สถานะ", value="รอการเลือกเซิร์ฟเวอร์ต้นทางจากเมนูด้านบน...", inline=False)
            
        embed.set_footer(text="ระบบช่วยสำรองข้อมูลและจัดการเซิร์ฟเวอร์ Discord")
        if self.source_guild and self.source_guild.icon:
            embed.set_thumbnail(url=self.source_guild.icon.url)
        return embed

# คลาสวิวสำหรับควบคุม/สั่งหยุดคัดลอกขณะทำงานอยู่
class CloneProgressView(discord.ui.View):
    def __init__(self, target_guild_id):
        super().__init__(timeout=600)
        self.target_guild_id = target_guild_id
        
    @discord.ui.button(label="หยุดทำงาน (Stop)", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ค้นหา Task ที่กำลังรันคัดลอกอยู่ของเซิร์ฟเวอร์นั้น
        task = active_clones.get(self.target_guild_id)
        if task:
            task.cancel() # สั่งยกเลิก/ยกเลิกอะซิงก์รันนิ่งทาสก์
            button.disabled = True
            await interaction.response.edit_message(content="🛑 สั่งยกเลิกงานแล้ว... บอตกำลังหยุดขั้นตอนและทำความสะอาดระบบ", view=self)
        else:
            await interaction.response.send_message("ไม่พบบอตที่กำลังทำงานคัดลอกในเซิร์ฟเวอร์นี้แล้ว หรือการคัดลอกเสร็จสิ้นแล้ว", ephemeral=True)

# วิวยืนยันคำสั่งกู้คืน (/undo)
class UndoConfirmView(discord.ui.View):
    def __init__(self, bot, user, guild):
        super().__init__(timeout=60)
        self.bot = bot
        self.user = user
        self.guild = guild

    @discord.ui.button(label="ยืนยันการกู้คืนข้อมูล", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("คุณต้องเป็นผู้ดูแลระบบในการทำงานนี้", ephemeral=True)
            return
            
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="🔄 กำลังเริ่มกระบวนการกู้คืนสภาพเซิร์ฟเวอร์แบบเดิม...", view=self)
        asyncio.create_task(run_undo(interaction, self.bot, self.guild))

    @discord.ui.button(label="ยกเลิก", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ การกู้คืนข้อมูลถูกยกเลิก", view=None)

# คำสั่งคัดลอกห้องและยศ (/copy)
@bot.tree.command(name="copy", description="คัดลอกห้องแชท ยศ และสิทธิ์การใช้งานจากเซิร์ฟเวอร์ที่คุณเป็น Admin")
async def copy_command(interaction: discord.Interaction):
    # เลื่อนการตอบกลับทันทีเพื่อไม่ให้เกิดข้อผิดพลาดหมดอายุ 3 วินาที (Unknown Interaction)
    await interaction.response.defer(ephemeral=False)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send("❌ คุณต้องเป็นผู้ดูแลระบบ (Administrator) เพื่อใช้คำสั่งนี้", ephemeral=True)
        return

    view = CloneConfigView(bot, interaction.user, interaction.guild)
    await interaction.edit_original_response(embed=view.make_embed(), view=view)

# คำสั่งกู้คืนเซิร์ฟเวอร์ก่อนหน้า (/undo)
@bot.tree.command(name="undo", description="ย้อนกลับเซิร์ฟเวอร์นี้ให้ไปเป็นค่าเริ่มต้นก่อนที่บอตจะคัดลอกข้อมูลล่าสุด")
async def undo_command(interaction: discord.Interaction):
    # เลื่อนการตอบกลับทันทีเพื่อไม่ให้เกิดข้อผิดพลาดหมดอายุ 3 วินาที (Unknown Interaction)
    await interaction.response.defer(ephemeral=False)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send("❌ คุณต้องเป็นผู้ดูแลระบบ (Administrator) เพื่อใช้คำสั่งนี้", ephemeral=True)
        return

    backup_path = f"backups/{interaction.guild_id}_undo.json"
    if not os.path.exists(backup_path):
        await interaction.edit_original_response(content="❌ ไม่พบจุดกู้คืนความปลอดภัยของเซิร์ฟเวอร์นี้ (ไม่เคยคัดลอกมาก่อน)")
        return

    view = UndoConfirmView(bot, interaction.user, interaction.guild)
    await interaction.edit_original_response(
        content="⚠️ **คำเตือน**: ระบบจะทำการลบช่องแชทและยศปัจจุบันทั้งหมด เพื่อนำโครงสร้างเดิมจากไฟล์แบคอัพสำรองขึ้นมาใช้งานใหม่ คุณแน่ใจหรือไม่ที่จะกู้คืนสถานะกลับไป?",
        view=view
    )

# เหตุการณ์ตอนบอตพร้อมทำงาน
@bot.event
async def on_ready():
    print("=========================================")
    print(f"เชื่อมต่อสำเร็จในชื่อบอต: {bot.user.name} ({bot.user.id})")
    print("=========================================")
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands"
    print(f"ลิงก์เชิญบอตเข้าสู่ระบบ:\n{invite_url}")
    print("=========================================")
    try:
        synced = await bot.tree.sync()
        print(f"อัปเดตคำสั่งสแลชบอตจำนวน {len(synced)} คำสั่งเสร็จสมบูรณ์")
    except Exception as e:
        print(f"พบปัญหาการอัปเดตคำสั่ง: {e}")
    print("บอทพร้อมรับการใช้งานเรียบร้อยแล้ว!")

# เริ่มต้นบอต
if __name__ == "__main__":
    if not TOKEN:
        print("ข้อผิดพลาด: ไม่พบค่า DISCORD_TOKEN ในไฟล์ .env")
    else:
        bot.run(TOKEN)

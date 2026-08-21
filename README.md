<div align="center">

# Discord Bot Suite & Automation Management
**ชุดบอทดิสคอร์ดอเนกประสงค์สำหรับบันทึกประวัติกิจกรรม โคลนสำรองเซิร์ฟเวอร์ และระบบจัดการเบื้องหลังบน Windows แบบ 1-Click**

[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)](https://github.com/phwyverysad/Bot-Discord)
[![Language](https://img.shields.io/badge/Language-Python%203.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Library](https://img.shields.io/badge/Library-discord.py%20v2.3%2B-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Automation](https://img.shields.io/badge/Automation-VBScript-grey?style=flat-square)](https://github.com/phwyverysad/Bot-Discord)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/phwyverysad/Bot-Discord?style=flat-square&color=gold)](https://github.com/phwyverysad/Bot-Discord/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/phwyverysad/Bot-Discord?style=flat-square&color=orange)](https://github.com/phwyverysad/Bot-Discord/issues)

[ภาพรวม](#ภาพรวม) | [ฟังก์ชันและโมดูล](#ฟังก์ชันและโมดูล) | [สิ่งที่จำเป็นก่อนใช้งาน](#สิ่งที่จำเป็นก่อนใช้งาน) | [วิธีติดตั้งและเริ่มใช้งาน](#วิธีติดตั้งและเริ่มใช้งาน) | [การตั้งค่า-discord-developer-portal](#การตั้งค่า-discord-developer-portal) | [รายการคำสั่ง](#รายการคำสั่ง) | [ความปลอดภัยและประสิทธิภาพ](#ความปลอดภัยและประสิทธิภาพ) | [สัญญาอนุญาต](#สัญญาอนุญาต)

</div>

---

## ภาพรวม

**Discord Bot Suite** คือชุดรวมโปรแกรมบอท Discord ภาษา Python ที่ถูกปรับแต่งสำหรับการใช้งานบน Windows โดยเฉพาะ มาพร้อมระบบสคริปต์อัตโนมัติ `LaunchBot.vbs` และ `StopBot.vbs` ที่ช่วยให้ทุกคนสามารถเปิด/ปิดบอทในเบื้องหลัง (Background Service) ได้ทันทีด้วยการดับเบิ้ลคลิกเพียงครั้งเดียว โดยไม่ต้องพิมพ์คำสั่ง Command Line หรือเปิดหน้าต่าง Command Prompt ค้างไว้

---

## ฟังก์ชันและโมดูล

โปรเจกต์นี้แบ่งออกเป็น 3 ระบบหลักตามการใช้งาน:

### 1. โมดูล `เช็คสถานะ` (Discord Audit & Activity Logger)
บอทสำหรับบันทึกและตรวจสอบประวัติเหตุการณ์ทั้งหมดที่เกิดขึ้นในเซิร์ฟเวอร์แบบ Real-time พร้อมสร้างหมวดหมู่และห้องแชทแยกประเภทอัตโนมัติ:
* **การเข้า/ออกเซิร์ฟเวอร์**: ตรวจสอบสมาชิกเข้า-ออก พร้อมระบุผู้เชิญและลิงก์คำเชิญ (Invite Tracker)
* **การใช้งานห้องเสียง (Voice Channels)**: บันทึกการเข้า, ออก, ย้ายห้องเสียง และกรณีถูกตัดการเชื่อมต่อ
* **สถานะการควบคุมเสียง**: บันทึกการถูกปิดไมค์ (Server Mute) หรือปิดหูฟัง (Server Deafen) จากแอดมิน
* **การลงโทษและจัดการสมาชิก**: ประวัติการเตะ (Kick), การแบน (Ban) และการจำกัดเวลา (Timeout)
* **การแก้ไข/ลบข้อความ**: บันทึกข้อความเดิมก่อนถูกแก้ไขหรือถูกลบ
* **การเปลี่ยนแปลงข้อมูลผู้ใช้**: ประวัติการเปลี่ยนรูปโปรไฟล์ (Avatar) และการเปลี่ยนชื่อเล่น (Nickname)
* **การจัดการยศ (Role Audit)**: ประวัติการเพิ่ม/ลบยศให้สมาชิก และการปรับแก้สิทธิ์ของยศ

### 2. โมดูล `copy discord` (Discord Server Cloner & Backup)
บอทสำหรับสำรองข้อมูลและโคลนโครงสร้างดิสคอร์ดเซิร์ฟเวอร์แบบ Full Fidelity:
* **สำรองโครงสร้างเซิร์ฟเวอร์**: บันทึกยศ สิทธิ์การใช้งาน หมวดหมู่ ห้องข้อความ ห้องเสียง รูปโปรไฟล์ และแบนเนอร์เซิร์ฟเวอร์ลงไฟล์ JSON
* **โคลนและกู้คืน (Restore/Clone)**: สร้างห้องและยศตามโครงสร้างเดิม พร้อมคัดลอกสิทธิ์ Permission Overwrites อย่างแม่นยำ
* **ระบบความปลอดภัย Undo Point**: บันทึกจุดกู้คืนความปลอดภัยอัตโนมัติก่อนเริ่มกระบวนการโคลน

### 3. โมดูล `บอทไว้ยืงดิส` (Discord Fast Server Reset)
บอทสำหรับการล้างข้อมูลและรีเซ็ตเซิร์ฟเวอร์ความเร็วสูงด้วยสถาปัตยกรรม Asynchronous ขนาน (Parallel Processing) สำหรับผู้ดูแลระบบที่ต้องการเคลียร์พื้นที่ทดสอบอย่างรวดเร็ว

---

## สิ่งที่จำเป็นก่อนใช้งาน

* ระบบปฏิบัติการ **Windows 10** หรือ **Windows 11** (64-bit)
* ติดตั้ง **Python 3.10 ขึ้นไป** 

> [!IMPORTANT]
> **สำคัญมากสำหรับการติดตั้ง Python**:
> 1. ดาวน์โหลด Python ตัวติดตั้งจาก [python.org](https://www.python.org/downloads/)
> 2. ในหน้าแรกของโปรแกรมติดตั้ง **ต้องทำเครื่องหมายถูกที่ช่อง "Add python.exe to PATH"** ด้านล่างสุดก่อนกด Install Now
> 3. หากไม่ได้เลือกช่องดังกล่าว สคริปต์อัตโนมัติจะไม่สามารถตรวจหา Python ในระบบได้

---

## วิธีติดตั้งและเริ่มใช้งาน

### 1. โคลนคลังข้อมูล (Clone Repository)
```cmd
git clone https://github.com/phwyverysad/Bot-Discord.git
cd Bot-Discord
```

### 2. ตั้งค่าโทเค็นบอท (Bot Token Configuration)
คัดลอกไฟล์ `.env.example` เป็นชื่อไฟล์ `.env` ในโฟลเดอร์บอทที่ต้องการใช้งาน หรือในโฟลเดอร์หลัก:

```cmd
copy .env.example .env
```

จากนั้นเปิดไฟล์ `.env` ด้วย Notepad แล้วใส่ Token ของคุณ:
```env
DISCORD_TOKEN=your_bot_token_here
```

### 3. การเปิดใช้งานบอทแบบ 1-Click (`LaunchBot.vbs`)
* **ดับเบิ้ลคลิกไฟล์ `LaunchBot.vbs`** ที่โฟลเดอร์หลัก หรือในโฟลเดอร์ย่อยของบอทแต่ละตัว
* สคริปต์จะทำการตรวจสอบ Python, สร้าง Virtual Environment (`.venv`) และติดตั้ง Library ที่จำเป็นจาก `requirements.txt` ให้อัตโนมัติ
* บอทจะเริ่มทำงานในเบื้องหลังทันทีโดยไม่มีหน้าต่าง CMD สีดำกวนใจ
* มีการแจ้งเตือน **Windows Toast Notification** แสดงสถานะเมื่อบอทเริ่มทำงานสำเร็จ

### 4. การปิดบอท (`StopBot.vbs`)
* **ดับเบิ้ลคลิกไฟล์ `StopBot.vbs`** เพื่อปิดการทำงานของบอทในระบบอย่างปลอดภัยและสมบูรณ์

---

## การตั้งค่า Discord Developer Portal

เพื่อให้บอทสามารถอ่านข้อมูลสมาชิก ประวัติข้อความ และสถานะต่างๆ ได้อย่างครบถ้วน จำเป็นต้องเปิดใช้งานสิทธิ์ **Privileged Gateway Intents**:

1. ไปที่ [Discord Developer Portal](https://discord.com/developers/applications)
2. เลือก Application บอทของคุณ แล้วไปที่เมนู **Bot** ในแถบซ้ายมือ
3. เลื่อนลงมาที่หัวข้อ **Privileged Gateway Intents** และเปิดใช้งานทั้ง 3 ข้อ:
   - ✅ **Presence Intent**
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent**
4. บันทึกการเปลี่ยนแปลง (Save Changes)
5. ไปที่เมนู **OAuth2 -> URL Generator** เลือก Scope `bot` และ `applications.commands` พร้อมให้สิทธิ์ `Administrator` เพื่อรับลิงก์เชิญบอทเข้าสู่เซิร์ฟเวอร์ของคุณ

---

## รายการคำสั่ง

### โมดูล `เช็คสถานะ` (Slash Commands)

| คำสั่ง | คำอธิบาย |
| :--- | :--- |
| `/setup` | สร้างหมวดหมู่ `ประวัติ` และห้องบันทึก Log กิจกรรมทั้งหมดอัตโนมัติ |
| `/set_channel [key] [channel]` | กำหนดห้องรับ Log เฉพาะประเภทตามต้องการ |
| `/stats` | แสดงสถิติและข้อมูลภาพรวมของเซิร์ฟเวอร์ |
| `/backup` | สำรองข้อมูลโครงสร้างการตั้งค่าของเซิร์ฟเวอร์ |
| `/purge [amount]` | ลบข้อความในห้องแชทตามจำนวนที่ระบุ |
| `/mute_history [member]` | ดูประวัติการปิดไมค์/หูฟังของสมาชิก |
| `/userinfo [member]` | ตรวจสอบข้อมูล บัญชี วันที่เข้าร่วม และยศของผู้ใช้ |

---

## ความปลอดภัยและประสิทธิภาพ

* **ทำงานแบบ Background Service**: ควบคุมผ่าน VBScript และ WMI Process Management ทำงานเงียบ ไร้หน้าต่างรบกวน
* **ระบบจัดการความลับ**: โทเค็นทั้งหมดถูกแยกเก็บในไฟล์ `.env` และได้รับการป้องกันด้วย `.gitignore` อย่างรัดกุม
* **ประหยัดทรัพยากร**: ใช้ Asynchronous I/O (`asyncio` + `aiohttp`) กินหน่วยความจำน้อยและตอบสนองต่อเหตุการณ์ได้ทันที

---

## สัญญาอนุญาต

โปรเจกต์นี้เผยแพร่ภายใต้สัญญาอนุญาต MIT License

```
MIT License - Copyright (c) 2026 phwyverysad
```

<div align="center">

# Discord Bot Suite

**ชุดบอท Discord อเนกประสงค์ พร้อมระบบรันเบื้องหลังแบบ 1-Click บน Windows**

[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)](https://github.com/phwyverysad/Bot-Discord)
[![Language](https://img.shields.io/badge/Language-Python%203.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Library](https://img.shields.io/badge/Library-discord.py-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/phwyverysad/Bot-Discord?style=flat-square&color=gold)](https://github.com/phwyverysad/Bot-Discord/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/phwyverysad/Bot-Discord?style=flat-square&color=orange)](https://github.com/phwyverysad/Bot-Discord/issues)

[ภาพรวม](#ภาพรวม) | [ฟีเจอร์หลัก](#ฟีเจอร์หลัก) | [สิ่งที่ต้องมีก่อนเริ่ม](#สิ่งที่ต้องมีก่อนเริ่ม) | [การติดตั้งและใช้งาน](#การติดตั้งและใช้งาน) | [การตั้งค่าบอท](#การตั้งค่าบอท) | [สัญญาอนุญาต](#สัญญาอนุญาต)

</div>

---

## ภาพรวม

**Discord Bot Suite** คือชุดโปรแกรมบอท Discord สำหรับ Windows ที่ออกแบบมาให้ใช้งานง่ายที่สุด เพียงดับเบิ้ลคลิก `LaunchBot.vbs` ระบบจะจัดการติดตั้ง Library และรันบอทในเบื้องหลัง (Background Service) ให้อัตโนมัติทันที

---

## ฟีเจอร์หลัก

* **เช็คสถานะ (`bothistory.py`)**: บันทึก Log ทุกเหตุการณ์ในเซิร์ฟเวอร์แบบ Real-time (เข้า-ออก, ห้องเสียง, ย้ายห้อง, ปิดไมค์/หูฟัง, แบน, เตะ, แก้ไข/ลบข้อความ, ประวัติโปรไฟล์/ยศ)
* **copy discord (`bot.py`)**: สำรองและโคลนโครงสร้างเซิร์ฟเวอร์ (ยศ, หมวดหมู่, ห้อง, สิทธิ์การเข้าถึง, ไอคอน, แบนเนอร์)
* **บอทไว้ยืงดิส (`bot.py`)**: ระบบรีเซ็ตและล้างข้อมูลเซิร์ฟเวอร์ความเร็วสูง (Parallel Asynchronous)

---

## สิ่งที่ต้องมีก่อนเริ่ม

1. ระบบปฏิบัติการ **Windows 10 / 11**
2. **Python 3.10 ขึ้นไป** ([ดาวน์โหลดที่นี่](https://www.python.org/downloads/))

> [!IMPORTANT]
> **สำคัญมาก**: ตอนติดตั้ง Python **ต้องทำเครื่องหมายถูกที่ `Add python.exe to PATH`** ด้านล่างสุดก่อนกดติดตั้ง

---

## การติดตั้งและใช้งาน

### 1. โคลนโปรเจกต์
```cmd
git clone https://github.com/phwyverysad/Bot-Discord.git
cd Bot-Discord
```

### 2. ใส่โทเค็นบอท
คัดลอกไฟล์ `.env.example` แล้วเปลี่ยนชื่อเป็น `.env` จากนั้นเปิดไฟล์แล้วใส่ Token ของคุณ:
```env
DISCORD_TOKEN=your_bot_token_here
```

### 3. เปิด/ปิดบอท (1-Click)
* **เปิดบอท**: ดับเบิ้ลคลิก `LaunchBot.vbs` (ระบบจะสร้าง `.venv` และติดตั้ง Library ให้เองอัตโนมัติ)
* **ปิดบอท**: ดับเบิ้ลคลิก `StopBot.vbs` เพื่อหยุดการทำงานของบอท

---

## การตั้งค่าบอท

ก่อนใช้งาน ให้ไปที่ [Discord Developer Portal](https://discord.com/developers/applications) และเปิดสิทธิ์ **Privileged Gateway Intents**:
* ✅ **Presence Intent**
* ✅ **Server Members Intent**
* ✅ **Message Content Intent**

---

## สัญญาอนุญาต

โปรเจกต์นี้เผยแพร่ภายใต้สัญญาอนุญาต MIT License

```
MIT License - Copyright (c) 2026 phwyverysad
```

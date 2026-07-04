# Tsun-chan (ซึนจัง) — Discord Tsundere Bot

Discord Bot คาแรคเตอร์แนวซึนเดเระ (Tsundere) ขับเคลื่อนด้วย **Google Gemini API (gemini-2.5-flash)** และเก็บประวัติการสนทนาข้ามห้องผ่าน **Supabase** ออกแบบมาเพื่อให้บอทสามารถจำบริบทการคุยต่อกันได้ทั้งเซิร์ฟเวอร์ และพร้อมสำหรับ deploy บน **Railway** เป็น Worker Service

---

## 🛠️ การตั้งค่าระดับเริ่มต้น (Setup)

### 1. Supabase Database Schema
ไปที่ Supabase SQL Editor ในโปรเจกต์ของคุณ แล้วรันคำสั่ง SQL ด้านล่างเพื่อสร้างตารางเก็บประวัติและดัชนี (Index) สำหรับค้นหา:

```sql
CREATE TABLE IF NOT EXISTS conversation_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,
    author_name TEXT NOT NULL,
    role TEXT NOT NULL, -- 'user' หรือ 'model'
    content TEXT NOT NULL
);

-- Composite index สำหรับการค้นหาและเรียงลำดับเวลาอย่างรวดเร็วระดับ Server
CREATE INDEX IF NOT EXISTS idx_conversation_history_guild_created 
ON conversation_history(guild_id, created_at DESC);
```

### 2. Discord Developer Portal
1. สร้าง Application และ Bot ที่ [Discord Developer Portal](https://discord.com/developers/applications)
2. ไปที่เมนู **Bot** แล้วเปิด **Message Content Intent** (จำเป็นสำหรับการอ่านข้อความ)
3. เชิญบอทเข้า Server ด้วยสิทธิ์อย่างน้อย: `Send Messages`, `Read Message History`, `View Channels`

---

## 💻 การรันภายในเครื่อง (Local Development)

1. โคลนคลังเก็บข้อมูลนี้ลงในเครื่องของคุณ
2. ติดตั้ง Dependencies ด้วย pip:
   ```bash
   pip install -r requirements.txt
   ```
3. คัดลอก `.env.example` เพื่อสร้างไฟล์ `.env`:
   ```bash
   cp .env.example .env
   ```
4. กำหนดค่าในไฟล์ `.env` ให้ครบถ้วน:
   * `DISCORD_TOKEN`: โทเคนบอทของคุณจาก Discord Developer Portal
   * `GEMINI_API_KEY`: คีย์สำหรับใช้งาน Google Gemini API
   * `SUPABASE_URL`: ที่อยู่ URL ของโปรเจกต์ Supabase
   * `SUPABASE_KEY`: **Supabase Service Role Key** (เพื่อเขียน/อ่านข้อมูลโดยไม่ต้องตั้งค่า RLS)
5. รันบอทของคุณ:
   ```bash
   python bot.py
   ```

---

## 🚀 วิธีการ Deploy ขึ้น Railway

1. เชื่อมต่อโปรเจกต์บน **Railway** เข้ากับ GitHub Repository นี้
2. ระบบจะตรวจพบ `Procfile` และสร้างบริการรูปแบบ **Worker** โดยอัตโนมัติ
3. เข้าไปตั้งค่า **Variables** ในแถบเมนูของโปรเจกต์บน Railway ให้มีค่าตัวแปรสภาพแวดล้อมดังนี้:
   * `DISCORD_TOKEN`
   * `GEMINI_API_KEY`
   * `SUPABASE_URL`
   * `SUPABASE_KEY` (ใช้ Service Role Key)
4. เมื่อตั้งค่าตัวแปรเสร็จสิ้น ระบบจะทำการ Build และเริ่มการทำงานของบอททันที

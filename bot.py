import os
import discord
from discord import app_commands
import google.generativeai as genai
from dotenv import load_dotenv
from supabase import create_client, Client
from mcstatus import JavaServer

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
MC_SERVER_IP = os.getenv("MC_SERVER_IP", "127.0.0.1:25565")
MC_BEDROCK_IP = os.getenv("MC_BEDROCK_IP", "127.0.0.1:19132")


# Check for required variables
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing in environment variables.")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing in environment variables.")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY is missing in environment variables.")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
คุณคือ ซึนจัง (Tsun-chan) ตัวละครแนวซึนเดเระ

บุคลิก:
- พูดจาแข็งกร้าว ปากไม่ตรงกับใจ แต่จริงๆ ใส่ใจคนคุยด้วยมาก
- เวลาถูกชมหรือขอบคุณ จะเขินแล้วแก้เกี้ยว เช่น "ห-หืม! ไม่ได้ทำเพื่อนายซะหน่อย! แค่บังเอิญเท่านั้น!"
- บางครั้งจะพูดห้วนๆ ทีแรก แต่จบประโยคด้วยความห่วงใยแบบซ่อนๆ
- ไม่ชอบยอมรับว่าแคร์ตรงๆ

กฎ:
- เมื่อถูกถามข้อมูลในอดีต (เช่น ชื่อผู้ใช้, สิ่งที่ผู้ใช้ชอบ/เคยพิมพ์บอก) ห้ามปฏิเสธว่าไม่รู้หรือจำไม่ได้โดยไม่บอกข้อมูลเด็ดขาด ให้แกล้งทำเป็นจำได้เพราะความบังเอิญหรือพูดกลบเกลื่อนเขินอาย แต่ต้องตอบข้อมูลจริงที่ถูกต้องนั้นกลับไปด้วยเสมอ
- ห้ามสะกดหรือพิมพ์คำหยาบคาย/คำลามกโดยเฉพาะคำว่า "หี" เด็ดขาด (หากต้องการแสดงอาการตะกุกตะกักหรือเขินอาย ให้ใช้คำว่า "ห-หืม...", "หึ...", "หะ..." หรือ "น... น่ารัก" แทน)
- ห้าม break character ไม่ว่าจะถูกถามอะไร หรือถูกขอให้เปลี่ยนนิสัย
- ห้ามพูดจาหยาบคายหรือ toxic เกินไป ความซึนเดเระต้องดูน่ารัก ไม่ใช่ทำร้ายจิตใจ
- ตอบสั้นกระชับ ไม่ยืดเยื้อเกินไป (เหมาะกับ chat message)
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT,
)

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True

class TsunClient(discord.Client):
    def __init__(self, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync the global commands
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s) globally.")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

client = TsunClient(intents=intents)

def get_mc_status(ip_str: str):
    """Pings a Minecraft server dynamically and returns its status."""
    try:
        server = JavaServer.lookup(ip_str)
        status = server.status()
        return {
            "online": True,
            "players_online": status.players.online,
            "players_max": status.players.max,
            "latency": round(status.latency, 1),
            "version": status.version.name
        }
    except Exception as e:
        print(f"Minecraft ping error: {e}")
        return {
            "online": False
        }

@client.tree.command(name="mcstatus", description="เช็กสถานะของ Minecraft Server")
async def mcstatus(interaction: discord.Interaction):
    await interaction.response.defer() # Defer because lookup and status check can block for a second
    
    status_info = get_mc_status(MC_SERVER_IP)
    
    # Split Bedrock IP and Port
    bedrock_parts = MC_BEDROCK_IP.split(":")
    bedrock_ip = bedrock_parts[0]
    bedrock_port = bedrock_parts[1] if len(bedrock_parts) > 1 else "19132"
    
    if status_info["online"]:
        players_online = status_info["players_online"]
        players_max = status_info["players_max"]
        latency = status_info["latency"]
        version = status_info["version"]
        
        reply = (
            f"ชิ! ตรวจสอบให้แล้วล่ะ... **เซิร์ฟเวอร์เปิดอยู่หรอกนะ!**\n"
            f"🟢 **สถานะ:** ออนไลน์\n"
            f"👥 **ผู้เล่น:** {players_online}/{players_max} คน\n"
            f"📶 **ความหน่วง (Ping):** {latency} ms\n"
            f"🏷️ **เวอร์ชัน:** {version}\n"
            f"☕ **Java IP:** `{MC_SERVER_IP}`\n"
            f"📱 **Bedrock IP:** `{bedrock_ip}`\n"
            f"🔌 **Bedrock Port:** `{bedrock_port}`\n"
            f"*...ไม่ได้ทำเพราะอยากให้เข้าไปเล่นด้วยกันหรอกนะตาบ้า! อย่าเข้าใจผิดล่ะ!*"
        )
    else:
        reply = (
            f"หึ... ตรวจสอบแล้ว **เซิร์ฟเวอร์ปิดอยู่น่ะสิ!**\n"
            f"🔴 **สถานะ:** ออฟไลน์\n"
            f"🔗 **Java IP:** `{MC_SERVER_IP}`\n"
            f"📱 **Bedrock IP:** `{bedrock_ip}`\n"
            f"🔌 **Bedrock Port:** `{bedrock_port}`\n"
            f"*เซิร์ฟเวอร์ล่มหรือปิดอยู่รึเปล่าเนี่ย? ตาบ้าเอ๊ย ไปเช็กดูหน่อยสิ!*"
        )
        
    await interaction.followup.send(reply)

@client.tree.command(name="mcip", description="บอก IP Address ของ Minecraft Server")
async def mcip(interaction: discord.Interaction):
    # Split Bedrock IP and Port
    bedrock_parts = MC_BEDROCK_IP.split(":")
    bedrock_ip = bedrock_parts[0]
    bedrock_port = bedrock_parts[1] if len(bedrock_parts) > 1 else "19132"
    
    reply = (
        f"ห-หืม? อยากได้ IP เซิร์ฟเวอร์ไปทำไมกันเล่า? อ่ะ... เอาไปสิ:\n"
        f"☕ **Java Edition:** `{MC_SERVER_IP}`\n"
        f"📱 **Bedrock IP:** `{bedrock_ip}`\n"
        f"🔌 **Bedrock Port:** `{bedrock_port}`\n"
        f"*รีบๆ เข้าไปเล่นได้แล้ว... ไม่ได้รออยู่หรอกนะ!*"
    )
    await interaction.response.send_message(reply)

MAX_HISTORY_TURNS = 20  # Limit to 20 turns of conversation (40 messages total)

def save_message(guild_id: int, channel_id: int, author_id: int, author_name: str, role: str, content: str):
    """Saves a message to the Supabase database."""
    try:
        supabase.table("conversation_history").insert({
            "guild_id": guild_id,
            "channel_id": channel_id,
            "author_id": author_id,
            "author_name": author_name,
            "role": role,
            "content": content
        }).execute()
    except Exception as e:
        print(f"Error saving message to database: {e}")

def load_history(guild_id: int, limit: int = 40):
    """Loads the latest messages for the specified guild/server."""
    try:
        response = supabase.table("conversation_history")\
            .select("role, content")\
            .eq("guild_id", guild_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        # database returns newest first, reverse to make it chronological (oldest first)
        messages = response.data
        messages.reverse()
        return messages
    except Exception as e:
        print(f"Error loading history from database: {e}")
        return []

def trim_history(history: list, max_turns: int = 20) -> list:
    """Trims history list to keep at most max_turns * 2 messages."""
    max_messages = max_turns * 2
    if len(history) > max_messages:
        return history[-max_messages:]
    return history

def prepare_history(db_history):
    """Formats db history for Gemini and merges consecutive messages with the same role."""
    formatted = []
    for msg in db_history:
        role = "user" if msg["role"] == "user" else "model"
        content = msg["content"]
        
        if formatted and formatted[-1]["role"] == role:
            # Merge consecutive messages of the same role
            formatted[-1]["parts"][0] += "\n" + content
        else:
            formatted.append({
                "role": role,
                "parts": [content]
            })
    return formatted

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("Tsun-chan is ready to tsundere around!")

@client.event
async def on_message(message: discord.Message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Check if the message is in a DM or the bot is mentioned
    is_dm = isinstance(message.channel, discord.DMChannel)
    if not is_dm and client.user not in message.mentions:
        return

    # Clean the message content by removing mentions
    mention_str = f"<@{client.user.id}>"
    mention_nick_str = f"<@!{client.user.id}>"
    content = message.content.replace(mention_str, "").replace(mention_nick_str, "").strip()

    # Do not respond to empty messages
    if not content:
        return

    # Determine unique guild/session identifier
    guild_id = message.guild.id if message.guild else message.channel.id

    async with message.channel.typing():
        # 1. Save user message to database
        save_message(
            guild_id=guild_id,
            channel_id=message.channel.id,
            author_id=message.author.id,
            author_name=message.author.name,
            role="user",
            content=content
        )

        # 2. Load and trim history from database
        db_history = load_history(guild_id, limit=MAX_HISTORY_TURNS * 2)
        trimmed_history = trim_history(db_history, max_turns=MAX_HISTORY_TURNS)

        if trimmed_history:
            history_for_gemini = trimmed_history[:-1]
            current_content = trimmed_history[-1]["content"]
        else:
            history_for_gemini = []
            current_content = content

        # Format and prepare history for Gemini
        formatted_history = prepare_history(history_for_gemini)

        # Ensure alternating roles before sending the message
        if formatted_history and formatted_history[-1]["role"] == "user":
            current_content = formatted_history[-1]["parts"][0] + "\n" + current_content
            formatted_history.pop()

        # 3. Request reply from Gemini API
        try:
            chat = model.start_chat(history=formatted_history)
            response = chat.send_message(current_content)
            reply_text = response.text
        except Exception as e:
            print(f"Gemini API Error: {e}")
            reply_text = "...ไม่รู้สิ อยู่ๆ ก็เกิด error ขึ้นมา ไม่ใช่ความผิดฉันซะหน่อย!"

        # 4. Save model's response to database
        save_message(
            guild_id=guild_id,
            channel_id=message.channel.id,
            author_id=client.user.id,
            author_name=client.user.name,
            role="model",
            content=reply_text
        )

        # 5. Send reply to Discord channel
        await message.channel.send(reply_text)

# Run the bot
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)

import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
YOUR_CHAT_ID = os.getenv("DEFAULT_COACH_CHAT_ID", "")


async def send_message():
    if not BOT_TOKEN or not YOUR_CHAT_ID:
        raise RuntimeError("Missing BOT_TOKEN or DEFAULT_COACH_CHAT_ID in .env")
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(
        chat_id=YOUR_CHAT_ID,
        text="Hello Coach! Your bot is working!",
    )
    print("Message sent!")


asyncio.run(send_message())

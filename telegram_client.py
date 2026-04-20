import os
import asyncio
from telethon import TelegramClient, events
from config import api_id, api_hash, bot_username

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, "session")
os.makedirs(SESSION_DIR, exist_ok=True)

SESSION_PATH = os.path.join(SESSION_DIR, "april_session")

client = TelegramClient(SESSION_PATH, api_id, api_hash)

async def start_client():
    await client.start()

async def send_and_receive(message):
    entity = await client.get_entity(bot_username)

    # Create future to wait for reply
    future = asyncio.get_event_loop().create_future()

    @client.on(events.NewMessage(from_users=entity))
    async def handler(event):
        if not future.done():
            future.set_result(event.message.text)

    # Send message
    await client.send_message(entity, message)

    try:
        # Wait for reply (max 10 seconds)
        reply = await asyncio.wait_for(future, timeout=10)
    except asyncio.TimeoutError:
        reply = "⚠️ No response from bot"
    finally:
        client.remove_event_handler(handler)

    return reply
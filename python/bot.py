import sys
import asyncio
from telethon import TelegramClient

api_id = 39894476
api_hash = "100a3ea5cf8fbfa6a60d7134d6cac39a"
bot_username = "april848_bot"

client = TelegramClient("session", api_id, api_hash)


async def main():
    await client.start()

    while True:
        user_input = sys.stdin.readline().strip()
        if not user_input:
            continue

        entity = await client.get_entity(bot_username)

        # Get last message ID before sending
        before = await client.get_messages(entity, limit=1)
        send_id = before[0].id if before else 0

        # Send our message
        await client.send_message(entity, user_input)

        # Wait for response
        await asyncio.sleep(2)

        # Get messages and find bot's reply (skip our own message)
        async for msg in client.iter_messages(entity, limit=10):
            if msg.id > send_id:
                print(msg.text, flush=True)
                break


asyncio.run(main())

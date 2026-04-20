"""
April — Your Personal 24/7 AI Assistant
python-telegram-bot + Groq + SQLite + Starlette
"""

import logging
import sys
import time

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from groq import Groq
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
import uvicorn

from config import (
    TELEGRAM_TOKEN,
    GROQ_API_KEY,
    OWNER_CHAT_ID,
    WEBHOOK_URL,
    PORT,
    MODEL,
    MAX_HISTORY,
    MAX_TOKENS,
    validate_config,
)
from memory import ConversationMemory
from personal_info import SYSTEM_PROMPT

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("April")

# ─── Clients ─────────────────────────────────────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY)
memory = ConversationMemory()

# ─── Shared state ─────────────────────────────────────────────────────────────
last_reply = {"text": "", "timestamp": 0}


# ─── Core AI function (shared by Telegram + Desktop) ─────────────────────────
async def get_april_reply(chat_id: int, user_message: str) -> str:
    global last_reply

    memory.add_message(chat_id, "user", user_message)
    history = memory.get_history(chat_id, limit=MAX_HISTORY)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=0.75,
    )
    reply = response.choices[0].message.content.strip()
    memory.add_message(chat_id, "assistant", reply)

    last_reply["text"] = reply
    last_reply["timestamp"] = int(time.time() * 1000)

    return reply


# ─── Helpers ──────────────────────────────────────────────────────────────────
def is_owner(update: Update) -> bool:
    return update.effective_chat.id == OWNER_CHAT_ID


async def send_long_message(update: Update, text: str):
    limit = 4096
    if len(text) <= limit:
        await update.message.reply_text(text)
        return
    for chunk in [text[i:i+limit] for i in range(0, len(text), limit)]:
        await update.message.reply_text(chunk)


# ─── Telegram Command Handlers ────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("🔒 Private assistant. Access denied.")
        return
    await update.message.reply_text(
        "🌸 *Hey! I'm April* — your personal AI assistant.\n\n"
        "I'm here 24/7, I know who you are, and I remember our conversations.\n\n"
        "Just type anything — I'll respond ✨",
        parse_mode="Markdown",
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    await update.message.reply_text(
        "🌸 *April — Help*\n\n"
        "• /start — Wake me up\n"
        "• /clear — Clear memory\n"
        "• /memory — Memory stats\n"
        "• /about — About April",
        parse_mode="Markdown",
    )

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    count = memory.get_message_count(update.effective_chat.id)
    memory.clear_history(update.effective_chat.id)
    await update.message.reply_text(f"🧹 Cleared {count} messages. Fresh start! 🌱")

async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    stats = memory.get_stats(update.effective_chat.id)
    await update.message.reply_text(
        f"🧠 *Memory Stats*\n\n"
        f"• Total: {stats['total']}\n"
        f"• Your messages: {stats['user_count']}\n"
        f"• My replies: {stats['assistant_count']}\n"
        f"• Oldest: {stats['oldest'] or 'none'}\n"
        f"• Latest: {stats['latest'] or 'none'}",
        parse_mode="Markdown",
    )

async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    await update.message.reply_text(
        "🌸 *About April*\n\n"
        "Brain: Llama 3.3 70B via Groq\n"
        "Memory: SQLite\n"
        "Hosting: Railway\n"
        "Interface: Telegram + Desktop HUD 💫",
        parse_mode="Markdown",
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("🔒 Private assistant. Access denied.")
        return

    user_message = update.message.text.strip()
    if not user_message: return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply = await get_april_reply(update.effective_chat.id, user_message)
        await send_long_message(update, reply)
    except Exception as e:
        logger.error(f"Groq error: {e}")
        await update.message.reply_text("😅 Hit a snag. Try again!")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}", exc_info=context.error)


# ─── HTTP Routes ──────────────────────────────────────────────────────────────
ptb_app: Application = None

async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return PlainTextResponse("OK")

async def desktop_chat(request: Request):
    """
    Electron calls POST /chat {"message": "..."}
    April replies directly — no Telegram token confusion.
    Also syncs the reply to your Telegram phone.
    """
    try:
        data = await request.json()
        user_message = data.get("message", "").strip()
        if not user_message:
            return JSONResponse({"error": "empty message"}, status_code=400)

        reply = await get_april_reply(OWNER_CHAT_ID, user_message)

        # Sync to Telegram phone so history stays in one place
        try:
            await ptb_app.bot.send_message(chat_id=OWNER_CHAT_ID, text=reply)
        except Exception:
            pass

        return JSONResponse(
            {"reply": reply},
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Desktop chat error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def get_last_reply(request: Request):
    since = int(request.query_params.get("since", 0))
    if last_reply["timestamp"] > since:
        return JSONResponse(last_reply, headers={"Access-Control-Allow-Origin": "*"})
    return JSONResponse({"text": "", "timestamp": 0}, headers={"Access-Control-Allow-Origin": "*"})

async def health_check(request: Request):
    return PlainTextResponse("April is alive 🌸")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    global ptb_app

    validate_config()
    logger.info("🌸 Starting April...")

    ptb_app = Application.builder().token(TELEGRAM_TOKEN).build()
    ptb_app.add_handler(CommandHandler("start",  cmd_start))
    ptb_app.add_handler(CommandHandler("help",   cmd_help))
    ptb_app.add_handler(CommandHandler("clear",  cmd_clear))
    ptb_app.add_handler(CommandHandler("memory", cmd_memory))
    ptb_app.add_handler(CommandHandler("about",  cmd_about))
    ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    ptb_app.add_error_handler(error_handler)

    if WEBHOOK_URL:
        logger.info(f"☁️  Webhook mode | Port: {PORT} | URL: {WEBHOOK_URL}")

        starlette_app = Starlette(routes=[
            Route(f"/{TELEGRAM_TOKEN}", telegram_webhook, methods=["POST"]),
            Route("/chat",       desktop_chat,   methods=["POST"]),
            Route("/last-reply", get_last_reply, methods=["GET"]),
            Route("/health",     health_check,   methods=["GET"]),
        ])

        async def on_startup():
            await ptb_app.initialize()
            await ptb_app.bot.set_webhook(
                url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}",
                drop_pending_updates=True,
            )
            await ptb_app.bot.set_my_commands([
                BotCommand("start",  "Wake April up"),
                BotCommand("help",   "Show commands"),
                BotCommand("clear",  "Clear memory"),
                BotCommand("memory", "Memory stats"),
                BotCommand("about",  "About April"),
            ])
            await ptb_app.start()
            logger.info(f"✅ April is live! Owner: {OWNER_CHAT_ID}")

        async def on_shutdown():
            await ptb_app.stop()

        starlette_app.add_event_handler("startup",  on_startup)
        starlette_app.add_event_handler("shutdown", on_shutdown)

        uvicorn.run(starlette_app, host="0.0.0.0", port=PORT)

    else:
        logger.info("💻 Polling mode (local)")
        async def post_init(app):
            await app.bot.set_my_commands([
                BotCommand("start",  "Wake April up"),
                BotCommand("help",   "Show commands"),
                BotCommand("clear",  "Clear memory"),
                BotCommand("memory", "Memory stats"),
                BotCommand("about",  "About April"),
            ])
            logger.info(f"✅ April is live! Owner: {OWNER_CHAT_ID}")
        ptb_app.post_init = post_init
        ptb_app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

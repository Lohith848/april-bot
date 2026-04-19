"""
April — Your Personal 24/7 AI Assistant (Telegram Bot)
Built with: python-telegram-bot + Groq (Llama 3.3 70B) + SQLite + Starlette
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

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("April")

# ─── Clients ────────────────────────────────────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY)
memory = ConversationMemory()

# ─── Last reply store (for Electron desktop polling) ────────────────────────
last_reply = {"text": "", "timestamp": 0}


# ─── Helpers ─────────────────────────────────────────────────────────────────
def is_owner(update: Update) -> bool:
    return update.effective_chat.id == OWNER_CHAT_ID


async def send_long_message(update: Update, text: str):
    limit = 4096
    if len(text) <= limit:
        await update.message.reply_text(text)
        return
    chunks = [text[i : i + limit] for i in range(0, len(text), limit)]
    for chunk in chunks:
        await update.message.reply_text(chunk)


# ─── Command Handlers ────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("🔒 I'm a private assistant. Access denied.")
        return
    await update.message.reply_text(
        "🌸 *Hey! I'm April* — your personal AI assistant.\n\n"
        "I'm here for you 24/7, I know who you are, and I remember our conversations.\n\n"
        "*Commands:*\n"
        "💬 Just type anything — I'll respond\n"
        "/clear — Wipe my memory (fresh start)\n"
        "/memory — See how much I remember\n"
        "/about — About me\n"
        "/help — Show this menu\n\n"
        "What's on your mind? ✨",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text(
        "🌸 *April — Help*\n\n"
        "*Available Commands:*\n"
        "• /start — Wake me up\n"
        "• /help — Show this menu\n"
        "• /clear — Clear conversation memory\n"
        "• /memory — Show memory stats\n"
        "• /about — About April\n\n"
        "*Tips:*\n"
        "• I remember the last 30 messages of our chat\n"
        "• I know your personal info (edit `personal_info.py` to update)\n"
        "• I work on your phone and laptop via Telegram\n"
        "• I run 24/7 on the cloud ☁️",
        parse_mode="Markdown",
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    chat_id = update.effective_chat.id
    count = memory.get_message_count(chat_id)
    memory.clear_history(chat_id)
    await update.message.reply_text(
        f"🧹 Cleared {count} messages from memory.\n"
        "Fresh start! What would you like to talk about? 🌱"
    )


async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    chat_id = update.effective_chat.id
    stats = memory.get_stats(chat_id)
    await update.message.reply_text(
        f"🧠 *April's Memory Stats*\n\n"
        f"• Total messages stored: {stats['total']}\n"
        f"• Your messages: {stats['user_count']}\n"
        f"• My replies: {stats['assistant_count']}\n"
        f"• Oldest memory: {stats['oldest'] or 'none yet'}\n"
        f"• Latest memory: {stats['latest'] or 'none yet'}\n\n"
        f"I keep the last *{MAX_HISTORY}* messages active in my brain at a time.",
        parse_mode="Markdown",
    )


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text(
        "🌸 *About April*\n\n"
        "I'm your personal AI assistant, built just for you.\n\n"
        "*Brain:* Llama 3.3 70B via Groq\n"
        "*Memory:* SQLite (persistent)\n"
        "*Hosting:* Railway (24/7 cloud)\n"
        "*Interface:* Telegram + Desktop HUD\n\n"
        "I'm private — only you can talk to me. 💫",
        parse_mode="Markdown",
    )


# ─── Message Handler ──────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_reply

    if not is_owner(update):
        await update.message.reply_text("🔒 I'm a private assistant. Access denied.")
        return

    chat_id = update.effective_chat.id
    user_message = update.message.text.strip()

    if not user_message:
        return

    memory.add_message(chat_id, "user", user_message)
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    history = memory.get_history(chat_id, limit=MAX_HISTORY)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=0.75,
        )
        reply = response.choices[0].message.content.strip()

        memory.add_message(chat_id, "assistant", reply)

        # ── Save for Electron desktop app to poll ───────────────────────
        last_reply["text"] = reply
        last_reply["timestamp"] = int(time.time() * 1000)
        # ────────────────────────────────────────────────────────────────

        await send_long_message(update, reply)

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        await update.message.reply_text(
            "😅 I hit a small snag. Give me a second and try again!"
        )


# ─── Error Handler ────────────────────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Unhandled error: {context.error}", exc_info=context.error)


# ─── Starlette HTTP Routes ────────────────────────────────────────────────────
async def telegram_webhook(request: Request):
    """Receive Telegram updates via webhook."""
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return PlainTextResponse("OK")


async def get_last_reply(request: Request):
    """Electron desktop app polls this to get April's latest reply."""
    since = int(request.query_params.get("since", 0))
    if last_reply["timestamp"] > since:
        return JSONResponse(last_reply, headers={"Access-Control-Allow-Origin": "*"})
    return JSONResponse({"text": "", "timestamp": 0}, headers={"Access-Control-Allow-Origin": "*"})


async def health_check(request: Request):
    return PlainTextResponse("April is alive 🌸")


# ─── Build PTB app (global so webhook route can access it) ───────────────────
ptb_app: Application = None


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    global ptb_app

    validate_config()
    logger.info("🌸 Starting April...")

    ptb_app = Application.builder().token(TELEGRAM_TOKEN).build()

    ptb_app.add_handler(CommandHandler("start", cmd_start))
    ptb_app.add_handler(CommandHandler("help", cmd_help))
    ptb_app.add_handler(CommandHandler("clear", cmd_clear))
    ptb_app.add_handler(CommandHandler("memory", cmd_memory))
    ptb_app.add_handler(CommandHandler("about", cmd_about))
    ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    ptb_app.add_error_handler(error_handler)

    if WEBHOOK_URL:
        # ── Cloud mode (Railway) — Starlette + uvicorn ────────────────────
        logger.info(f"☁️  Webhook mode | Port: {PORT} | URL: {WEBHOOK_URL}")

        starlette_app = Starlette(routes=[
            Route(f"/{TELEGRAM_TOKEN}", telegram_webhook, methods=["POST"]),
            Route("/last-reply",        get_last_reply,   methods=["GET"]),
            Route("/health",            health_check,     methods=["GET"]),
        ])

        async def on_startup():
            await ptb_app.initialize()
            await ptb_app.bot.set_webhook(
                url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}",
                drop_pending_updates=True,
            )
            await ptb_app.bot.set_my_commands([
                BotCommand("start",  "Wake April up"),
                BotCommand("help",   "Show all commands"),
                BotCommand("clear",  "Clear memory"),
                BotCommand("memory", "Memory stats"),
                BotCommand("about",  "About April"),
            ])
            await ptb_app.start()
            logger.info(f"✅ April is live! Owner chat ID: {OWNER_CHAT_ID}")

        async def on_shutdown():
            await ptb_app.stop()

        starlette_app.add_event_handler("startup",  on_startup)
        starlette_app.add_event_handler("shutdown", on_shutdown)

        uvicorn.run(starlette_app, host="0.0.0.0", port=PORT)

    else:
        # ── Local mode — polling ──────────────────────────────────────────
        logger.info("💻 Polling mode (local)")

        async def post_init(app: Application):
            await app.bot.set_my_commands([
                BotCommand("start",  "Wake April up"),
                BotCommand("help",   "Show all commands"),
                BotCommand("clear",  "Clear memory"),
                BotCommand("memory", "Memory stats"),
                BotCommand("about",  "About April"),
            ])
            logger.info(f"✅ April is live! Owner chat ID: {OWNER_CHAT_ID}")

        ptb_app.post_init = post_init
        ptb_app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

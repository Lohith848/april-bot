"""
April — Your Personal 24/7 AI Assistant (Telegram Bot)
Built with: python-telegram-bot + Groq (Llama 3.3 70B) + SQLite
"""

import logging
import sys
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from groq import Groq

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


# ─── Helpers ─────────────────────────────────────────────────────────────────
def is_owner(update: Update) -> bool:
    """Only allow the owner to use April."""
    return update.effective_chat.id == OWNER_CHAT_ID


async def send_long_message(update: Update, text: str):
    """Split and send messages that exceed Telegram's 4096 char limit."""
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
        "*Interface:* Telegram\n\n"
        "I'm private — only you can talk to me. "
        "I know your personal info and remember our conversations. "
        "Think of me as your always-available, always-ready assistant. 💫",
        parse_mode="Markdown",
    )


# ─── Message Handler ──────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("🔒 I'm a private assistant. Access denied.")
        return

    chat_id = update.effective_chat.id
    user_message = update.message.text.strip()

    if not user_message:
        return

    # Store user message
    memory.add_message(chat_id, "user", user_message)

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Build message history for Groq
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

        # Store assistant reply
        memory.add_message(chat_id, "assistant", reply)

        await send_long_message(update, reply)

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        await update.message.reply_text(
            "😅 I hit a small snag. Give me a second and try again!"
        )


# ─── Error Handler ────────────────────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Unhandled error: {context.error}", exc_info=context.error)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    # Validate config first
    validate_config()

    logger.info("🌸 Starting April...")

    # Build the application
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("memory", cmd_memory))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    # Set bot commands menu (shows in Telegram UI)
    async def post_init(app: Application):
        await app.bot.set_my_commands([
            BotCommand("start", "Wake April up"),
            BotCommand("help", "Show all commands"),
            BotCommand("clear", "Clear memory"),
            BotCommand("memory", "Memory stats"),
            BotCommand("about", "About April"),
        ])
        logger.info(f"✅ April is live! Owner chat ID: {OWNER_CHAT_ID}")

    app.post_init = post_init

    if WEBHOOK_URL:
        # ── Cloud mode (Railway) — webhook ────────────────────────────────
        logger.info(f"☁️  Webhook mode | Port: {PORT} | URL: {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}",
            drop_pending_updates=True,
        )
    else:
        # ── Local mode — polling ──────────────────────────────────────────
        logger.info("💻 Polling mode (local)")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

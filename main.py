import os
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, filters
)
from collections import defaultdict
from fastapi import FastAPI, Request
import threading

# === CONFIGURATION ===
TOKEN = "8141321315:AAEdQAi30YBrc-Kfu7puiSpoTk_rTsT6W00"
ADMIN_ID = 6356015122  # Apna Telegram ID yaha dalna
app = FastAPI()

# === Message Tracking ===
message_db = defaultdict(dict)
message_counter = 1

# === BOT APP ===
bot_app = ApplicationBuilder().token(TOKEN).build()

# === GROUP HANDLER ===
async def group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global message_counter
    msg = update.message

    if not msg:
        return

    mentioned = context.bot.username.lower() in (msg.text or "").lower()
    is_reply = msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id

    if mentioned or is_reply:
        await context.bot.send_chat_action(chat_id=ADMIN_ID, action=ChatAction.TYPING)

        name = msg.from_user.full_name
        uname = msg.from_user.username or "NoUsername"
        text = msg.text or "[Non-text message]"

        message_db[message_counter] = {
            "chat_id": msg.chat_id,
            "message_id": msg.message_id
        }

        forward_text = f"ID - {message_counter}\nName: {name} (@{uname})\nMessage: {text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=forward_text)
        message_counter += 1

# === ADMIN REPLY ===
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /y <id> <message>")
        return

    try:
        msg_id = int(args[0])
        reply_text = " ".join(args[1:])
        info = message_db.get(msg_id)

        if not info:
            await update.message.reply_text("ID not found.")
            return

        await context.bot.send_chat_action(chat_id=info["chat_id"], action=ChatAction.TYPING)
        await context.bot.send_message(chat_id=info["chat_id"], reply_to_message_id=info["message_id"], text=reply_text)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# === PRIVATE HANDLER ===
async def private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat_id == ADMIN_ID:
        return

    if msg.sticker:
        await msg.reply_text("Sticker nahi, message bhejo.")
        return

    if msg.text:
        await context.bot.send_chat_action(chat_id=ADMIN_ID, action=ChatAction.TYPING)
        name = msg.from_user.full_name
        uname = msg.from_user.username or "NoUsername"
        text = msg.text
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"Name: {name} (@{uname})\nMessage: {text}")

# === FASTAPI ENDPOINT ===
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "Bot is running!"}

# === HANDLERS ===
bot_app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT, group_message))
bot_app.add_handler(CommandHandler("y", reply_command))
bot_app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT, private_message))

# === START ===
def start_bot():
    import uvicorn
    asyncio.run(bot_app.initialize())
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    # Running the bot and FastAPI in separate threads for proper event loop handling
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

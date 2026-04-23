import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MY_CHAT_ID = int(os.getenv("MY_CHAT_ID"))

# Setup Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Setup logging
logging.basicConfig(level=logging.INFO)

# Simpan history chat per user
chat_histories = {}

# ── COMMAND /start ──
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Saya asisten AI pribadi kamu 🤖\n"
        "Ketik apa saja untuk mulai ngobrol!\n\n"
        "Perintah:\n"
        "/start - Mulai\n"
        "/clear - Hapus riwayat chat\n"
        "/ping - Cek bot aktif"
    )

# ── COMMAND /clear ──
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_histories[chat_id] = []
    await update.message.reply_text("Riwayat chat dihapus! Mulai percakapan baru 🗑️")

# ── COMMAND /ping ──
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif! 🟢")

# ── HANDLER PESAN BIASA ──
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_message = update.message.text

    # Inisialisasi history
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    # Kirim "mengetik..."
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # Buat chat dengan history
        chat = model.start_chat(history=chat_histories[chat_id])
        response = chat.send_message(user_message)
        reply = response.text

        # Simpan history
        chat_histories[chat_id] = chat.history

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ── PESAN TERJADWAL ──
async def kirim_pesan_terjadwal(bot):
    pesan_list = [
        "☀️ Selamat pagi! Sudah minum air hari ini?",
        "💪 Sudah makan siang? Jangan lupa istirahat sejenak!",
        "🌙 Malam! Sudah produktif hari ini? Ceritakan pada saya!",
        "⏰ Waktunya review target harianmu!",
    ]
    import random
    pesan = random.choice(pesan_list)
    await bot.send_message(chat_id=MY_CHAT_ID, text=pesan)

# ── MAIN ──
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Setup scheduler (kirim pesan setiap 5 jam)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        kirim_pesan_terjadwal,
        "interval",
        hours=5,
        args=[app.bot]
    )
    scheduler.start()

    print("Bot berjalan...")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())

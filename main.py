import telebot
from telebot import types
import os
from datetime import datetime
from flask import Flask
import threading

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = -1002445709942

if not TOKEN:
    raise Exception("BOT_TOKEN tidak ditemukan!")

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

app = Flask(__name__)

# ======================
# WEB SERVER (FLY NEED THIS)
# ======================
@app.route("/")
def home():
    return "Bot is running 🚀"

# ======================
# DATA STORAGE
# ======================
pending_users = set()
user_fess_count = {}
user_last_message = {}
total_fess_sent = 0

banned_words = ['anjing', 'bangsat', 'kontol', 'tolol']

# ======================
# HELPERS
# ======================
def contains_bad_words(text):
    return any(word in text.lower() for word in banned_words)

def can_send(user_id):
    today = datetime.now().date()

    if user_id not in user_fess_count:
        user_fess_count[user_id] = [(today, 1)]
        return True

    date_list = user_fess_count[user_id]

    if date_list[-1][0] != today:
        user_fess_count[user_id] = [(today, 1)]
        return True

    elif date_list[-1][1] < 5:
        user_fess_count[user_id][-1] = (today, date_list[-1][1] + 1)
        return True

    return False

# ======================
# COMMAND /START
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Kirim Menfess", callback_data="send_fess"))
    markup.add(types.InlineKeyboardButton("Lihat Statistik", callback_data="show_stats"))
    markup.add(types.InlineKeyboardButton("Hapus Fess Terakhir", callback_data="unsend_fess"))

    bot.send_message(message.chat.id, "Hai! Pilih menu:", reply_markup=markup)

# ======================
# CALLBACK MENU
# ======================
@bot.callback_query_handler(func=lambda call: True)
def callback_menu(call):
    user_id = call.from_user.id

    if call.data == "send_fess":
        if not can_send(user_id):
            bot.send_message(user_id, "Limit 5 menfess per hari.")
            return

        pending_users.add(user_id)
        bot.send_message(user_id, "Kirim menfess kamu sekarang.")

    elif call.data == "show_stats":
        bot.send_message(user_id, f"Total menfess terkirim: {total_fess_sent}")

    bot.answer_callback_query(call.id)

# ======================
# HANDLE MESSAGE
# ======================
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def handle_fess(message):
    global total_fess_sent

    user_id = message.from_user.id

    if user_id not in pending_users:
        bot.reply_to(message, "Klik /start dulu.")
        return

    try:
        msg_sent = None

        if message.content_type == 'text':
            text = message.text.strip()

            if contains_bad_words(text):
                return bot.reply_to(message, "Ada kata terlarang.")

            msg_sent = bot.send_message(CHANNEL_ID, "💚 " + text)

        elif message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            caption = message.caption or ""

            if contains_bad_words(caption):
                return bot.reply_to(message, "Caption terlarang.")

            msg_sent = bot.send_photo(CHANNEL_ID, file_id, caption="💚 " + caption)

        if msg_sent:
            total_fess_sent += 1
            user_last_message[user_id] = msg_sent.message_id
            bot.send_message(user_id, "Terkirim!")

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

    pending_users.discard(user_id)

# ======================
# RUN FUNCTIONS
# ======================
def run_web():
    app.run(host="0.0.0.0", port=8080)

def run_bot():
    bot.infinity_polling(skip_pending=True)

# ======================
# MAIN (FLY SAFE VERSION)
# ======================
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    run_bot()

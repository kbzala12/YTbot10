import telebot import sqlite3 import os from flask import Flask from threading import Thread

========== CONFIG ==========

BOT_TOKEN = "8192810260:AAFfhjDfNywZIzkrlVmtAuKFL5_E-ZnsOmU" ADMIN_ID = 7459795138 YOUTUBE_CHANNEL = "https://youtube.com/@kishorsinhzala.?si=L3MaMmn51a-ZyV_y" TELEGRAM_GROUP = "https://t.me/FreesubscribeYouTube2k" VIDEO_LIBRARY = [ {"url": "https://youtu.be/G2YCGapVbEc?si=OOfd-eH3a75Dsi9S", "code": "BOOST1"}, {"url": "https://youtube.com/shorts/KP7TXFpTCeI?si=xRVrDsy53OnCwDcN", "code": "BOOM2"}, {"url": "https://youtube.com/shorts/dVUy6aWYgHI?si=-ffnsKllf4Kl-BMM", "code": "REACH3"}, {"url": "https://youtu.be/SWMtSEvaiFU", "code": "ZALA4"}, {"url": "https://youtu.be/VID5", "code": "XTRA5"}, {"url": "https://youtu.be/VIDi7", "code": "BOOM6"}, {"url": "https://youtu.be/VID8", "code": "KISHOR7"}, {"url": "https://youtu.be/VID8", "code": "TREND8"}, {"url": "https://youtu.be/VID9", "code": "ROCKET9"}, {"url": "https://youtu.be/VID10", "code": "BOOMUP10"} ]

bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect("users.db", check_same_thread=False) cursor = conn.cursor() cursor.execute(""" CREATE TABLE IF NOT EXISTS users ( id TEXT PRIMARY KEY, points INTEGER DEFAULT 0, videos INTEGER DEFAULT 0, shares INTEGER DEFAULT 0, referrals INTEGER DEFAULT 0, claimed_codes TEXT DEFAULT "" ) """) conn.commit()

def check_user(user_id): cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,)) if cursor.fetchone() is None: cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,)) conn.commit()

def get_user(user_id): cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)) row = cursor.fetchone() return { "id": row[0], "points": row[1], "videos": row[2], "shares": row[3], "referrals": row[4], "claimed_codes": row[5] }

@bot.message_handler(commands=['start']) def send_welcome(msg): user_id = str(msg.from_user.id) check_user(user_id) ref_id = msg.text.split(" ")[-1] if len(msg.text.split()) > 1 else None

if ref_id and ref_id != user_id:
    cursor.execute("SELECT id FROM users WHERE id = ?", (ref_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE users SET referrals = referrals + 1, points = points + 50 WHERE id = ?", (ref_id,))
        conn.commit()

bot.reply_to(msg, f"""

🎉 स्वागत है! आपका यूट्यूब चैनल: {YOUTUBE_CHANNEL} हमारा टेलीग्राम ग्रुप: {TELEGRAM_GROUP}

आप वीडियो देखकर, शेयर करके और रेफरल से पॉइंट्स कमा सकते हैं।

📌 कमांड: 🎥 वीडियो देखा 📊 मेरी जानकारी 🔗 मेरा रेफरल लिंक

सफलता की ओर कदम बढ़ाइए 🚀 """)

@bot.message_handler(func=lambda msg: msg.text == "📊 मेरी जानकारी") def user_info(msg): user_id = str(msg.from_user.id) check_user(user_id) u = get_user(user_id)

watched = u['videos']
total = len(VIDEO_LIBRARY)
progress = ""
for i in range(total):
    progress += f"{'✅' if i < watched else '❌'} {i+1} "

bot.reply_to(msg, f"""📊 आपकी जानकारी:

🔢 कुल पॉइंट्स: {u['points']} 🎬 देखे गए वीडियो: {watched}/{total} 🎯 प्रगति: {progress} """)

@bot.message_handler(func=lambda msg: msg.text == "🔗 मेरा रेफरल लिंक") def refer_link(msg): user_id = str(msg.from_user.id) link = f"https://t.me/Hkzyt_bot?start={user_id}" bot.reply_to(msg, f"🔗 आपका रेफरल लिंक:\n{link}")

@bot.message_handler(func=lambda msg: msg.text and not msg.text.startswith("/")) def code_check(msg): user_id = str(msg.from_user.id) code = msg.text.strip().upper()

check_user(user_id)
user = get_user(user_id)
claimed = user["claimed_codes"].split(",") if user["claimed_codes"] else []

for index, video in enumerate(VIDEO_LIBRARY):
    if code == video["code"]:
        if code in claimed:
            bot.reply_to(msg, "⚠️ आपने पहले ही इस कोड का उपयोग किया है।")
            return

        claimed.append(code)
        new_claimed = ",".join(claimed)
        cursor.execute("UPDATE users SET claimed_codes = ?, videos = videos + 1, points = points + 10 WHERE id = ?",
                       (new_claimed, user_id))
        conn.commit()

        bot.reply_to(msg, f"✅ सही कोड! वीडियो #{index + 1} के लिए +10 पॉइंट्स मिल गए।")
        return

bot.reply_to(msg, "❌ गलत कोड! कृपया वीडियो देखकर सही कोड टाइप करें।")

@bot.message_handler(func=lambda msg: msg.text == "🎥 वीडियो देखा") def send_all_videos(msg): text = f"📺 सभी वीडियो देखें और कोड टाइप करें:\n\nहमारा यूट्यूब चैनल: {YOUTUBE_CHANNEL}\nटेलीग्राम ग्रुप: {TELEGRAM_GROUP}\n\n" for i, video in enumerate(VIDEO_LIBRARY): text += f"🎬 Video {i + 1}: {video['url']}\n📌 कोड: (वीडियो में मिलेगा)\n\n" bot.send_message(msg.chat.id, text)

=================== WEB SERVER FOR RENDER ===================

app = Flask('') @app.route('/') def home(): return "बॉट एक्टिव है।"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()

print("🤖 Bot is running...") bot.polling()


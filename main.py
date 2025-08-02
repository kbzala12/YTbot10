========== .env लोड करना ==========

import os, sqlite3 from datetime import datetime from flask import Flask from threading import Thread import telebot from dotenv import load_dotenv

load_dotenv()  # .env से वैरिएबल्स लोड करें

========== CONFIG ==========

BOT_TOKEN = os.getenv("BOT_TOKEN") ADMIN_ID = 7459795138 TELEGRAM_GROUP = "@FreesubscribeYouTube2k" YOUTUBE_LINK = "https://opensea.io/item/ethereum/0xbd3531da5cf5857e7cfaa92426877b022e612cf8/734"

========== KEEP ALIVE ==========

app = Flask('') @app.route('/') def home(): return "बॉट चल रहा है।" def run(): app.run(host='0.0.0.0', port=8080) def keep_alive(): Thread(target=run).start() keep_alive()

========== DB SETUP ==========

conn = sqlite3.connect("bot.db", check_same_thread=False) cursor = conn.cursor() cursor.execute(""" CREATE TABLE IF NOT EXISTS users ( id TEXT PRIMARY KEY, points INTEGER DEFAULT 0, videos INTEGER DEFAULT 0, shares INTEGER DEFAULT 0, ref INTEGER DEFAULT 0, referred_by TEXT, claimed_codes TEXT DEFAULT '' ) """) conn.commit()

========== BOT ==========

bot = telebot.TeleBot(BOT_TOKEN)

========== VIDEO LIST ==========

VIDEO_LIBRARY = [ {"url": "https://youtu.be/G2YCGapVbEc?si=OOfd-eH3a75Dsi9S", "code": "BOOST1"}, {"url": "https://youtube.com/shorts/KP7TXFpTCeI?si=xRVrDsy53OnCwDcN", "code": "BOOM2"}, {"url": "https://youtube.com/shorts/dVUy6aWYgHI?si=-ffnsKllf4Kl-BMM", "code": "REACH3"}, {"url": "https://youtu.be/SWMtSEvaiFU", "code": "ZALA4"}, {"url": "https://youtu.be/VID5", "code": "XTRA5"}, {"url": "https://youtu.be/VID6", "code": "BOOM6"}, {"url": "https://youtu.be/VID7", "code": "KISHOR7"}, {"url": "https://youtu.be/VID8", "code": "TREND8"}, {"url": "https://youtu.be/VID9", "code": "ROCKET9"}, {"url": "https://youtu.be/VID10", "code": "BOOMUP10"} ]

========== बाकी कोड समान रहेगा ==========

(START हैंडलर, यूट्यूब स्क्रिनशॉट, एडमिन कमांड्स, etc.)

print("🤖 बॉट अब चल रहा है...") bot.infinity_polling()


import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from flask import Flask, render_template_string
import threading
import sqlite3
import os

# कॉन्फिगरेशन
TOKEN = "7978191312:AAFyWVkBruuR42HTuTd_sQxFaKHBrre0VWw"
ADMIN_ID = 7459795138
REWARD_COINS = 100
REQUIRED_GROUPS = [
    {"name": "Bingyt Bot", "url": "https://t.me/Bingyt_bot"},
    {"name": "Boom Up", "url": "https://t.me/boomupbot10"},
    {"name": "Free Subscribe", "url": "https://t.me/FreesubscribeYouTube2k"}
]

# डेटाबेस सेटअप
conn = sqlite3.connect('bot_db.sqlite', check_same_thread=False)
cursor = conn.cursor()

# टेबल्स बनाएं
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    coins INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    joined_all_groups INTEGER DEFAULT 0,
    join_date TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS referrals (
    referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    referred_id INTEGER,
    date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES users (user_id),
    FOREIGN KEY (referred_id) REFERENCES users (user_id)
)
''')
conn.commit()

# Flask वेब डैशबोर्ड
app = Flask(__name__)

@app.route('/')
def dashboard():
    # टॉप रेफरर्स
    cursor.execute('''
        SELECT username, referrals, coins 
        FROM users 
        ORDER BY referrals DESC 
        LIMIT 10
    ''')
    top_referrers = cursor.fetchall()
    
    # टोटल स्टैट्स
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE joined_all_groups=1')
    active_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM referrals')
    total_referrals = cursor.fetchone()[0]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Referral Bot Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .card {{ background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 10px 0; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            .btn {{ background: #0088cc; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>🤖 Referral Bot Dashboard</h1>
        
        <div class="card">
            <h3>📊 स्टैटिस्टिक्स</h3>
            <p>कुल यूजर्स: {total_users}</p>
            <p>एक्टिव यूजर्स: {active_users}</p>
            <p>कुल रेफरल्स: {total_referrals}</p>
        </div>
        
        <h2>🏆 टॉप 10 रेफरर्स</h2>
        <table>
            <tr>
                <th>रैंक</th>
                <th>यूजरनेम</th>
                <th>रेफरल्स</th>
                <th>कॉइन्स</th>
            </tr>
            {% for i, user in enumerate(top_referrers, 1) %}
            <tr>
                <td>{i}</td>
                <td>{{user[0] or 'Anonymous'}}</td>
                <td>{{user[1]}}</td>
                <td>{{user[2]}}</td>
            </tr>
            {% endfor %}
        </table>
        
        <div style="margin-top: 20px;">
            <a href="https://t.me/share/url?url=https://t.me/your_bot&text=Join%20this%20awesome%20bot!" class="btn">
                📢 बोट शेयर करें
            </a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, enumerate=enumerate, top_referrers=top_referrers)

def run_flask():
    app.run(host='0.0.0.0', port=5000)

# Flask थ्रेड स्टार्ट करें
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# लॉगिंग
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def check_groups(user_id, context):
    try:
        for group in REQUIRED_GROUPS:
            group_username = group["url"].split('/')[-1]
            chat_member = await context.bot.get_chat_member(f"@{group_username}", user_id)
            if chat_member.status in ['left', 'kicked']:
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking groups: {e}")
        return False

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    referral_link = f"https://t.me/{context.bot.username}?start={user.id}"
    
    # रेफरल चेक
    if context.args:
        referrer_id = int(context.args[0])
        if referrer_id != user.id:  # खुद को रेफर नहीं कर सकता
            cursor.execute('SELECT 1 FROM users WHERE user_id=?', (user.id,))
            if not cursor.fetchone():
                # नया यूजर
                cursor.execute('''
                    INSERT INTO users (user_id, username, coins)
                    VALUES (?, ?, ?)
                ''', (user.id, user.username or str(user.id), REWARD_COINS))
                
                # रेफरल रिकॉर्ड
                cursor.execute('''
                    INSERT INTO referrals (referrer_id, referred_id)
                    VALUES (?, ?)
                ''', (referrer_id, user.id))
                
                # रेफरर को इनाम
                cursor.execute('''
                    UPDATE users 
                    SET coins = coins + ?, referrals = referrals + 1 
                    WHERE user_id = ?
                ''', (REWARD_COINS, referrer_id))
                conn.commit()
                
                await update.message.reply_text(
                    f"🎉 आपको {REWARD_COINS} कॉइन्स मिले हैं रेफरल बोनस के रूप में!"
                )
                
                # रेफरर को नोटिफिकेशन
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎊 {user.username or user.id} ने आपके रेफरल लिंक से जॉइन किया!\n"
                             f"आपको {REWARD_COINS} कॉइन्स मिले हैं!"
                    )
                except Exception as e:
                    logger.error(f"Could not notify referrer: {e}")
    
    # यूजर रजिस्टर करें
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username) 
        VALUES (?, ?)
    ''', (user.id, user.username or str(user.id)))
    conn.commit()
    
    # ग्रुप्स चेक
    has_joined = await check_groups(user.id, context)
    
    if has_joined:
        cursor.execute('UPDATE users SET joined_all_groups=1 WHERE user_id=?', (user.id,))
        conn.commit()
        
        # बैलेंस चेक
        cursor.execute('SELECT coins FROM users WHERE user_id=?', (user.id,))
        coins = cursor.fetchone()[0]
        
        keyboard = [
            [InlineKeyboardButton("📢 इनवाइट फ्रेंड्स", 
             url=f"https://t.me/share/url?url={referral_link}&text=Join%20this%20awesome%20bot%20and%20get%20{REWARD_COINS}%20coins!")],
            [InlineKeyboardButton("💰 मेरे कॉइन्स", callback_data="balance")],
            [InlineKeyboardButton("🌐 वेब डैशबोर्ड", url="http://your-server-ip:5000")]
        ]
        
        await update.message.reply_text(
            f"👋 नमस्ते {user.first_name}!\n\n"
            f"🔗 आपका रेफरल लिंक:\n<code>{referral_link}</code>\n\n"
            f"💰 आपके कॉइन्स: <b>{coins}</b>\n\n"
            f"दोस्तों को इनवाइट करके {REWARD_COINS} कॉइन्स प्रति रेफरल कमाएं!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:
        # ग्रुप जॉइन करने के लिए बटन्स
        buttons = []
        for group in REQUIRED_GROUPS:
            buttons.append([InlineKeyboardButton(
                f"जॉइन {group['name']}", 
                url=group["url"]
            )])
        
        buttons.append([InlineKeyboardButton(
            "✅ मैंने जॉइन कर लिया", 
            callback_data="check_groups"
        )])
        
        await update.message.reply_text(
            "⚠️ बोट का उपयोग करने के लिए कृपया निम्न ग्रुप्स जॉइन करें:\n\n" +
            "\n".join([f"• {group['url']}" for group in REQUIRED_GROUPS]) +
            "\n\nसभी ग्रुप्स जॉइन करने के बाद नीचे बटन दबाएं:",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "balance":
        cursor.execute('SELECT coins FROM users WHERE user_id=?', (query.from_user.id,))
        coins = cursor.fetchone()[0]
        
        await query.edit_message_text(
            f"💰 आपके पास <b>{coins} कॉइन्स</b> हैं!\n\n"
            f"अधिक कॉइन्स कमाने के लिए दोस्तों को इनवाइट करें।",
            parse_mode='HTML'
        )
    
    elif query.data == "check_groups":
        has_joined = await check_groups(query.from_user.id, context)
        
        if has_joined:
            cursor.execute('UPDATE users SET joined_all_groups=1 WHERE user_id=?', (query.from_user.id,))
            conn.commit()
            
            await query.edit_message_text(
                "🎉 सत्यापन पूरा हुआ! अब आप बोट का पूरा उपयोग कर सकते हैं।\n\n"
                "/start टाइप करके मुख्य मेनू देखें।"
            )
        else:
            await query.answer(
                "❌ आप अभी भी सभी ग्रुप्स में नहीं हैं। कृपया सभी लिंक्स पर क्लिक करके जॉइन करें।",
                show_alert=True
            )

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    
    updater.start_polling()
    logger.info("बोट चल रहा है...")
    updater.idle()

if __name__ == '__main__':
    main()
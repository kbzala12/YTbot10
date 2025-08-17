import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
import sqlite3
import random
import string

# लॉगिंग कॉन्फ़िगर करें
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# कॉन्फ़िगरेशन
BOT_TOKEN = "7978191312:AAFyWVkBruuR42HTuTd_sQxFaKHBrre0VWw"  # अपना बॉट टोकन यहाँ डालें
ADMIN_ID = 7459795138  # अपना एडमिन ID
WEB_APP_URL = "https://0e8b2f63-6f1c-4921-9feb-42115ce5360f-00-2amqt62lj9glu.picard.replit.dev"
GROUP_ID = "@boomupbot10"  # अपना ग्रुप यूजरनेम या ID (-100...)

# डेटाबेस इनिशियलाइज़ेशन
def init_db():
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    # यूजर्स टेबल
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id TEXT UNIQUE,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        coin_balance INTEGER DEFAULT 0,
        today_coins INTEGER DEFAULT 0,
        total_coins_earned INTEGER DEFAULT 0,
        videos_watched INTEGER DEFAULT 0,
        referral_code TEXT UNIQUE,
        referred_by TEXT,
        is_group_member BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # रेफरल्स टेबल
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (referrer_id) REFERENCES users (id),
        FOREIGN KEY (referred_user_id) REFERENCES users (id)
    ''')
    
    conn.commit()
    conn.close()

# रेफरल कोड जनरेटर
def generate_referral_code():
    return f"REF{random.randint(1000, 9999)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}"

# यूजर मैनेजमेंट
def get_or_create_user(telegram_id, username=None, first_name=None, last_name=None, referral_code=None):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(telegram_id),))
    user = cursor.fetchone()
    
    if not user:
        ref_code = generate_referral_code()
        cursor.execute('''
            INSERT INTO users (telegram_id, username, first_name, last_name, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(telegram_id), username, first_name, last_name, ref_code, referral_code))
        
        user_id = cursor.lastrowid
        
        # रेफरल बोनस
        if referral_code:
            cursor.execute('SELECT id FROM users WHERE referral_code = ?', (referral_code,))
            referrer = cursor.fetchone()
            
            if referrer:
                referrer_id = referrer[0]
                cursor.execute('''
                    UPDATE users 
                    SET coin_balance = coin_balance + 100, 
                        total_coins_earned = total_coins_earned + 100
                    WHERE id = ?
                ''', (referrer_id,))
                
                cursor.execute('''
                    INSERT INTO referrals (referrer_id, referred_user_id)
                    VALUES (?, ?)
                ''', (referrer_id, user_id))
        
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
    
    conn.close()
    return user

# /start कमांड
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    referral_code = context.args[0] if context.args else None
    
    db_user = get_or_create_user(
        user.id, 
        user.username, 
        user.first_name, 
        user.last_name, 
        referral_code
    )
    
    welcome_message = f"""
🎬 *Video Coin Earner Bot में आपका स्वागत है!* 🎬

नमस्ते {user.first_name}! 

📹 *वीडियो देखें और कॉइन कमाएं:*
• प्रत्येक वीडियो के लिए 30 कॉइन्स
• दैनिक लिमिट: 900 कॉइन्स
• 100+ भारतीय YouTube वीडियो

👥 *रेफरल सिस्टम:*
• दोस्तों को इनवाइट करें
• प्रत्येक नए यूजर के लिए 100 कॉइन्स

🔗 *URL जमा करें:*
• अपना YouTube वीडियो जमा करें
• 200 कॉइन्स पाएं

⚠️ *महत्वपूर्ण:* बॉट का उपयोग करने के लिए पहले हमारे ग्रुप में जॉइन करना आवश्यक है।

आपका रेफरल कोड: `{db_user[9]}`
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🚀 ऐप लॉन्च करें", web_app=WebAppInfo(url=WEB_APP_URL)),
            InlineKeyboardButton("👥 ग्रुप जॉइन करें", url=f"https://t.me/{GROUP_ID.replace('@', '')}")
        ],
        [
            InlineKeyboardButton(
                "📢 दोस्तों को इनवाइट करें", 
                switch_inline_query=f"🎬 Video Coin Earner Bot से कॉइन्स कमाएं! {WEB_APP_URL}?ref={db_user[9]}"
            )
        ]
    ]
    
    await update.message.reply_text(
        welcome_message, 
        parse_mode='Markdown', 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# /verify कमांड
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    try:
        chat_member = await context.bot.get_chat_member(GROUP_ID, user.id)
        is_member = chat_member.status in ['member', 'administrator', 'creator']
        
        if is_member:
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_group_member = 1 WHERE telegram_id = ?', (str(user.id),))
            conn.commit()
            conn.close()
            
            await update.message.reply_text(
                '✅ वेरिफिकेशन सफल! अब आप कॉइन्स कमा सकते हैं।',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 ऐप लॉन्च करें", web_app=WebAppInfo(url=WEB_APP_URL))]
                ])
            )
        else:
            await update.message.reply_text(
                '❌ कृपया पहले ग्रुप जॉइन करें।',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👥 ग्रुप जॉइन करें", url=f"https://t.me/{GROUP_ID.replace('@', '')}")]
                ])
            )
    except Exception as e:
        logging.error(f"Verify error: {e}")
        await update.message.reply_text('वेरिफिकेशन में त्रुटि। बाद में प्रयास करें।')

# /wallet कमांड
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(user.id),))
    db_user = cursor.fetchone()
    
    if not db_user:
        await update.message.reply_text('कृपया पहले /start कमांड का उपयोग करें।')
        return
    
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (db_user[0],))
    referral_count = cursor.fetchone()[0]
    conn.close()
    
    wallet_message = f"""
💰 *आपका वॉलेट*

🪙 उपलब्ध कॉइन्स: {db_user[5]}
📊 कुल कमाए गए: {db_user[7]}
📹 देखे गए वीडियो: {db_user[8]}
👥 सफल रेफरल्स: {referral_count}
📅 आज कमाए गए: {db_user[6]}/900
"""
    
    await update.message.reply_text(
        wallet_message, 
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 ऐप लॉन्च करें", web_app=WebAppInfo(url=WEB_APP_URL))]
        )
    )

# /referral कमांड
async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(user.id),))
    db_user = cursor.fetchone()
    
    if not db_user:
        await update.message.reply_text('कृपया पहले /start कमांड का उपयोग करें।')
        return
    
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (db_user[0],))
    referral_count = cursor.fetchone()[0]
    conn.close()
    
    referral_message = f"""
👥 *रेफरल सिस्टम*

🔗 आपका रेफरल लिंक:
`{WEB_APP_URL}?ref={db_user[9]}`

📊 आपके स्टेट्स:
• कुल रेफरल्स: {referral_count}
• रेफरल से कमाया: {referral_count * 100} कॉइन्स
"""
    
    await update.message.reply_text(
        referral_message, 
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 शेयर करें", switch_inline_query=f"कॉइन्स कमाएं: {WEB_APP_URL}?ref={db_user[9]}")],
            [InlineKeyboardButton("🚀 ऐप लॉन्च करें", web_app=WebAppInfo(url=WEB_APP_URL))]
        )
    )

# /help कमांड
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
🎬 *बॉट कमांड्स*

/start - बॉट शुरू करें
/wallet - वॉलेट देखें
/referral - रेफरल जानकारी
/verify - ग्रुप मेंबरशिप वेरिफाई करें
/help - सहायता
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# मेन फंक्शन
def main() -> None:
    init_db()  # डेटाबेस इनिशियलाइज़
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # कमांड हैंडलर्स
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("wallet", wallet))
    app.add_handler(CommandHandler("referral", referral))
    app.add_handler(CommandHandler("help", help_command))
    
    # बॉट स्टार्ट करें
    app.run_polling()

if __name__ == '__main__':
    main()
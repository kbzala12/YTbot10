import telebot

# ✅ यहाँ अपना बॉट टोकन डालें
BOT_TOKEN = "8192810260:AAFfhjDfNywZIzkrlVmtAuKFL5_E-ZnsOmU"

bot = telebot.TeleBot(BOT_TOKEN)

# 👋 Welcome message
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "नमस्ते! यह एक रिवॉर्ड बॉट है। 🎁")

# ✉️ General message handler
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"आपने भेजा: {message.text}")

# ✅ Bot polling शुरू करें
if __name__ == "__main__":
    bot.polling()


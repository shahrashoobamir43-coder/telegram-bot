import telebot
import requests

TELEGRAM_TOKEN = "8273287076:AAEDG2pjUF-b67FwzSd7qpi8umGlBAk74H4"
OPENROUTER_KEY = "5427733464c75ce7be20a260a7ce4db691570e615b3ddcfd6e6aa2aee3a6581f"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def ask_ai(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openrouter/free",
        "messages": [
            {"role": "system", "content": "جواب‌هات کوتاه، خلاصه و مستقیم باشن. از توضیحات اضافه و طولانی پرهیز کن. حداکثر در ۲-۳ جمله جواب بده مگر اینکه کاربر صریحاً توضیح بیشتر بخواد."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 300
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        result = r.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return str(result)
    except Exception as e:
        return f"خطا: {e}"

@bot.message_handler(func=lambda m: True)
def handle(message):
    try:
        bot.send_chat_action(message.chat.id, "typing")
        response = ask_ai(message.text)
        for i in range(0, len(response), 4000):
            bot.reply_to(message, response[i:i+4000])
    except Exception as e:
        print(f"خطا نادیده گرفته شد: {e}")

bot.infinity_polling()

import telebot
import requests
import os
from gtts import gTTS
from langdetect import detect

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

last_response = {}

SYSTEM_PROMPT = (
    "جواب‌های کوتاه، خلاصه و مستقیم باش. از توضیحات اضافه و طولانی پرهیز کن. "
    "حداکثر در ۲-۳ جمله جواب بده مگر اینکه کاربر صریحاً توضیح بیشتر بخواد. "
    "همیشه دقیقاً به همان زبانی که کاربر با آن پیام داده پاسخ بده (هر زبانی که باشد: فارسی، عربی، انگلیسی، ترکی، فرانسوی، اسپانیایی، آلمانی، روسی، اردو، چینی و غیره). "
    "هرگز زبان را عوض نکن مگر اینکه کاربر صریحاً بخواد."
)

LANG_CODE_MAP = {
    "fa": "fa", "ar": "ar", "en": "en", "tr": "tr", "fr": "fr",
    "es": "es", "de": "de", "ru": "ru", "ur": "ur", "zh-cn": "zh-CN",
    "hi": "hi", "it": "it", "pt": "pt", "ja": "ja", "ko": "ko",
}


def ask_ai(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openrouter/free",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
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


def ask_ai_vision(image_url, caption=""):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    prompt_text = caption if caption else "این تصویر را توصیف و تفسیر کن."
    data = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        "max_tokens": 300
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        result = r.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return str(result)
    except Exception as e:
        return f"خطا: {e}"


def detect_lang_code(text):
    try:
        code = detect(text)
        return LANG_CODE_MAP.get(code, "fa")
    except Exception:
        return "fa"


def text_to_voice(text, filepath):
    lang_code = detect_lang_code(text)
    tts = gTTS(text=text, lang=lang_code)
    tts.save(filepath)


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        bot.send_chat_action(message.chat.id, "typing")
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"

        caption = message.caption if message.caption else ""
        response = ask_ai_vision(file_url, caption)

        last_response[message.chat.id] = response
        for i in range(0, len(response), 4000):
            bot.reply_to(message, response[i:i + 4000])
    except Exception as e:
        print(f"خطا نادیده گرفته شد: {e}")


@bot.message_handler(func=lambda m: m.text and m.text.strip() in ["ویس بده", "/voice", "ویس", "voice", "send voice"])
def handle_voice_request(message):
    try:
        chat_id = message.chat.id
        text = last_response.get(chat_id)
        if not text:
            bot.reply_to(message, "هنوز جوابی برای تبدیل به ویس وجود نداره. اول یه سوال بپرس.")
            return

        bot.send_chat_action(chat_id, "record_voice")
        voice_path = f"/tmp/voice_{chat_id}.mp3"
        text_to_voice(text, voice_path)

        with open(voice_path, "rb") as voice_file:
            bot.send_voice(chat_id, voice_file)

        os.remove(voice_path)
    except Exception as e:
        print(f"خطا نادیده گرفته شد: {e}")
        bot.reply_to(message, "متاسفانه نتونستم ویس بسازم.")


@bot.message_handler(func=lambda m: True)
def handle(message):
    try:
        bot.send_chat_action(message.chat.id, "typing")
        response = ask_ai(message.text)
        last_response[message.chat.id] = response
        for i in range(0, len(response), 4000):
            bot.reply_to(message, response[i:i + 4000])
    except Exception as e:
        print(f"خطا نادیده گرفته شد: {e}")


bot.infinity_polling()
import telebot
from telebot import types
import requests
import time
import random
import os
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = '8347775737:AAFSFwXxse-7c3SsOu4JSTN7jSfdYh4vJa4'
GROQ_KEY = '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'
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

bot = telebot.TeleBot(BOT_TOKEN)

# ========== КНОПКИ ==========
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💬 GPT 5.2", "🎨 Создать фото")
    markup.add("🍌 Nano Banana", "❓ Помощь")
    return markup

# ========== AI ФУНКЦИЯ ==========
def get_ai_response(message):
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Ты GPT 5.2 — мощный AI-ассистент. Отвечай кратко, понятно, с юмором. Помогай решать любые вопросы."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.8,
        "max_tokens": 500
    }
    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        return "❌ Ошибка API. Попробуй позже."
    except:
        return "❌ Технические проблемы. Напиши позже."

# ========== ГЕНЕРАЦИЯ ФОТО ==========
def generate_image_from_prompt(prompt):
    """Генерирует описание картинки (бесплатно, без API)"""
    # Используем AI для описания
    ai_prompt = f"Опиши подробно, как выглядит: {prompt}. Напиши красочное описание для генерации изображения."
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Ты художник, который создаёт красивые описания для картинок."},
            {"role": "user", "content": ai_prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 300
    }
    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
        if resp.status_code == 200:
            description = resp.json()["choices"][0]["message"]["content"].strip()
            return f"🎨 *Твой запрос:* {prompt}\n\n✨ *Описание для художника:*\n{description}\n\n(для реальной генерации нужен API Midjourney или DALL·E)"
        return f"🎨 *Твой запрос:* {prompt}\n\n✨ Представь себе: {prompt} в стиле цифрового искусства, яркие цвета, детализированная композиция."
    except:
        return f"🎨 *Твой запрос:* {prompt}\n\n✨ Отличная идея для картинки! (для реальной генерации нужен платный API)"

# ========== NANO BANANA (обработка фото) ==========
def apply_nano_banana(image):
    img = image.convert('RGB')
    img = ImageEnhance.Brightness(img).enhance(1.2)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = ImageEnhance.Color(img).enhance(1.15)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except:
        font = ImageFont.load_default()
    draw.text((10, 10), "🍌 NANOBANANO 🍌", fill=(255, 215, 0), font=font)
    draw.text((10, img.height - 50), "✨ обработано ✨", fill=(255, 200, 100), font=font)
    return img

def process_photo(file_id):
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    img = Image.open(io.BytesIO(file))
    return apply_nano_banana(img)

# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start(message):
    welcome = """🤖 *NanoBanano AI — бесплатный мощный бот!*

*Возможности:*
💬 GPT 5.2 — отвечаю на любые вопросы
🎨 Создать фото — опиши желаемую картинку
🍌 Nano Banana — обработаю любое фото

*Как пользоваться:*
• Нажми кнопку 💬 GPT 5.2 и задай вопрос
• Нажми 🎨 Создать фото и напиши описание
• Нажми 🍌 Nano Banana и отправь фото

*Всё бесплатно!* 🚀

По вопросам: @avgustc"""
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(), parse_mode='Markdown')

# ========== GPT 5.2 ==========
@bot.message_handler(func=lambda msg: msg.text == "💬 GPT 5.2")
def gpt_mode(message):
    bot.send_message(message.chat.id, "💬 *GPT 5.2* готов! Напиши свой вопрос.", reply_markup=main_menu(), parse_mode='Markdown')
    bot.register_next_step_handler(message, process_gpt)

def process_gpt(message):
    bot.send_chat_action(message.chat.id, 'typing')
    answer = get_ai_response(message.text)
    bot.send_message(message.chat.id, answer, reply_markup=main_menu(), parse_mode='Markdown')

# ========== СОЗДАТЬ ФОТО ==========
@bot.message_handler(func=lambda msg: msg.text == "🎨 Создать фото")
def create_photo(message):
    bot.send_message(message.chat.id, "🎨 *Напиши описание картинки, которую хочешь создать*\n\nНапример: *киберпанк кот в неоне* или *закат на море с пальмами*", reply_markup=main_menu(), parse_mode='Markdown')
    bot.register_next_step_handler(message, process_photo_generation)

def process_photo_generation(message):
    bot.send_chat_action(message.chat.id, 'typing')
    result = generate_image_from_prompt(message.text)
    bot.send_message(message.chat.id, result, reply_markup=main_menu(), parse_mode='Markdown')

# ========== NANO BANANA ==========
@bot.message_handler(func=lambda msg: msg.text == "🍌 Nano Banana")
def nano_mode(message):
    bot.send_message(message.chat.id, "🍌 *Nano Banana* готов! Отправь мне фото, и я обработаю его.", reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    photo = message.photo[-1]
    status_msg = bot.send_message(message.chat.id, "🍌 *Обрабатываю фото...*", parse_mode='Markdown')
    
    try:
        processed = process_photo(photo.file_id)
        output = io.BytesIO()
        processed.save(output, format='JPEG')
        output.seek(0)
        bot.send_photo(message.chat.id, output, caption="✨ *Обработано Nano Banana!*", parse_mode='Markdown')
        bot.delete_message(message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ *Ошибка:* {e}", message.chat.id, status_msg.message_id, parse_mode='Markdown')

# ========== ПОМОЩЬ ==========
@bot.message_handler(func=lambda msg: msg.text == "❓ Помощь")
def help_handler(message):
    help_text = """🤖 *NanoBanano AI — бесплатный бот*

*Возможности:*

💬 *GPT 5.2*
Просто задай любой вопрос — AI ответит

🎨 *Создать фото*
Напиши описание картинки — я создам детальное описание для художника

🍌 *Nano Banana*
Отправь фото — я обработаю:
• Увеличу яркость и контраст
• Добавлю насыщенность
• Наложу фирменный стикер

*Всё бесплатно!* 🚀

По вопросам: @avgustc"""
    bot.send_message(message.chat.id, help_text, reply_markup=main_menu(), parse_mode='Markdown')

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🤖 NanoBanano AI (бесплатная версия) запущен!")
    bot.polling(none_stop=True)

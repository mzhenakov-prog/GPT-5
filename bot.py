import telebot
from telebot import types
import requests
import time
import random
import os
import io
import urllib.parse
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import sqlite3

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = '8347775737:AAFSFwXxse-7c3SsOu4JSTN7jSfdYh4vJa4'
GROQ_KEY = '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'
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище для временных данных
user_photos = {}  # {user_id: {'photos': [], 'step': '...'}}

# ========== КНОПКИ ==========
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💬 GPT 5.2", "🎨 Создать фото")
    markup.add("🍌 Nano Banana", "🤝 Объединить фото", "❓ Помощь")
    return markup

# ========== AI ФУНКЦИЯ (текст) ==========
def get_ai_response(message):
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Ты GPT 5.2 — мощный AI-ассистент. Отвечай кратко, понятно, с юмором."},
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

# ========== АНАЛИЗ ФОТО ЧЕРЕЗ GPT ==========
def analyze_photo_with_gpt(image_data, question):
    """Отправляет фото в AI для анализа"""
    # Кодируем фото в base64
    encoded = base64.b64encode(image_data).decode('utf-8')
    
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Проанализируй это изображение. {question}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}
                ]
            }
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        return "❌ Не удалось проанализировать фото."
    except Exception as e:
        return f"❌ Ошибка: {e}"

# ========== ГЕНЕРАЦИЯ ФОТО ==========
def generate_image(prompt):
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}"

# ========== NANO BANANA ==========
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

def process_single_photo(file_id):
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    img = Image.open(io.BytesIO(file))
    return apply_nano_banana(img)

def download_photo(file_id):
    file_info = bot.get_file(file_id)
    return bot.download_file(file_info.file_path)

# ========== ОБЪЕДИНЕНИЕ ФОТО ==========
def merge_two_photos(img1_data, img2_data, prompt):
    img1 = Image.open(io.BytesIO(img1_data))
    img2 = Image.open(io.BytesIO(img2_data))
    
    target_size = (500, 500)
    img1 = img1.resize(target_size, Image.LANCZOS)
    img2 = img2.resize(target_size, Image.LANCZOS)
    
    result = Image.new('RGB', (1000, 500))
    result.paste(img1, (0, 0))
    result.paste(img2, (500, 0))
    
    draw = ImageDraw.Draw(result)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((10, result.height - 40), f"✨ {prompt[:50]}", fill=(255, 255, 255), font=font)
    draw.text((10, result.height - 20), "🍌 Nano Banana AI", fill=(255, 215, 0), font=font)
    
    return result

# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start(message):
    welcome = """🤖 *NanoBanano AI — мощный бот!*

*Возможности:*
💬 GPT 5.2 — отвечаю на вопросы (текст и фото)
🎨 Создать фото — генерация картинок
🍌 Nano Banana — обработка фото
🤝 Объединить фото — объединяю 2 фото по промту

*Как использовать GPT с фото:*
1. Нажми 💬 GPT 5.2
2. Отправь фото (можно с вопросом)
3. Получи анализ изображения!

*Всё бесплатно!* 🚀

По вопросам: @avgustc"""
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(), parse_mode='Markdown')

# ========== GPT 5.2 (текст + фото) ==========
@bot.message_handler(func=lambda msg: msg.text == "💬 GPT 5.2")
def gpt_mode(message):
    bot.send_message(message.chat.id, "💬 *GPT 5.2* готов!\n\nОтправь текст или фото — я отвечу!", reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(content_types=['photo'], func=lambda msg: True)
def handle_photo_for_gpt(message):
    # Проверяем, что пользователь в режиме GPT (или просто обрабатываем)
    user_id = message.from_user.id
    
    # Если пользователь в режиме объединения фото — пропускаем
    if user_id in user_photos and user_photos[user_id].get('step') in ['waiting_photo1', 'waiting_photo2', 'waiting_prompt']:
        handle_photo_for_merge(message)
        return
    
    # Получаем фото
    photo = message.photo[-1]
    caption = message.caption or "Что на этом фото?"
    
    status_msg = bot.send_message(message.chat.id, "🔍 *Анализирую фото...*", parse_mode='Markdown')
    
    try:
        # Скачиваем фото
        file_info = bot.get_file(photo.file_id)
        image_data = bot.download_file(file_info.file_path)
        
        # Анализируем через AI
        analysis = analyze_photo_with_gpt(image_data, caption)
        
        bot.edit_message_text(f"🖼 *Анализ фото:*\n\n{analysis}", message.chat.id, status_msg.message_id, parse_mode='Markdown')
    except Exception as e:
        bot.edit_message_text(f"❌ *Ошибка:* {e}", message.chat.id, status_msg.message_id, parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text and msg.text != "💬 GPT 5.2" and msg.text not in ["🎨 Создать фото", "🍌 Nano Banana", "🤝 Объединить фото", "❓ Помощь"])
def handle_text(message):
    # Обычный текст в GPT режиме
    bot.send_chat_action(message.chat.id, 'typing')
    answer = get_ai_response(message.text)
    bot.send_message(message.chat.id, answer, reply_markup=main_menu(), parse_mode='Markdown')

# ========== СОЗДАТЬ ФОТО ==========
@bot.message_handler(func=lambda msg: msg.text == "🎨 Создать фото")
def create_photo(message):
    bot.send_message(message.chat.id, "🎨 *Напиши описание картинки*", reply_markup=main_menu(), parse_mode='Markdown')
    bot.register_next_step_handler(message, process_photo_generation)

def process_photo_generation(message):
    bot.send_chat_action(message.chat.id, 'typing')
    status = bot.send_message(message.chat.id, "🎨 *Генерирую картинку...*", parse_mode='Markdown')
    try:
        image_url = generate_image(message.text)
        bot.send_photo(message.chat.id, image_url, caption=f"🎨 *{message.text}*", parse_mode='Markdown')
        bot.delete_message(message.chat.id, status.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ *Ошибка:* {e}", message.chat.id, status.message_id, parse_mode='Markdown')

# ========== NANO BANANA (одно фото) ==========
@bot.message_handler(func=lambda msg: msg.text == "🍌 Nano Banana")
def nano_mode(message):
    bot.send_message(message.chat.id, "🍌 *Nano Banana* готов! Отправь фото для обработки.", reply_markup=main_menu(), parse_mode='Markdown')

# ========== ОБЪЕДИНИТЬ ФОТО ==========
@bot.message_handler(func=lambda msg: msg.text == "🤝 Объединить фото")
def merge_mode(message):
    user_id = message.from_user.id
    user_photos[user_id] = {'photos': [], 'step': 'waiting_photo1'}
    bot.send_message(message.chat.id, "📸 *Отправь ПЕРВОЕ фото*", reply_markup=main_menu(), parse_mode='Markdown')

def handle_photo_for_merge(message):
    user_id = message.from_user.id
    photo = message.photo[-1]
    
    if user_id not in user_photos:
        return
    
    user_photos[user_id]['photos'].append(photo.file_id)
    
    if user_photos[user_id]['step'] == 'waiting_photo1':
        user_photos[user_id]['step'] = 'waiting_photo2'
        bot.send_message(message.chat.id, "📸 *Отправь ВТОРОЕ фото*", reply_markup=main_menu(), parse_mode='Markdown')
    else:
        user_photos[user_id]['step'] = 'waiting_prompt'
        bot.send_message(message.chat.id, "📝 *Напиши промт*\n\nНапример: *сделай так, чтобы мы стояли рядом*", reply_markup=main_menu(), parse_mode='Markdown')
        bot.register_next_step_handler(message, process_merge_prompt, user_photos[user_id]['photos'])

def process_merge_prompt(message, photo_ids):
    user_id = message.from_user.id
    prompt = message.text
    
    status_msg = bot.send_message(message.chat.id, "🤝 *Объединяю фото...*", parse_mode='Markdown')
    
    try:
        img1_data = download_photo(photo_ids[0])
        img2_data = download_photo(photo_ids[1])
        
        result = merge_two_photos(img1_data, img2_data, prompt)
        
        output = io.BytesIO()
        result.save(output, format='JPEG')
        output.seek(0)
        bot.send_photo(message.chat.id, output, caption=f"✨ *Объединено по промту:*\n{prompt}", parse_mode='Markdown')
        
        bot.delete_message(message.chat.id, status_msg.message_id)
        del user_photos[user_id]
        
    except Exception as e:
        bot.edit_message_text(f"❌ *Ошибка:* {e}", message.chat.id, status_msg.message_id, parse_mode='Markdown')
        del user_photos[user_id]

# ========== ОБРАБОТКА ФОТО ДЛЯ NANO BANANA ==========
@bot.message_handler(content_types=['photo'])
def handle_photo_for_nano(message):
    user_id = message.from_user.id
    
    # Если в режиме объединения — пропускаем
    if user_id in user_photos:
        return
    
    status_msg = bot.send_message(message.chat.id, "🍌 *Обрабатываю фото...*", parse_mode='Markdown')
    try:
        processed = process_single_photo(message.photo[-1].file_id)
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
    help_text = """🤖 *NanoBanano AI*

*Возможности:*

💬 *GPT 5.2* — умный AI-ассистент (текст + анализ фото)

🎨 *Создать фото* — генерация по тексту

🍌 *Nano Banana* — обработка фото с эффектами

🤝 *Объединить фото* — объединяю 2 фото по промту

*Как использовать GPT с фото:*
1. Нажми 💬 GPT 5.2
2. Отправь фото (можно добавить вопрос в подписи)
3. Получи анализ изображения!

*По вопросам:* @avgustc"""
    bot.send_message(message.chat.id, help_text, reply_markup=main_menu(), parse_mode='Markdown')

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🤖 NanoBanano AI (с анализом фото) запущен!")
    bot.polling(none_stop=True)

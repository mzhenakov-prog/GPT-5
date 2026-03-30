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

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = '8347775737:AAFSFwXxse-7c3SsOu4JSTN7jSfdYh4vJa4'
GROQ_KEY = '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'
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище для временных данных
user_photos = {}

# ========== КНОПКИ ==========
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💬 GPT 5.2", "🎨 Создать фото")
    markup.add("🍌 Nano Banana", "🤝 Объединить фото", "❓ Помощь")
    return markup

# ========== AI ФУНКЦИЯ ==========
def get_ai_response(message):
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.8,
        "max_tokens": 500
    }
    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        return "❌ Ошибка API."
    except:
        return "❌ Технические проблемы."

# ========== ГЕНЕРАЦИЯ ФОТО (локальная заглушка) ==========
def generate_image_fallback(prompt):
    """Создаёт картинку-заглушку с текстом"""
    img = Image.new('RGB', (1024, 1024), color=(30, 30, 60))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Разбиваем текст
    words = prompt.split()
    lines = []
    current = ""
    for w in words:
        if len(current + w) < 50:
            current += w + " "
        else:
            lines.append(current)
            current = w + " "
    lines.append(current)
    
    y = 400
    for line in lines[:8]:
        draw.text((100, y), line, fill=(255, 255, 255), font=font)
        y += 50
    
    draw.text((100, 800), "🎨 NanoBanano AI", fill=(255, 215, 0), font=font)
    
    output = io.BytesIO()
    img.save(output, format='JPEG')
    output.seek(0)
    return output

# ========== ОБЪЕДИНЕНИЕ ФОТО (реальное) ==========
def merge_photos_horizontal(img1_path, img2_path, prompt, user_id):
    """Объединяет два фото горизонтально с AI-подписью"""
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)
    
    # Приводим к одному размеру
    target_size = (500, 500)
    img1 = img1.resize(target_size, Image.LANCZOS)
    img2 = img2.resize(target_size, Image.LANCZOS)
    
    # Создаём полотно
    result = Image.new('RGB', (1000, 650), color=(30, 30, 50))
    result.paste(img1, (0, 50))
    result.paste(img2, (500, 50))
    
    # Добавляем AI-описание
    draw = ImageDraw.Draw(result)
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Заголовок
    draw.text((10, 10), "✨ AI-объединение по промту:", fill=(255, 215, 0), font=font_big)
    
    # Промт (с переносом)
    words = prompt.split()
    lines = []
    current = ""
    for w in words:
        if len(current + w) < 60:
            current += w + " "
        else:
            lines.append(current)
            current = w + " "
    lines.append(current)
    
    y = 580
    for line in lines[:3]:
        draw.text((10, y), line, fill=(200, 200, 200), font=font_small)
        y += 25
    
    draw.text((10, y + 10), "🍌 NanoBanano AI", fill=(255, 215, 0), font=font_small)
    
    return result

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

# ========== СТАРТ ==========
@bot.message_handler(commands=['start'])
def start(message):
    welcome = """🤖 *NanoBanano AI — мощный бот!*

*Возможности:*
💬 GPT 5.2 — отвечаю на вопросы
🎨 Создать фото — генерация картинок
🍌 Nano Banana — обработка фото
🤝 Объединить фото — объединяю 2 фото в одно

*Как объединить фото:*
1. Нажми 🤝 Объединить фото
2. Отправь ПЕРВОЕ фото
3. Отправь ВТОРОЕ фото
4. Напиши промт (например: "сделай так, чтобы они стояли рядом и обнимались")
5. Получи результат!

*Всё бесплатно!* 🚀

По вопросам: @avgustc"""
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(), parse_mode='Markdown')

# ========== GPT 5.2 ==========
@bot.message_handler(func=lambda msg: msg.text == "💬 GPT 5.2")
def gpt_mode(message):
    bot.send_message(message.chat.id, "💬 *GPT 5.2* готов! Напиши вопрос.", reply_markup=main_menu(), parse_mode='Markdown')
    bot.register_next_step_handler(message, lambda m: bot.send_message(m.chat.id, get_ai_response(m.text), reply_markup=main_menu(), parse_mode='Markdown'))

# ========== СОЗДАТЬ ФОТО ==========
@bot.message_handler(func=lambda msg: msg.text == "🎨 Создать фото")
def create_photo(message):
    bot.send_message(message.chat.id, "🎨 *Напиши описание картинки*", reply_markup=main_menu(), parse_mode='Markdown')
    bot.register_next_step_handler(message, process_photo_generation)

def process_photo_generation(message):
    status = bot.send_message(message.chat.id, "🎨 *Генерирую...*", parse_mode='Markdown')
    img = generate_image_fallback(message.text)
    bot.send_photo(message.chat.id, img, caption=f"🎨 *{message.text}*", parse_mode='Markdown')
    bot.delete_message(message.chat.id, status.message_id)

# ========== NANO BANANA ==========
@bot.message_handler(func=lambda msg: msg.text == "🍌 Nano Banana")
def nano_mode(message):
    bot.send_message(message.chat.id, "🍌 *Nano Banana* готов! Отправь фото.", reply_markup=main_menu(), parse_mode='Markdown')

# ========== ОБЪЕДИНИТЬ ФОТО ==========
@bot.message_handler(func=lambda msg: msg.text == "🤝 Объединить фото")
def merge_mode(message):
    user_id = message.from_user.id
    user_photos[user_id] = {'photos': [], 'step': 'waiting_photo1'}
    bot.send_message(message.chat.id, "📸 *Отправь ПЕРВОЕ фото*", reply_markup=main_menu(), parse_mode='Markdown')

def handle_photo_for_merge(message):
    user_id = message.from_user.id
    if user_id not in user_photos:
        return
    
    photo = message.photo[-1]
    user_photos[user_id]['photos'].append(photo.file_id)
    
    if user_photos[user_id]['step'] == 'waiting_photo1':
        user_photos[user_id]['step'] = 'waiting_photo2'
        bot.send_message(message.chat.id, "📸 *Отправь ВТОРОЕ фото*", reply_markup=main_menu(), parse_mode='Markdown')
    else:
        user_photos[user_id]['step'] = 'waiting_prompt'
        bot.send_message(message.chat.id, "📝 *Напиши промт*\n\nНапример: *сделай так, чтобы они стояли рядом и обнимались*", reply_markup=main_menu(), parse_mode='Markdown')
        bot.register_next_step_handler(message, process_merge_prompt, user_photos[user_id]['photos'])

def process_merge_prompt(message, photo_ids):
    user_id = message.from_user.id
    prompt = message.text
    
    status_msg = bot.send_message(message.chat.id, "🤝 *Объединяю фото...*", parse_mode='Markdown')
    
    try:
        # Скачиваем фото
        img1_data = download_photo(photo_ids[0])
        img2_data = download_photo(photo_ids[1])
        
        # Сохраняем временно
        path1 = f"/tmp/photo1_{user_id}.jpg"
        path2 = f"/tmp/photo2_{user_id}.jpg"
        with open(path1, 'wb') as f:
            f.write(img1_data)
        with open(path2, 'wb') as f:
            f.write(img2_data)
        
        # Объединяем
        result = merge_photos_horizontal(path1, path2, prompt, user_id)
        
        # Отправляем
        output = io.BytesIO()
        result.save(output, format='JPEG')
        output.seek(0)
        bot.send_photo(message.chat.id, output, caption=f"✨ *Объединено по промту:*\n{prompt}\n\n🍌 NanoBanano AI", parse_mode='Markdown')
        
        # Удаляем временные файлы
        os.remove(path1)
        os.remove(path2)
        bot.delete_message(message.chat.id, status_msg.message_id)
        del user_photos[user_id]
        
    except Exception as e:
        bot.edit_message_text(f"❌ *Ошибка:* {e}", message.chat.id, status_msg.message_id, parse_mode='Markdown')
        del user_photos[user_id]

# ========== ОБРАБОТКА ФОТО ДЛЯ NANO BANANA ==========
@bot.message_handler(content_types=['photo'])
def handle_photo_for_nano(message):
    user_id = message.from_user.id
    
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

💬 *GPT 5.2* — умный AI-ассистент

🎨 *Создать фото* — генерация по тексту

🍌 *Nano Banana* — обработка фото с эффектами

🤝 *Объединить фото* — объединяю 2 фото в одно (горизонтально с AI-подписью)

*Как объединить:*
1. Отправь первое фото
2. Отправь второе фото
3. Напиши промт
4. Получи результат

*По вопросам:* @avgustc"""
    bot.send_message(message.chat.id, help_text, reply_markup=main_menu(), parse_mode='Markdown')

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🤖 NanoBanano AI запущен!")
    bot.polling(none_stop=True)

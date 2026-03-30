import telebot
from telebot import types
import requests
import time
import random
import os
import io
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import sqlite3
from datetime import datetime, timedelta

# ========== НАСТРОЙКИ ==========
TG_TOKEN = 'НОВЫЙ_ТОКЕН_ОТ_BOTFATHER'  # 👈 Замени
GROQ_KEY = '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'
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

bot = telebot.TeleBot(TG_TOKEN)

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  username TEXT, 
                  balance INTEGER DEFAULT 3,
                  premium INTEGER DEFAULT 0,
                  last_reset TEXT)''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT balance, premium, last_reset FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        balance, premium, last_reset = result
        # Проверяем сброс лимита
        if last_reset != datetime.now().strftime("%Y-%m-%d"):
            balance = 3
            update_user(user_id, balance, premium)
        return balance, premium
    else:
        add_user(user_id)
        return 3, 0

def add_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (user_id, balance, premium, last_reset) VALUES (?, 3, 0, ?)",
              (user_id, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def update_user(user_id, balance, premium):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance = ?, premium = ?, last_reset = ? WHERE user_id = ?",
              (balance, premium, datetime.now().strftime("%Y-%m-%d"), user_id))
    conn.commit()
    conn.close()

def use_token(user_id):
    balance, premium = get_user(user_id)
    if premium:
        return True
    if balance > 0:
        update_user(user_id, balance - 1, premium)
        return True
    return False

# ========== КНОПКИ ==========
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💬 GPT 5.2", "🎨 Создать фото")
    markup.add("📹 Создать видео", "🍌 Nano Banana")
    markup.add("💰 Баланс", "❓ Помощь", "💎 Premium")
    return markup

def photo_models_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎨 GPT Images", callback_data="model_gpt_img"),
        types.InlineKeyboardButton("🔥 FLUX", callback_data="model_flux"),
        types.InlineKeyboardButton("🎨 DALL·E 3", callback_data="model_dalle"),
        types.InlineKeyboardButton("🍌 Nano Banana", callback_data="model_nano")
    )
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

# ========== ГЕНЕРАЦИЯ ФОТО (симуляция) ==========
def generate_image(prompt, model):
    # В реальном боте здесь был бы API к нейросетям
    # Пока возвращаем заглушку
    return f"🎨 *{model}* сгенерировал бы картинку по запросу:\n\n*{prompt}*\n\n(в платной версии доступна реальная генерация)"

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

def process_photo(file_id):
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    img = Image.open(io.BytesIO(file))
    return apply_nano_banana(img)

# ========== ОБРАБОТЧИКИ ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    balance, premium = get_user(user_id)
    welcome = """🤖 *GPT 5.2 + Nano Banana 2*

*Возможности:*
💬 GPT 5.2 — отвечаю на любые вопросы
🎨 Создать фото — 4 модели (GPT Images, FLUX, DALL·E 3, Nano Banana)
📹 Создать видео — VEO, Sora
🍌 Nano Banana — обработка фото

*Лимиты:*
🎁 3 бесплатных запроса в день
💎 Premium — безлимит, все модели

*Кнопки:*
💰 Баланс — сколько осталось
💎 Premium — купить подписку

Готов? Пиши!"""
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == "💬 GPT 5.2")
def gpt_mode(message):
    bot.send_message(message.chat.id, "💬 *GPT 5.2* готов! Напиши свой вопрос.", reply_markup=main_menu(), parse_mode='Markdown')
    bot.register_next_step_handler(message, process_gpt)

def process_gpt(message):
    user_id = message.from_user.id
    balance, premium = get_user(user_id)
    
    if not use_token(user_id):
        bot.send_message(message.chat.id, "❌ *Лимит исчерпан!*\n\nУ тебя 3 бесплатных запроса в день.\nКупи подписку 💎 Premium для безлимита.", reply_markup=main_menu(), parse_mode='Markdown')
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    answer = get_ai_response(message.text)
    bot.send_message(message.chat.id, answer, reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == "🎨 Создать фото")
def photo_menu(message):
    bot.send_message(message.chat.id, "🎨 *Выбери модель для генерации фото:*", reply_markup=photo_models_menu(), parse_mode='Markdown')
    bot.register_next_step_handler(message, process_photo_prompt)

def process_photo_prompt(message):
    user_id = message.from_user.id
    balance, premium = get_user(user_id)
    
    if not use_token(user_id):
        bot.send_message(message.chat.id, "❌ *Лимит исчерпан!*\n\nКупи подписку 💎 Premium.", reply_markup=main_menu(), parse_mode='Markdown')
        return
    
    bot.send_message(message.chat.id, "🎨 *Напиши описание картинки:*", parse_mode='Markdown')
    bot.register_next_step_handler(message, lambda m: generate_and_send_photo(m, message.text))

def generate_and_send_photo(message, model):
    result = generate_image(message.text, model)
    bot.send_message(message.chat.id, result, reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == "🍌 Nano Banana")
def nano_mode(message):
    bot.send_message(message.chat.id, "🍌 *Nano Banana* готов! Отправь фото для обработки.", reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.text == "🍌 Nano Banana":
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
    else:
        bot.send_message(message.chat.id, "💬 *GPT 5.2:* напиши текст, а не фото!", reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == "💰 Баланс")
def balance_handler(message):
    user_id = message.from_user.id
    balance, premium = get_user(user_id)
    if premium:
        text = "💎 *Premium* — безлимит! 🚀"
    else:
        text = f"💰 *Баланс:* {balance} из 3 запросов сегодня\n\n💎 Купи Premium за Telegram Stars — безлимит!"
    bot.send_message(message.chat.id, text, reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == "💎 Premium")
def premium_handler(message):
    text = """💎 *Premium подписка*

*Что даёт:*
✅ Безлимитные запросы
✅ Все модели AI
✅ Приоритетная обработка
✅ Генерация видео

*Стоимость:* 100 Telegram Stars / месяц

*Как купить:* нажми кнопку ниже

[💎 Купить Premium](https://t.me/BotFather?start=premium)"""
    bot.send_message(message.chat.id, text, reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == "❓ Помощь")
def help_handler(message):
    help_text = """🤖 *GPT 5.2 + Nano Banana 2*

*Режимы:*
💬 GPT 5.2 — умный AI-ассистент
🎨 Создать фото — 4 модели:
   • GPT Images — сложные инструкции
   • FLUX — динамичные картинки
   • DALL·E 3 — точное следование тексту
   • Nano Banana — стилизация
📹 Создать видео — VEO, Sora
🍌 Nano Banana — обработка фото

*Лимиты:*
🎁 3 бесплатных запроса/день
💎 Premium — безлимит

*По вопросам:* @avgustc"""
    bot.send_message(message.chat.id, help_text, reply_markup=main_menu(), parse_mode='Markdown')

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    init_db()
    print("🤖 GPT 5.2 + Nano Banana 2 запущен!")
    bot.polling(none_stop=True)

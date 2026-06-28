"""
MH News Bot — ربات تحلیل خبر
─────────────────────────────
نیازمندی‌ها:
    pip install pyTelegramBotAPI google-generativeai duckduckgo-search

اجرا:
    python news_bot.py
"""

import telebot
from telebot import types
import google.generativeai as genai
from duckduckgo_search import DDGS
import json, re

# ──────────────────────────────────────────────
BOT_TOKEN  = "8925815734:AAHNN2EuK5kB5oiY8dRiMxQJm-hMDj-DM00"
GEMINI_KEY = "AQ.Ab8RN6KsP6b7z5vHuTgn5QvEhQ2NEYd_5c53isl6C6SlfI60Xg"
# ──────────────────────────────────────────────

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
bot = telebot.TeleBot(BOT_TOKEN)

# ─── ذخیره متن خبر کاربر ─────────────────────
user_news = {}

# ─── /start ──────────────────────────────────
@bot.message_handler(commands=['start'])
def start(msg):
    markup = main_menu()
    bot.send_message(
        msg.chat.id,
        "👋 سلام! به ربات تحلیل خبر MH خوش آمدی.\n\n"
        "📰 متن خبر رو بفرست، بعد از منوی پایین گزینه مورد نظرت رو انتخاب کن.",
        reply_markup=markup
    )

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 تحلیل خبر"),
        types.KeyboardButton("📝 خلاصه‌سازی"),
        types.KeyboardButton("🌐 ترجمه"),
        types.KeyboardButton("✍️ تصحیح املا"),
        types.KeyboardButton("🔍 بررسی صحت خبر"),
        types.KeyboardButton("ℹ️ راهنما")
    )
    return markup

# ─── دریافت متن خبر ──────────────────────────
@bot.message_handler(func=lambda m: m.text and m.text not in [
    "📊 تحلیل خبر", "📝 خلاصه‌سازی", "🌐 ترجمه",
    "✍️ تصحیح املا", "🔍 بررسی صحت خبر", "ℹ️ راهنما"
])
def receive_news(msg):
    user_news[msg.chat.id] = msg.text
    bot.send_message(
        msg.chat.id,
        "✅ خبر دریافت شد!\n\nحالا از منوی پایین گزینه مورد نظرت رو انتخاب کن 👇",
        reply_markup=main_menu()
    )

# ─── تحلیل خبر ───────────────────────────────
@bot.message_handler(func=lambda m: m.text == "📊 تحلیل خبر")
def analyze(msg):
    news = user_news.get(msg.chat.id)
    if not news:
        bot.send_message(msg.chat.id, "⚠️ اول متن خبر رو بفرست!")
        return
    wait = bot.send_message(msg.chat.id, "⏳ در حال تحلیل...")
    try:
        prompt = f"""این خبر را به فارسی کامل تحلیل کن:

متن خبر:
{news}

تحلیل شامل موارد زیر باشد:
1. 📌 موضوع اصلی خبر
2. 😊/😠 احساسات و لحن خبر (مثبت/منفی/خنثی)
3. 🎯 نکات کلیدی (حداکثر ۵ مورد)
4. 🌍 تأثیر و اهمیت این خبر
5. 📈 نتیجه‌گیری کلی

پاسخ را به فارسی و با فرمت واضح بنویس."""
        response = model.generate_content(prompt)
        bot.edit_message_text(f"📊 *تحلیل خبر:*\n\n{response.text}", msg.chat.id, wait.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطا: {e}", msg.chat.id, wait.message_id)

# ─── خلاصه‌سازی ──────────────────────────────
@bot.message_handler(func=lambda m: m.text == "📝 خلاصه‌سازی")
def summarize(msg):
    news = user_news.get(msg.chat.id)
    if not news:
        bot.send_message(msg.chat.id, "⚠️ اول متن خبر رو بفرست!")
        return
    wait = bot.send_message(msg.chat.id, "⏳ در حال خلاصه‌سازی...")
    try:
        prompt = f"""این متن را به فارسی خلاصه کن. خلاصه باید:
- حداکثر ۵ جمله باشد
- نکات اصلی را پوشش دهد
- واضح و روان باشد

متن:
{news}"""
        response = model.generate_content(prompt)
        bot.edit_message_text(f"📝 *خلاصه خبر:*\n\n{response.text}", msg.chat.id, wait.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطا: {e}", msg.chat.id, wait.message_id)

# ─── ترجمه ───────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "🌐 ترجمه")
def translate(msg):
    news = user_news.get(msg.chat.id)
    if not news:
        bot.send_message(msg.chat.id, "⚠️ اول متن خبر رو بفرست!")
        return
    wait = bot.send_message(msg.chat.id, "⏳ در حال ترجمه...")
    try:
        prompt = f"""این متن را بررسی کن:
- اگر فارسی است، به انگلیسی روان ترجمه کن
- اگر انگلیسی است، به فارسی روان ترجمه کن
- اگر زبان دیگری است، به فارسی ترجمه کن
- فقط ترجمه را بنویس، توضیح اضافه نده

متن:
{news}"""
        response = model.generate_content(prompt)
        bot.edit_message_text(f"🌐 *ترجمه:*\n\n{response.text}", msg.chat.id, wait.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطا: {e}", msg.chat.id, wait.message_id)

# ─── تصحیح املا ──────────────────────────────
@bot.message_handler(func=lambda m: m.text == "✍️ تصحیح املا")
def spell_check(msg):
    news = user_news.get(msg.chat.id)
    if not news:
        bot.send_message(msg.chat.id, "⚠️ اول متن خبر رو بفرست!")
        return
    wait = bot.send_message(msg.chat.id, "⏳ در حال بررسی...")
    try:
        prompt = f"""این متن را بررسی کن و غلط‌های املایی و نگارشی را اصلاح کن.

فرمت پاسخ:
✅ متن اصلاح‌شده:
[متن اصلاح‌شده]

📋 تغییرات:
[لیست تغییرات انجام‌شده، اگر تغییری نبود بنویس "غلط املایی یافت نشد"]

متن:
{news}"""
        response = model.generate_content(prompt)
        bot.edit_message_text(f"✍️ *تصحیح متن:*\n\n{response.text}", msg.chat.id, wait.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطا: {e}", msg.chat.id, wait.message_id)

# ─── بررسی صحت خبر ───────────────────────────
@bot.message_handler(func=lambda m: m.text == "🔍 بررسی صحت خبر")
def fact_check(msg):
    news = user_news.get(msg.chat.id)
    if not news:
        bot.send_message(msg.chat.id, "⚠️ اول متن خبر رو بفرست!")
        return
    wait = bot.send_message(msg.chat.id, "⏳ در حال جستجو و بررسی صحت خبر...")
    try:
        # استخراج کلمات کلیدی با Gemini
        kw_prompt = f"از این خبر ۳ تا ۵ کلمه کلیدی مهم به انگلیسی استخراج کن. فقط کلمات را با کاما جدا کن:\n{news}"
        kw_response = model.generate_content(kw_prompt)
        keywords = kw_response.text.strip()

        # جستجو در DuckDuckGo
        search_results = ""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(keywords, max_results=5))
                for r in results:
                    search_results += f"- {r.get('title','')}: {r.get('body','')[:200]}\n"
        except:
            search_results = "نتیجه جستجو یافت نشد"

        # تحلیل صحت با Gemini
        fact_prompt = f"""با توجه به اطلاعات زیر، صحت این خبر را بررسی کن:

خبر:
{news}

نتایج جستجو در اینترنت:
{search_results}

پاسخ را به فارسی و با این فرمت بنویس:
🎯 حکم: [واقعی / احتمالاً واقعی / نامشخص / احتمالاً کذب / کذب]
📊 درصد اطمینان: [عدد]٪
📝 دلایل: [توضیح کوتاه]
🔗 منابع مرتبط: [اگر یافت شد]"""

        fact_response = model.generate_content(fact_prompt)
        bot.edit_message_text(
            f"🔍 *بررسی صحت خبر:*\n\n{fact_response.text}",
            msg.chat.id, wait.message_id, parse_mode="Markdown"
        )
    except Exception as e:
        bot.edit_message_text(f"❌ خطا: {e}", msg.chat.id, wait.message_id)

# ─── راهنما ──────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "ℹ️ راهنما")
def help_cmd(msg):
    bot.send_message(
        msg.chat.id,
        "📖 *راهنمای استفاده:*\n\n"
        "۱. متن خبر رو بفرست\n"
        "۲. از منو گزینه مورد نظر رو انتخاب کن\n\n"
        "🔹 *📊 تحلیل خبر* — تحلیل کامل و نتیجه‌گیری\n"
        "🔹 *📝 خلاصه‌سازی* — خلاصه ۵ جمله‌ای\n"
        "🔹 *🌐 ترجمه* — فارسی↔انگلیسی خودکار\n"
        "🔹 *✍️ تصحیح املا* — رفع غلط‌های نگارشی\n"
        "🔹 *🔍 بررسی صحت* — جستجو و راستی‌آزمایی",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ─── اجرا ────────────────────────────────────
print("📰 ربات خبر MH شروع به کار کرد...")
bot.infinity_polling()

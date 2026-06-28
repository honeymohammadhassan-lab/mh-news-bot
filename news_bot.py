"""
MH News Bot — ربات تحلیل خبر با سیستم ژتون
─────────────────────────────────────────────
نیازمندی‌ها:
    pip install pyTelegramBotAPI google-generativeai duckduckgo-search

اجرا:
    python news_bot.py
"""

import telebot
from telebot import types
import google.generativeai as genai
from duckduckgo_search import DDGS
import json, os, time
from datetime import datetime, timedelta

# ──────────────────────────────────────────────
BOT_TOKEN  = "8925815734:AAHNN2EuK5kB5oiY8dRiMxQJm-hMDj-DM00"
GEMINI_KEY = "AQ.Ab8RN6KsP6b7z5vHuTgn5QvEhQ2NEYd_5c53isl6C6SlfI60Xg"
ADMIN_ID   = 8401423557
# ──────────────────────────────────────────────

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
bot = telebot.TeleBot(BOT_TOKEN)

# ─── فایل داده ───────────────────────────────
DATA_FILE = "news_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"card": "", "users": {}, "pending_payments": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── مدیریت ژتون ─────────────────────────────
def get_user(uid, name="کاربر"):
    data = load_data()
    uid = str(uid)
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": name,
            "tokens": 10,
            "last_daily": None,
            "status": "active"
        }
        save_data(data)
    return data, data["users"][uid]

def give_daily_tokens(uid):
    """هر ۲۴ ساعت ۸ ژتون رایگان"""
    data = load_data()
    uid = str(uid)
    user = data["users"].get(uid)
    if not user:
        return False, 0

    now = datetime.now()
    last = user.get("last_daily")

    if last is None or (now - datetime.fromisoformat(last)) >= timedelta(hours=24):
        user["tokens"] = user.get("tokens", 0) + 8
        user["last_daily"] = now.isoformat()
        data["users"][uid] = user
        save_data(data)
        return True, user["tokens"]
    return False, user.get("tokens", 0)

def use_token(uid):
    """مصرف یک ژتون — برمیگرداند True اگه موفق بود"""
    data = load_data()
    uid = str(uid)
    user = data["users"].get(uid, {})
    tokens = user.get("tokens", 0)
    if tokens <= 0:
        return False
    user["tokens"] = tokens - 1
    data["users"][uid] = user
    save_data(data)
    return True

def get_tokens(uid):
    data = load_data()
    return data["users"].get(str(uid), {}).get("tokens", 0)

def time_until_daily(uid):
    data = load_data()
    user = data["users"].get(str(uid), {})
    last = user.get("last_daily")
    if not last:
        return "همین الان"
    delta = timedelta(hours=24) - (datetime.now() - datetime.fromisoformat(last))
    if delta.total_seconds() <= 0:
        return "همین الان"
    hours = int(delta.total_seconds() // 3600)
    mins  = int((delta.total_seconds() % 3600) // 60)
    return f"{hours} ساعت و {mins} دقیقه دیگر"

# ─── ذخیره متن خبر ───────────────────────────
user_news = {}

# ─── منوی اصلی ───────────────────────────────
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 تحلیل خبر"),
        types.KeyboardButton("📝 خلاصه‌سازی"),
        types.KeyboardButton("🌐 ترجمه"),
        types.KeyboardButton("✍️ تصحیح املا"),
        types.KeyboardButton("🔍 بررسی صحت خبر"),
        types.KeyboardButton("💎 ژتون‌های من"),
        types.KeyboardButton("ℹ️ راهنما")
    )
    return markup

def no_token_message(uid):
    """پیام وقتی ژتون تموم شده"""
    next_daily = time_until_daily(uid)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 خرید ۱۰۰ ژتون — ۵۰,۰۰۰ تومان", callback_data="buy_tokens"))
    markup.add(types.InlineKeyboardButton(f"⏰ دریافت رایگان ({next_daily})", callback_data="daily_tokens"))
    return markup

# ─── /start ──────────────────────────────────
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.chat.id
    name = msg.chat.first_name or "کاربر"

    if uid == ADMIN_ID:
        admin_menu(uid)
        return

    data, user = get_user(uid, name)
    # بررسی ژتون روزانه
    gave, tokens = give_daily_tokens(uid)

    welcome = f"👋 سلام {name}!\n\n"
    if gave:
        welcome += f"🎁 ۸ ژتون روزانه به حسابت اضافه شد!\n"
    welcome += f"💎 ژتون‌های شما: {get_tokens(uid)}\n\n"
    welcome += "📰 متن خبر رو بفرست، بعد از منو گزینه مورد نظرت رو انتخاب کن."

    bot.send_message(uid, welcome, reply_markup=main_menu())

# ─── پنل ادمین ───────────────────────────────
def admin_menu(chat_id):
    data = load_data()
    card = data.get("card", "تنظیم نشده")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳 تغییر شماره کارت", callback_data="admin_set_card"))
    markup.add(types.InlineKeyboardButton("👥 آمار کاربران", callback_data="admin_stats"))
    bot.send_message(
        chat_id,
        f"🔐 *پنل ادمین ربات خبر*\n\n💳 شماره کارت: `{card}`",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(commands=['admin'])
def admin_cmd(msg):
    if msg.chat.id == ADMIN_ID:
        admin_menu(msg.chat.id)

# ─── دریافت پیام‌ها ───────────────────────────
@bot.message_handler(content_types=['photo', 'document', 'text'])
def handle_message(msg):
    uid = msg.chat.id
    text = msg.text or ""

    # ─── ادمین ───────────────────────────────
    if uid == ADMIN_ID:
        data = load_data()
        if data.get("_admin_awaiting_card"):
            data["card"] = text.strip()
            data["_admin_awaiting_card"] = False
            save_data(data)
            bot.send_message(ADMIN_ID, f"✅ شماره کارت ذخیره شد:\n`{data['card']}`", parse_mode="Markdown")
            return
        admin_menu(uid)
        return

    # ─── کاربر ───────────────────────────────
    get_user(uid, msg.chat.first_name or "کاربر")

    # دریافت فیش پرداخت
    if msg.content_type in ['photo', 'document']:
        data = load_data()
        uid_str = str(uid)
        if data.get("pending_payments", {}).get(uid_str) == "waiting_receipt":
            # فوروارد به ادمین
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"pay_approve_{uid}"),
                types.InlineKeyboardButton("❌ رد", callback_data=f"pay_reject_{uid}")
            )
            bot.send_message(
                ADMIN_ID,
                f"💰 *درخواست خرید ژتون*\n\n👤 {msg.chat.first_name or 'کاربر'}\n🆔 `{uid}`",
                parse_mode="Markdown"
            )
            bot.forward_message(ADMIN_ID, uid, msg.message_id)
            bot.send_message(ADMIN_ID, "پرداخت رو تایید می‌کنی؟", reply_markup=markup)
            data["pending_payments"][uid_str] = "waiting_admin"
            save_data(data)
            bot.send_message(uid, "⏳ فیش دریافت شد. منتظر تایید ادمین باش...", reply_markup=main_menu())
        return

    # منو
    menus = ["📊 تحلیل خبر", "📝 خلاصه‌سازی", "🌐 ترجمه", "✍️ تصحیح املا", "🔍 بررسی صحت خبر", "💎 ژتون‌های من", "ℹ️ راهنما"]

    if text not in menus:
        user_news[uid] = text
        tokens = get_tokens(uid)
        bot.send_message(uid, f"✅ خبر دریافت شد!\n💎 ژتون‌های شما: {tokens}\n\nاز منو گزینه مورد نظرت رو انتخاب کن 👇", reply_markup=main_menu())
        return

    # ─── ژتون‌های من ──────────────────────────
    if text == "💎 ژتون‌های من":
        tokens = get_tokens(uid)
        next_daily = time_until_daily(uid)
        gave, new_tokens = give_daily_tokens(uid)
        if gave:
            bot.send_message(uid, f"🎁 ۸ ژتون روزانه دریافت کردی!\n💎 ژتون‌های شما: {get_tokens(uid)}", reply_markup=main_menu())
        else:
            bot.send_message(uid, f"💎 ژتون‌های شما: {tokens}\n⏰ ژتون روزانه: {next_daily}", reply_markup=main_menu())
        return

    # ─── راهنما ───────────────────────────────
    if text == "ℹ️ راهنما":
        bot.send_message(
            uid,
            "📖 *راهنما:*\n\n"
            "۱. متن خبر رو بفرست\n"
            "۲. از منو گزینه انتخاب کن\n\n"
            "💎 *سیستم ژتون:*\n"
            "• شروع: ۱۰ ژتون رایگان\n"
            "• هر ۲۴ ساعت: ۸ ژتون رایگان\n"
            "• خرید: ۱۰۰ ژتون = ۵۰,۰۰۰ تومان\n\n"
            "🔹 تحلیل، خلاصه، ترجمه، تصحیح: ۱ ژتون\n"
            "🔹 بررسی صحت: ۲ ژتون",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return

    # ─── بررسی خبر و ژتون ────────────────────
    if uid not in user_news:
        bot.send_message(uid, "⚠️ اول متن خبر رو بفرست!", reply_markup=main_menu())
        return

    cost = 2 if text == "🔍 بررسی صحت خبر" else 1
    tokens = get_tokens(uid)

    if tokens < cost:
        # بررسی ژتون روزانه
        gave, new_tokens = give_daily_tokens(uid)
        if gave and new_tokens >= cost:
            use_token(uid)
            if cost == 2: use_token(uid)
            process_request(msg, text, uid)
        else:
            markup = no_token_message(uid)
            bot.send_message(
                uid,
                f"❌ *ژتون کافی ندارید!*\n\n"
                f"💎 ژتون فعلی: {get_tokens(uid)}\n"
                f"🔹 این عملیات نیاز به {cost} ژتون دارد\n\n"
                f"یکی از گزینه‌های زیر را انتخاب کن:",
                parse_mode="Markdown",
                reply_markup=markup
            )
        return

    # مصرف ژتون
    use_token(uid)
    if cost == 2: use_token(uid)
    process_request(msg, text, uid)

def process_request(msg, action, uid):
    news = user_news.get(uid, "")
    tokens = get_tokens(uid)

    if action == "📊 تحلیل خبر":
        wait = bot.send_message(uid, f"⏳ در حال تحلیل... (💎 {tokens} ژتون باقی‌مانده)")
        try:
            prompt = f"""این خبر را به فارسی کامل تحلیل کن:\n\n{news}\n\nشامل: موضوع، احساسات، نکات کلیدی، اهمیت، نتیجه‌گیری"""
            r = model.generate_content(prompt)
            bot.edit_message_text(f"📊 *تحلیل خبر:*\n\n{r.text}\n\n💎 ژتون باقی‌مانده: {tokens}", uid, wait.message_id, parse_mode="Markdown")
        except Exception as e:
            bot.edit_message_text(f"❌ خطا: {e}", uid, wait.message_id)

    elif action == "📝 خلاصه‌سازی":
        wait = bot.send_message(uid, f"⏳ در حال خلاصه‌سازی... (💎 {tokens} ژتون)")
        try:
            r = model.generate_content(f"این متن را در ۵ جمله به فارسی خلاصه کن:\n{news}")
            bot.edit_message_text(f"📝 *خلاصه:*\n\n{r.text}\n\n💎 ژتون باقی‌مانده: {tokens}", uid, wait.message_id, parse_mode="Markdown")
        except Exception as e:
            bot.edit_message_text(f"❌ خطا: {e}", uid, wait.message_id)

    elif action == "🌐 ترجمه":
        wait = bot.send_message(uid, f"⏳ در حال ترجمه... (💎 {tokens} ژتون)")
        try:
            r = model.generate_content(f"اگه فارسیه به انگلیسی، اگه انگلیسیه به فارسی ترجمه کن. فقط ترجمه:\n{news}")
            bot.edit_message_text(f"🌐 *ترجمه:*\n\n{r.text}\n\n💎 ژتون باقی‌مانده: {tokens}", uid, wait.message_id, parse_mode="Markdown")
        except Exception as e:
            bot.edit_message_text(f"❌ خطا: {e}", uid, wait.message_id)

    elif action == "✍️ تصحیح املا":
        wait = bot.send_message(uid, f"⏳ در حال بررسی... (💎 {tokens} ژتون)")
        try:
            r = model.generate_content(f"غلط‌های املایی این متن را اصلاح کن و تغییرات را بنویس:\n{news}")
            bot.edit_message_text(f"✍️ *تصحیح متن:*\n\n{r.text}\n\n💎 ژتون باقی‌مانده: {tokens}", uid, wait.message_id, parse_mode="Markdown")
        except Exception as e:
            bot.edit_message_text(f"❌ خطا: {e}", uid, wait.message_id)

    elif action == "🔍 بررسی صحت خبر":
        wait = bot.send_message(uid, f"⏳ در حال جستجو و بررسی... (💎 {tokens} ژتون)")
        try:
            kw = model.generate_content(f"۳ کلمه کلیدی انگلیسی از این خبر، فقط با کاما:\n{news}").text.strip()
            results = ""
            try:
                with DDGS() as ddgs:
                    for r in list(ddgs.text(kw, max_results=5)):
                        results += f"- {r.get('title','')}: {r.get('body','')[:200]}\n"
            except:
                results = "نتیجه‌ای یافت نشد"
            fact = model.generate_content(
                f"صحت این خبر را بررسی کن:\n{news}\n\nنتایج جستجو:\n{results}\n\n"
                f"فرمت: حکم، درصد اطمینان، دلایل"
            )
            bot.edit_message_text(f"🔍 *بررسی صحت:*\n\n{fact.text}\n\n💎 ژتون باقی‌مانده: {tokens}", uid, wait.message_id, parse_mode="Markdown")
        except Exception as e:
            bot.edit_message_text(f"❌ خطا: {e}", uid, wait.message_id)

# ─── Callbacks ────────────────────────────────
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid = call.message.chat.id
    data = load_data()

    # ─── خرید ژتون ───────────────────────────
    if call.data == "buy_tokens":
        card = data.get("card", "تنظیم نشده")
        data.setdefault("pending_payments", {})[str(call.from_user.id)] = "waiting_receipt"
        save_data(data)
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.from_user.id,
            f"💳 *خرید ۱۰۰ ژتون*\n\n"
            f"مبلغ: *۵۰,۰۰۰ تومان*\n"
            f"شماره کارت:\n`{card}`\n\n"
            f"بعد از واریز، **فیش پرداخت** رو اینجا بفرست 👇",
            parse_mode="Markdown"
        )
        return

    # ─── ژتون روزانه ─────────────────────────
    if call.data == "daily_tokens":
        bot.answer_callback_query(call.id)
        gave, tokens = give_daily_tokens(call.from_user.id)
        if gave:
            bot.send_message(call.from_user.id, f"🎁 ۸ ژتون روزانه دریافت کردی!\n💎 ژتون‌های شما: {tokens}", reply_markup=main_menu())
        else:
            next_daily = time_until_daily(call.from_user.id)
            bot.send_message(call.from_user.id, f"⏰ هنوز ۲۴ ساعت نشده!\n{next_daily} دیگه ژتون روزانه میگیری.", reply_markup=main_menu())
        return

    # ─── ادمین: تایید پرداخت ─────────────────
    if call.data.startswith("pay_approve_"):
        target = call.data.replace("pay_approve_", "")
        data.setdefault("users", {}).setdefault(target, {})
        data["users"][target]["tokens"] = data["users"][target].get("tokens", 0) + 100
        data.setdefault("pending_payments", {})[target] = "done"
        save_data(data)
        bot.answer_callback_query(call.id, "✅ تایید شد")
        bot.edit_message_reply_markup(uid, call.message.message_id, reply_markup=None)
        bot.send_message(uid, f"✅ پرداخت کاربر {target} تایید شد. ۱۰۰ ژتون اضافه شد.")
        bot.send_message(int(target), "✅ *پرداخت تایید شد!*\n\n💎 ۱۰۰ ژتون به حسابت اضافه شد.\nحالا می‌تونی از ربات استفاده کنی!", parse_mode="Markdown", reply_markup=main_menu())
        return

    # ─── ادمین: رد پرداخت ────────────────────
    if call.data.startswith("pay_reject_"):
        target = call.data.replace("pay_reject_", "")
        data.setdefault("pending_payments", {})[target] = "waiting_receipt"
        save_data(data)
        bot.answer_callback_query(call.id, "❌ رد شد")
        bot.edit_message_reply_markup(uid, call.message.message_id, reply_markup=None)
        bot.send_message(uid, f"❌ پرداخت کاربر {target} رد شد.")
        bot.send_message(int(target), "❌ فیش پرداخت تایید نشد.\n\nلطفاً فیش معتبر ارسال کن.")
        return

    # ─── ادمین: تغییر کارت ───────────────────
    if call.data == "admin_set_card":
        data["_admin_awaiting_card"] = True
        save_data(data)
        bot.answer_callback_query(call.id)
        bot.send_message(ADMIN_ID, "💳 شماره کارت جدید رو بفرست:")
        return

    # ─── ادمین: آمار ─────────────────────────
    if call.data == "admin_stats":
        bot.answer_callback_query(call.id)
        users = data.get("users", {})
        total = len(users)
        text = f"👥 *آمار کاربران:*\n\nتعداد کل: {total}\n\n"
        for uid_s, u in list(users.items())[-10:]:
            text += f"👤 {u.get('name','؟')} | 💎 {u.get('tokens',0)} ژتون\n"
        bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
        return

# ─── اجرا ────────────────────────────────────
print("📰 ربات خبر MH با سیستم ژتون شروع شد...")
bot.infinity_polling()


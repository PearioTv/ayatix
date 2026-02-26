#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت القرآن الكريم - Quran Telegram Bot
Full-featured Islamic Telegram Bot
"""

import os
import json
import random
import logging
import asyncio
from pathlib import Path
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAudio
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ChatMemberHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ─────────────────────────────────────────────
#   إعدادات
# ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "ضع_توكن_البوت_هنا")
BASE_DIR  = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"
USERS_FILE = BASE_DIR / "users.json"

# ─────────────────────────────────────────────
#   تحميل ملفات JSON
# ─────────────────────────────────────────────
def load_json(filename: str):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

ADHKAR_DATA      = load_json("adhkar.json")
NAMES_DATA       = load_json("Names_Of_Allah.json")
HISN_DATA        = load_json("hisn_almuslim.json")
PHOTOS_DATA      = load_json("Photo_Json.json")
VIDEOS_DATA      = load_json("Video_json.json")
LECTURES_DATA    = load_json("Lectures.json")
QURAN_BROADCAST  = load_json("Quran.json")
HISN_KEYS        = list(HISN_DATA.keys())

# ─────────────────────────────────────────────
#   إدارة المستخدمين
# ─────────────────────────────────────────────
def load_users() -> dict:
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_users(users: dict):
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")

def save_user(users: dict, uid: int, username, first_name, chat_type: str):
    key = str(uid)
    if key not in users:
        users[key] = {
            "id": uid, "username": username,
            "first_name": first_name, "type": chat_type,
            "broadcast": True, "message_id": None
        }
    else:
        users[key]["username"]   = username
        users[key]["first_name"] = first_name
    save_users(users)

async def safe_delete(context, chat_id, message_id):
    if message_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except (BadRequest, TelegramError):
            pass

# ─────────────────────────────────────────────
#   قائمة السور
# ─────────────────────────────────────────────
SURAHS = [
    "الفاتحة","البقرة","آل عمران","النساء","المائدة","الأنعام","الأعراف","الأنفال","التوبة","يونس",
    "هود","يوسف","الرعد","إبراهيم","الحجر","النحل","الإسراء","الكهف","مريم","طه",
    "الأنبياء","الحج","المؤمنون","النور","الفرقان","الشعراء","النمل","القصص","العنكبوت","الروم",
    "لقمان","السجدة","الأحزاب","سبأ","فاطر","يس","الصافات","ص","الزمر","غافر",
    "فصلت","الشورى","الزخرف","الدخان","الجاثية","الأحقاف","محمد","الفتح","الحجرات","ق",
    "الذاريات","الطور","النجم","القمر","الرحمن","الواقعة","الحديد","المجادلة","الحشر","الممتحنة",
    "الصف","الجمعة","المنافقون","التغابن","الطلاق","التحريم","الملك","القلم","الحاقة","المعارج",
    "نوح","الجن","المزمل","المدثر","القيامة","الإنسان","المرسلات","النبأ","النازعات","عبس",
    "التكوير","الانفطار","المطففين","الانشقاق","البروج","الطارق","الأعلى","الغاشية","الفجر","البلد",
    "الشمس","الليل","الضحى","الشرح","التين","العلق","القدر","البينة","الزلزلة","العاديات",
    "القارعة","التكاثر","العصر","الهمزة","الفيل","قريش","الماعون","الكوثر","الكافرون","النصر",
    "المسد","الإخلاص","الفلق","الناس"
]

# ─────────────────────────────────────────────
#   القراء وروابطهم
# ─────────────────────────────────────────────
RECITERS = {
    "idris":   {"name": "إدريس أبكر",         "base": "http://server6.mp3quran.net/abkr/"},
    "maher":   {"name": "ماهر المعيقلي",       "base": "http://server12.mp3quran.net/maher/"},
    "badr":    {"name": "بدر التركي",          "base": "http://server10.mp3quran.net/bader/Rewayat-Hafs-A-n-Assem/"},
    "ali":     {"name": "علي جابر",            "base": "http://server11.mp3quran.net/a_jbr/"},
    "sudais":  {"name": "عبدالرحمن السديس",    "base": "http://server11.mp3quran.net/sds/"},
    "khalid":  {"name": "خالد الجليل",         "base": "http://server10.mp3quran.net/jleel/"},
    "bandar":  {"name": "بندر بيليه",          "base": "http://server6.mp3quran.net/balilah/"},
    "ayoub":   {"name": "محمد أيوب",           "base": "http://server8.mp3quran.net/ayyub/"},
    "suwailem":{"name": "أحمد السويلم",        "base": "http://server14.mp3quran.net/swlim/Rewayat-Hafs-A-n-Assem/"},
    "musa":    {"name": "موسى بلال",           "base": "http://server11.mp3quran.net/bilal/"},
}

def surah_url(reciter_key: str, num: int) -> str:
    base = RECITERS[reciter_key]["base"]
    return f"{base}{num:03d}.mp3"

# ─────────────────────────────────────────────
#   بناء القوائم (Keyboards)
# ─────────────────────────────────────────────
def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("قرآن كريم 📖", callback_data="quran"),
         InlineKeyboardButton("حصن المسلم 🏰", callback_data="hisn")],
        [InlineKeyboardButton("أذكار 📿", callback_data="adhkar"),
         InlineKeyboardButton("بطاقات القرآن 🎴", callback_data="albitaqat")],
        [InlineKeyboardButton("فيديو قرآن 🎥", callback_data="video"),
         InlineKeyboardButton("صور إسلامية 🖼️", callback_data="photo")],
        [InlineKeyboardButton("محاضرات 🌾", callback_data="lectures"),
         InlineKeyboardButton("أسماء الله الحسنى ✨", callback_data="names")],
    ])

def back_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main")]])

def surah_page_keyboard(reciter_key: str, page: int) -> InlineKeyboardMarkup:
    """بناء صفحة السور (9 سور في الصفحة)"""
    per_page = 9
    start = page * per_page
    end   = min(start + per_page, 114)
    rows  = []

    # زر رجوع للأعلى
    if page == 0:
        rows.append([InlineKeyboardButton("⬆️ رجوع للقراء", callback_data="quran")])
    else:
        rows.append([InlineKeyboardButton("⬆️ السابق", callback_data=f"surah_pg|{reciter_key}|{page-1}")])

    # السور (3 في كل صف)
    row = []
    for i in range(start, end):
        row.append(InlineKeyboardButton(SURAHS[i], callback_data=f"play|{reciter_key}|{i+1}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    # زر التالي
    if end < 114:
        rows.append([InlineKeyboardButton("⬇️ التالي", callback_data=f"surah_pg|{reciter_key}|{page+1}")])
    else:
        rows.append([InlineKeyboardButton("🔙 رجوع للقراء", callback_data="quran")])

    return InlineKeyboardMarkup(rows)

def hisn_page_keyboard(page: int) -> InlineKeyboardMarkup:
    per_page = 8
    start = page * per_page
    end   = min(start + per_page, len(HISN_KEYS))
    rows  = []

    if page == 0:
        rows.append([InlineKeyboardButton("⬆️ القائمة الرئيسية", callback_data="main")])
    else:
        rows.append([InlineKeyboardButton("⬆️ السابق", callback_data=f"hisn_pg|{page-1}")])

    for i in range(start, end):
        rows.append([InlineKeyboardButton(HISN_KEYS[i], callback_data=f"hisn_item|{i}")])

    if end < len(HISN_KEYS):
        rows.append([InlineKeyboardButton("⬇️ التالي", callback_data=f"hisn_pg|{page+1}")])
    else:
        rows.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main")])

    return InlineKeyboardMarkup(rows)

def albitaqat_page_keyboard(page: int) -> InlineKeyboardMarkup:
    per_page = 9
    start = page * per_page
    end   = min(start + per_page, 114)
    rows  = []

    if page == 0:
        rows.append([InlineKeyboardButton("⬆️ القائمة الرئيسية", callback_data="main")])
    else:
        rows.append([InlineKeyboardButton("⬆️ السابق", callback_data=f"bitaqat_pg|{page-1}")])

    row = []
    for i in range(start, end):
        row.append(InlineKeyboardButton(SURAHS[i], callback_data=f"bitaqat|{i+1}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    if end < 114:
        rows.append([InlineKeyboardButton("⬇️ التالي", callback_data=f"bitaqat_pg|{page+1}")])
    else:
        rows.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main")])

    return InlineKeyboardMarkup(rows)

# ─────────────────────────────────────────────
#   رسالة الترحيب
# ─────────────────────────────────────────────
def welcome_text(name: str, users: dict, bot_name: str) -> str:
    vals = list(users.values())
    private_c  = sum(1 for u in vals if u.get("type") == "private")
    group_c    = sum(1 for u in vals if u.get("type") in ("supergroup", "group"))
    channel_c  = sum(1 for u in vals if u.get("type") == "channel")

    return (
        f"مرحباً بك {name} في بوت {bot_name} 👋\n\n"
        "✨ يقدم هذا البوت خدمات إسلامية متكاملة:\n\n"
        "📖 القرآن الكريم — بأصوات 10 قراء مشهورين\n"
        "📿 الأذكار — صباح / مساء / نوم / وضوء...\n"
        "🏰 حصن المسلم — 133 باباً من الأدعية\n"
        "🎴 بطاقات القرآن — لكل سور القرآن (صورة + صوت)\n"
        "✨ أسماء الله الحسنى — مع المعنى\n"
        "🎥 فيديوهات قرآنية عشوائية\n"
        "🖼️ صور إسلامية عشوائية\n"
        "🌾 محاضرات ودروس دينية\n\n"
        "📊 إحصائيات:\n"
        f"  👤 محادثات: {private_c}\n"
        f"  👥 مجموعات: {group_c}\n"
        f"  📢 قنوات: {channel_c}\n\n"
        "⬇️ اختر من القائمة:"
    )

# ─────────────────────────────────────────────
#   /start
# ─────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    uid  = chat.id
    name = chat.first_name or chat.title or f"@{chat.username}" or str(uid)

    users = load_users()
    save_user(users, uid, chat.username, name, chat.type)

    # حذف الرسالة القديمة
    old_mid = users.get(str(uid), {}).get("message_id")
    if old_mid:
        await safe_delete(context, uid, old_mid)

    bot_name = context.bot.first_name or "بوت القرآن"
    text = welcome_text(name, users, bot_name)
    msg = await update.message.reply_text(text, reply_markup=main_keyboard())

    users[str(uid)]["message_id"] = msg.message_id
    save_users(users)

# ─────────────────────────────────────────────
#   Callback handler رئيسي
# ─────────────────────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    chat = update.effective_chat
    uid  = chat.id
    users = load_users()

    async def edit_or_send(text, keyboard, parse_mode=None):
        """تحديث الرسالة الحالية أو إرسال جديدة"""
        try:
            kwargs = {"reply_markup": keyboard}
            if parse_mode:
                kwargs["parse_mode"] = parse_mode
            msg = await query.edit_message_text(text, **kwargs)
            users[str(uid)]["message_id"] = msg.message_id
            save_users(users)
        except BadRequest:
            msg = await context.bot.send_message(uid, text, reply_markup=keyboard, parse_mode=parse_mode)
            users.setdefault(str(uid), {})["message_id"] = msg.message_id
            save_users(users)

    # ────── القائمة الرئيسية ──────
    if data == "main":
        bot_name = context.bot.first_name or "بوت القرآن"
        name = chat.first_name or chat.title or str(uid)
        text = welcome_text(name, users, bot_name)
        await edit_or_send(text, main_keyboard())

    # ────── القرآن الكريم ──────
    elif data == "quran":
        text = "🎙️ اختر القارئ الكريم:\n\n"
        for key, r in RECITERS.items():
            text += f"• {r['name']}\n"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("إدريس أبكر", callback_data="surah_pg|idris|0"),
             InlineKeyboardButton("ماهر المعيقلي", callback_data="surah_pg|maher|0")],
            [InlineKeyboardButton("بدر التركي", callback_data="surah_pg|badr|0"),
             InlineKeyboardButton("علي جابر", callback_data="surah_pg|ali|0")],
            [InlineKeyboardButton("عبدالرحمن السديس", callback_data="surah_pg|sudais|0"),
             InlineKeyboardButton("خالد الجليل", callback_data="surah_pg|khalid|0")],
            [InlineKeyboardButton("بندر بيليه", callback_data="surah_pg|bandar|0"),
             InlineKeyboardButton("محمد أيوب", callback_data="surah_pg|ayoub|0")],
            [InlineKeyboardButton("أحمد السويلم", callback_data="surah_pg|suwailem|0"),
             InlineKeyboardButton("موسى بلال", callback_data="surah_pg|musa|0")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="main")],
        ])
        await edit_or_send(text, keyboard)

    # ────── صفحة السور ──────
    elif data.startswith("surah_pg|"):
        _, rec_key, page = data.split("|")
        page = int(page)
        rec  = RECITERS.get(rec_key, {})
        text = f"🎙️ القارئ: {rec.get('name', '')}\n\nاختر السورة:"
        await edit_or_send(text, surah_page_keyboard(rec_key, page))

    # ────── تشغيل سورة ──────
    elif data.startswith("play|"):
        _, rec_key, num = data.split("|")
        num = int(num)
        rec = RECITERS.get(rec_key, {})
        url = surah_url(rec_key, num)
        caption = f"📖 سورة: {SURAHS[num-1]}\n🎙️ القارئ: {rec.get('name', '')}"
        try:
            await context.bot.send_audio(uid, audio=url, caption=caption)
        except TelegramError:
            await context.bot.send_message(uid, f"⚠️ تعذّر إرسال الملف الصوتي لسورة {SURAHS[num-1]}")

    # ────── الأذكار ──────
    elif data == "adhkar":
        text = "📿 قائمة الأذكار\n\nاختر نوع الذكر:"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("أذكار الصباح ☀️", callback_data="adhkar|sabah"),
             InlineKeyboardButton("أذكار المساء 🌑", callback_data="adhkar|masa")],
            [InlineKeyboardButton("أذكار النوم 😴", callback_data="adhkar|nawm"),
             InlineKeyboardButton("أذكار عشوائية 🔄", callback_data="adhkar|random")],
            [InlineKeyboardButton("أدعية نبوية 🤲", callback_data="adhkar|duaa"),
             InlineKeyboardButton("أذكار الآذان 📢", callback_data="adhkar|azan")],
            [InlineKeyboardButton("أذكار المسجد 🕌", callback_data="adhkar|masjid"),
             InlineKeyboardButton("أذكار الوضوء 💦", callback_data="adhkar|wudu")],
            [InlineKeyboardButton("دخول وخروج المنزل 🏠", callback_data="adhkar|manzil"),
             InlineKeyboardButton("أذكار الخلاء 🚻", callback_data="adhkar|khalaa")],
            [InlineKeyboardButton("أذكار الطعام 🥣", callback_data="adhkar|taaam"),
             InlineKeyboardButton("دعاء ختم القرآن 📖", callback_data="adhkar|khatm")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="main")],
        ])
        await edit_or_send(text, keyboard)

    elif data.startswith("adhkar|"):
        kind = data.split("|")[1]
        back_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 ذكر عشوائي", callback_data="adhkar|random"),
            InlineKeyboardButton("🔙 رجوع للأذكار", callback_data="adhkar")
        ]])
        text = ADHKAR_TEXTS.get(kind, "")
        if kind == "random":
            item = random.choice(ADHKAR_DATA)
            text  = f"📿 {item.get('category','')}\n\n"
            text += item.get("zekr", "")
            if item.get("description"): text += f"\n\n💡 {item['description']}"
            if item.get("count"):       text += f"\n\n🔢 عدد التكرار: {item['count']}"
            if item.get("reference"):   text += f"\n\n📚 {item['reference']}"
        await edit_or_send(text or "لا يوجد محتوى", back_kb)

    # ────── حصن المسلم ──────
    elif data == "hisn":
        text = (
            "🏰 حصن المسلم\n\n"
            "كتاب أدعية تأليف: سعيد بن علي بن وهف القحطاني\n"
            f"يحتوي على {len(HISN_KEYS)} باباً من الأذكار النبوية\n\n"
            "اختر الباب:"
        )
        await edit_or_send(text, hisn_page_keyboard(0))

    elif data.startswith("hisn_pg|"):
        page = int(data.split("|")[1])
        await edit_or_send("🏰 حصن المسلم — اختر الباب:", hisn_page_keyboard(page))

    elif data.startswith("hisn_item|"):
        idx = int(data.split("|")[1])
        key = HISN_KEYS[idx]
        item = HISN_DATA[key]
        texts = item.get("text", [])
        footnotes = item.get("footnote", [])
        msg_text = f"🏰 {key}\n\n"
        msg_text += "\n\n".join(texts)
        if footnotes:
            msg_text += "\n\n──────────\n" + "\n".join(footnotes)
        back_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 رجوع لحصن المسلم", callback_data=f"hisn_pg|{idx // 8}")
        ]])
        # قد تكون الرسالة طويلة جداً، نرسل رسالة جديدة
        try:
            await query.edit_message_text(msg_text[:4096], reply_markup=back_kb)
        except Exception:
            await context.bot.send_message(uid, msg_text[:4096], reply_markup=back_kb)

    # ────── بطاقات القرآن ──────
    elif data == "albitaqat":
        text = (
            "🎴 بطاقات القرآن الكريم\n\n"
            "لكل سورة بطاقة تعريفية تشمل:\n"
            "• عدد الآيات\n• معنى الاسم\n• سبب التسمية\n"
            "• المقصد العام\n• فضل السورة\n\n"
            "⚠️ اضغط على اسم السورة لإرسال الصورة والصوت:"
        )
        await edit_or_send(text, albitaqat_page_keyboard(0))

    elif data.startswith("bitaqat_pg|"):
        page = int(data.split("|")[1])
        await edit_or_send("🎴 اختر السورة:", albitaqat_page_keyboard(page))

    elif data.startswith("bitaqat|"):
        num = int(data.split("|")[1])
        img_url   = f"http://bot.altaqwaa.org/media/albitaqat/images/{num:03d}.jpg"
        audio_url = f"http://bot.altaqwaa.org/media/albitaqat/mp3/{num:03d}.mp3"
        caption   = f"🎴 بطاقة سورة: {SURAHS[num-1]} 📖"
        try:
            await context.bot.send_photo(uid, photo=img_url)
            await context.bot.send_audio(uid, audio=audio_url, caption=caption)
        except TelegramError:
            await context.bot.send_message(uid, f"⚠️ تعذّر إرسال بطاقة سورة {SURAHS[num-1]}")

    # ────── أسماء الله الحسنى ──────
    elif data == "names":
        item = random.choice(NAMES_DATA)
        text  = f"✨ <b>{item['name']}</b>\n\n"
        text += item.get("text", "")
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 اسم آخر", callback_data="names"),
            InlineKeyboardButton("🔙 رجوع", callback_data="main")
        ]])
        await edit_or_send(text, kb, parse_mode=ParseMode.HTML)

    # ────── الصور ──────
    elif data == "photo":
        url = random.choice(PHOTOS_DATA)
        kb  = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 صورة أخرى", callback_data="photo"),
            InlineKeyboardButton("🔙 رجوع", callback_data="main")
        ]])
        try:
            old_mid = users.get(str(uid), {}).get("message_id")
            await safe_delete(context, uid, old_mid)
            msg = await context.bot.send_photo(uid, photo=url, reply_markup=kb)
            users[str(uid)]["message_id"] = msg.message_id
            save_users(users)
        except TelegramError:
            await edit_or_send("⚠️ تعذّر إرسال الصورة", back_main())

    # ────── الفيديو ──────
    elif data == "video":
        url = random.choice(VIDEOS_DATA)
        kb  = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 فيديو آخر", callback_data="video"),
            InlineKeyboardButton("🔙 رجوع", callback_data="main")
        ]])
        try:
            old_mid = users.get(str(uid), {}).get("message_id")
            await safe_delete(context, uid, old_mid)
            msg = await context.bot.send_video(uid, video=url, reply_markup=kb)
            users[str(uid)]["message_id"] = msg.message_id
            save_users(users)
        except TelegramError:
            await edit_or_send("⚠️ تعذّر إرسال الفيديو", back_main())

    # ────── المحاضرات ──────
    elif data == "lectures":
        item = random.choice(LECTURES_DATA)
        caption  = f"🌾 <b>{item['Lectures']}</b>"
        if item.get("Author"):
            caption += f"\n\n🎙️ الشيخ: {item['Author']}"
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 محاضرة أخرى", callback_data="lectures"),
            InlineKeyboardButton("🔙 رجوع", callback_data="main")
        ]])
        try:
            old_mid = users.get(str(uid), {}).get("message_id")
            await safe_delete(context, uid, old_mid)
            msg = await context.bot.send_video(
                uid, video=item["FilePath"],
                caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb
            )
            users[str(uid)]["message_id"] = msg.message_id
            save_users(users)
        except TelegramError:
            await edit_or_send("⚠️ تعذّر إرسال المحاضرة", back_main())

# ─────────────────────────────────────────────
#   on message (تفعيل / تعطيل)
# ─────────────────────────────────────────────
async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    uid  = chat.id
    text = update.message.text or ""
    name = chat.first_name or chat.title or str(uid)

    users = load_users()
    save_user(users, uid, chat.username, name, chat.type)

    if text == "تعطيل":
        if users[str(uid)].get("broadcast") is not False:
            users[str(uid)]["broadcast"] = False
            save_users(users)
            await update.message.reply_text("✅ تم تعطيل الإرسال التلقائي\nلإعادة التفعيل أرسل: تفعيل")
        else:
            await update.message.reply_text("ℹ️ الخدمة معطلة بالفعل!")
    elif text == "تفعيل":
        if users[str(uid)].get("broadcast") is False:
            users[str(uid)]["broadcast"] = True
            save_users(users)
            await update.message.reply_text("✅ تم تفعيل الإرسال التلقائي")
        else:
            await update.message.reply_text("ℹ️ الخدمة مفعلة بالفعل!")

# ─────────────────────────────────────────────
#   انضمام/مغادرة للمجموعات
# ─────────────────────────────────────────────
async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        members = update.message.new_chat_members
        bot_id  = context.bot.id
        admins  = await context.bot.get_chat_administrators(update.effective_chat.id)
        bot_admin = next((a for a in admins if a.user.id == bot_id), None)
        if not bot_admin or not bot_admin.can_delete_messages:
            return
        for member in members:
            if not member.is_bot:
                uname = f"@{member.username}" if member.username else member.first_name
                msg = await context.bot.send_message(
                    update.effective_chat.id,
                    f"مرحباً بك {uname} 👋\nفي مجموعة {update.effective_chat.title}"
                )
                await update.message.delete()
                asyncio.get_event_loop().call_later(
                    20, asyncio.create_task,
                    context.bot.delete_message(update.effective_chat.id, msg.message_id)
                )
    except Exception:
        pass

async def on_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.left_chat_member.is_bot:
            return
        bot_id = context.bot.id
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        bot_admin = next((a for a in admins if a.user.id == bot_id), None)
        if bot_admin and bot_admin.can_delete_messages:
            await update.message.delete()
    except Exception:
        pass

async def on_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.my_chat_member
    chat   = member.chat
    uid    = chat.id
    status = member.new_chat_member.status
    users  = load_users()

    if status in ("member", "administrator"):
        name = chat.first_name or chat.title or str(uid)
        save_user(users, uid, chat.username, name, chat.type)
        try:
            can_post = getattr(member.new_chat_member, "can_post_messages", None)
            if can_post is True or chat.type == "private":
                uname = f"@{chat.username}" if chat.username else name
                await context.bot.send_message(
                    uid,
                    f"مرحبا {uname} 🎉\nتم تفعيل خدمة الإرسال التلقائي\nلإيقافها أرسل: تعطيل"
                )
        except Exception:
            pass
    elif status in ("left", "kicked"):
        users.pop(str(uid), None)
        save_users(users)

# ─────────────────────────────────────────────
#   الإرسال التلقائي (scheduler)
# ─────────────────────────────────────────────
async def broadcast_to_all(app: Application, sender):
    users = load_users()
    me    = await app.bot.get_me()
    for uid_str, info in users.items():
        if info.get("broadcast") is False:
            continue
        uid = int(uid_str)
        try:
            if info["type"] == "private":
                await sender(app.bot, uid)
            elif info["type"] in ("supergroup", "group"):
                admins = await app.bot.get_chat_administrators(uid)
                if any(a.user.id == me.id and a.status == "administrator" for a in admins):
                    await sender(app.bot, uid)
            elif info["type"] == "channel":
                admins = await app.bot.get_chat_administrators(uid)
                if any(a.user.id == me.id and getattr(a, "can_post_messages", False) for a in admins):
                    await sender(app.bot, uid)
        except Exception:
            pass
        await asyncio.sleep(0.05)  # تجنب flood

async def send_adhkar(bot, uid):
    item = random.choice(ADHKAR_DATA)
    text = f"📿 {item.get('category','')}\n\n{item.get('zekr','')}"
    if item.get("count"):  text += f"\n\n🔢 {item['count']}"
    await bot.send_message(uid, text)

async def send_video_broadcast(bot, uid):
    url = random.choice(VIDEOS_DATA)
    await bot.send_video(uid, video=url)

async def send_photo_broadcast(bot, uid):
    url = random.choice(PHOTOS_DATA)
    await bot.send_photo(uid, photo=url)

async def send_quran_broadcast(bot, uid):
    item    = random.choice(QURAN_BROADCAST)
    caption = f"📖 سورة: {item['Surah']}\n🎙️ {item['Author']}"
    await bot.send_audio(uid, audio=item["FilePath"], caption=caption)

async def send_lectures_broadcast(bot, uid):
    item    = random.choice(LECTURES_DATA)
    caption = f"🌾 {item['Lectures']}"
    if item.get("Author"): caption += f"\n🎙️ {item['Author']}"
    await bot.send_video(uid, video=item["FilePath"], caption=caption)

async def send_morning_adhkar(bot, uid):
    await bot.send_audio(
        uid,
        audio="http://bot.altaqwaa.org/media/adhkar_mp3/Adhkar_sbh.mp3",
        caption="☀️ أذكار الصباح\n🎙️ بصوت إدريس أبكر"
    )

async def send_evening_adhkar(bot, uid):
    await bot.send_audio(
        uid,
        audio="http://bot.altaqwaa.org/media/adhkar_mp3/Adhkar_msa.mp3",
        caption="🌑 أذكار المساء\n🎙️ بصوت فيصل بن جذيان"
    )

async def send_hisn_broadcast(bot, uid):
    key  = random.choice(HISN_KEYS)
    item = HISN_DATA[key]
    text = f"🏰 {key}\n\n" + "\n\n".join(item.get("text", []))
    await bot.send_message(uid, text[:4096])

def setup_scheduler(app: Application) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Riyadh")

    scheduler.add_job(lambda: asyncio.create_task(broadcast_to_all(app, send_adhkar)),
                      "cron", hour=15, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(broadcast_to_all(app, send_video_broadcast)),
                      "cron", hour=8, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(broadcast_to_all(app, send_photo_broadcast)),
                      "cron", hour=12, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(broadcast_to_all(app, send_quran_broadcast)),
                      "cron", hour=21, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(broadcast_to_all(app, send_lectures_broadcast)),
                      "cron", hour=23, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(broadcast_to_all(app, send_morning_adhkar)),
                      "cron", hour=6, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(broadcast_to_all(app, send_evening_adhkar)),
                      "cron", hour=18, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(broadcast_to_all(app, send_hisn_broadcast)),
                      "cron", hour=2, minute=0)

    scheduler.start()
    logger.info("✅ Scheduler started")
    return scheduler

# ─────────────────────────────────────────────
#   نصوص الأذكار الثابتة
# ─────────────────────────────────────────────
ADHKAR_TEXTS = {
    "sabah": """☀️ أذكار الصباح

▪ الفاتحة | مرة
▪ آية الكرسى | مرة
▪ الإخلاص والمعوذتين | 3 مرات

❀ أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ... | مرة

❀ اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ، وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ... | مرة

❀ رَضِيتُ بِاللَّهِ رَبًّا وَبِالْإِسْلَامِ دِينًا وَبِمُحَمَّدٍ ﷺ نَبِيًّا | 3 مرات

❀ حَسْبِيَ اللَّهُ لَا إِلَهَ إِلَّا هُوَ عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ | 7 مرات

❀ بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ | 3 مرات

❀ اللَّهُمَّ عَافِنِي فِي بَدَنِي، اللَّهُمَّ عَافِنِي فِي سَمْعِي، اللَّهُمَّ عَافِنِي فِي بَصَرِي | 3 مرات

❀ سُبْحَانَ اللَّهِ وَبِحَمْدِهِ عَدَدَ خَلْقِهِ وَرِضَا نَفْسِهِ وَزِنَةَ عَرْشِهِ وَمِدَادَ كَلِمَاتِهِ | 3 مرات

❀ اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ وَالْعَجْزِ وَالْكَسَلِ وَالْجُبْنِ وَالْبُخْلِ وَضَلَعِ الدَّيْنِ وَغَلَبَةِ الرِّجَالِ | 3 مرات

❀ اللَّهُمَّ صَلِّ وَسَلِّمْ وَبَارِكْ عَلَى نَبِيِّنَا مُحَمَّدٍ | 10 مرات""",

    "masa": """🌑 أذكار المساء

▪ الفاتحة | مرة
▪ آية الكرسى | مرة
▪ الإخلاص والمعوذتين | 3 مرات

❀ أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ... | مرة

❀ اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ... | مرة

❀ رَضِيتُ بِاللَّهِ رَبًّا وَبِالْإِسْلَامِ دِينًا وَبِمُحَمَّدٍ ﷺ نَبِيًّا | 3 مرات

❀ حَسْبِيَ اللَّهُ لَا إِلَهَ إِلَّا هُوَ عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ | 7 مرات

❀ بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ | 3 مرات

❀ اللَّهُمَّ صَلِّ وَسَلِّمْ وَبَارِكْ عَلَى نَبِيِّنَا مُحَمَّدٍ | 10 مرات""",

    "nawm": """😴 أذكار النوم

❀ بِاسْمِكَ رَبِّي وَضَعْتُ جَنْبِي وَبِكَ أَرْفَعُهُ، فَإِنْ أَمْسَكْتَ نَفْسِي فَارْحَمْهَا وَإِنْ أَرْسَلْتَهَا فَاحْفَظْهَا | مرة

❀ اللَّهُمَّ قِنِي عَذَابَكَ يَوْمَ تَبْعَثُ عِبَادَكَ | 3 مرات

❀ بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا | مرة

❀ اللَّهُمَّ إِنَّكَ خَلَقْتَ نَفْسِي وَأَنْتَ تَوَفَّاهَا، لَكَ مَمَاتُهَا وَمَحْيَاهَا | مرة

❀ اللَّهُمَّ أَسْلَمْتُ نَفْسِي إِلَيْكَ وَفَوَّضْتُ أَمْرِي إِلَيْكَ وَوَجَّهْتُ وَجْهِي إِلَيْكَ... | مرة

❀ سُبْحَانَ اللَّهِ | 33 مرة
❀ الْحَمْدُ لِلَّهِ  | 33 مرة
❀ اللَّهُ أَكْبَرُ  | 34 مرة

▪ قراءة: آية الكرسي + سورة الكافرون + المعوذتين""",

    "duaa": """🤲 أدعية نبوية

▪ اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ، وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ، أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ...

▪ اللَّهُمَّ إِنِّي ظَلَمْتُ نَفْسِي ظُلْمًا كَثِيرًا وَلَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ فَاغْفِرْ لِي مَغْفِرَةً مِنْ عِنْدِكَ وَارْحَمْنِي إِنَّكَ أَنْتَ الْغَفُورُ الرَّحِيمُ

▪ اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ وَالْعَجْزِ وَالْكَسَلِ وَالْجُبْنِ وَالْبُخْلِ وَضَلَعِ الدَّيْنِ وَغَلَبَةِ الرِّجَالِ

▪ اللَّهُمَّ أَصْلِحْ لِي دِينِي الَّذِي هُوَ عِصْمَةُ أَمْرِي، وَأَصْلِحْ لِي دُنْيَايَ الَّتِي فِيهَا مَعَاشِي، وَأَصْلِحْ لِي آخِرَتِي الَّتِي فِيهَا مَعَادِي

▪ اللَّهُمَّ إِنِّي أَسْأَلُكَ الْهُدَى وَالتُّقَى وَالْعَفَافَ وَالْغِنَى

▪ اللَّهُمَّ إِنِّي أَعُوذُ بِرِضَاكَ مِنْ سَخَطِكَ وَبِمُعَافَاتِكَ مِنْ عُقُوبَتِكَ وَأَعُوذُ بِكَ مِنْكَ، لَا أُحْصِي ثَنَاءً عَلَيْكَ أَنْتَ كَمَا أَثْنَيْتَ عَلَى نَفْسِكَ""",

    "azan": """📢 أذكار عند سماع الأذان

▪ يقول مثل ما يقول المؤذن إلا في "حَيَّ عَلَى الصَّلَاةِ وَحَيَّ عَلَى الْفَلَاحِ" فيقول:
"لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ"

▪ بعد الأذان يقول:
اللَّهُمَّ رَبَّ هَذِهِ الدَّعْوَةِ التَّامَّةِ وَالصَّلَاةِ الْقَائِمَةِ آتِ مُحَمَّدًا الْوَسِيلَةَ وَالْفَضِيلَةَ وَابْعَثْهُ مَقَامًا مَحْمُودًا الَّذِي وَعَدْتَهُ

▪ أشْهَدُ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ وَأَنَّ مُحَمَّدًا عَبْدُهُ وَرَسُولُهُ رَضِيتُ بِاللَّهِ رَبًّا وَبِمُحَمَّدٍ رَسُولًا وَبِالْإِسْلَامِ دِينًا

▪ بين الأذان والإقامة: الدعاء لا يُرَدّ""",

    "masjid": """🕌 أذكار المسجد

▪ الذهاب للمسجد:
اللَّهُمَّ اجْعَلْ فِي قَلْبِي نُورًا وَفِي لِسَانِي نُورًا وَفِي سَمْعِي نُورًا وَفِي بَصَرِي نُورًا وَمِنْ فَوْقِي نُورًا وَمِنْ تَحْتِي نُورًا وَعَنْ يَمِينِي نُورًا وَعَنْ شِمَالِي نُورًا وَمِنْ أَمَامِي نُورًا وَمِنْ خَلْفِي نُورًا وَاجْعَلْ لِي نُورًا

▪ دخول المسجد (ابدأ بالرجل اليمنى):
أَعُوذُ بِاللَّهِ الْعَظِيمِ وَبِوَجْهِهِ الْكَرِيمِ وَسُلْطَانِهِ الْقَدِيمِ مِنَ الشَّيْطَانِ الرَّجِيمِ
بِسْمِ اللَّهِ وَالصَّلَاةُ وَالسَّلَامُ عَلَى رَسُولِ اللَّهِ
اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ

▪ الخروج من المسجد (ابدأ بالرجل اليسرى):
بِسْمِ اللَّهِ وَالصَّلَاةُ وَالسَّلَامُ عَلَى رَسُولِ اللَّهِ
اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنْ فَضْلِكَ
اللَّهُمَّ اعْصِمْنِي مِنَ الشَّيْطَانِ الرَّجِيمِ""",

    "wudu": """💦 أذكار الوضوء

▪ قبل الوضوء:
بِسْمِ اللَّهِ

▪ بعد الوضوء:
أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ وَأَشْهَدُ أَنَّ مُحَمَّدًا عَبْدُهُ وَرَسُولُهُ

اللَّهُمَّ اجْعَلْنِي مِنَ التَّوَّابِينَ وَاجْعَلْنِي مِنَ الْمُتَطَهِّرِينَ

سُبْحَانَكَ اللَّهُمَّ وَبِحَمْدِكَ أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا أَنْتَ أَسْتَغْفِرُكَ وَأَتُوبُ إِلَيْكَ""",

    "manzil": """🏠 أذكار دخول وخروج المنزل

▪ دخول المنزل:
بِسْمِ اللَّهِ وَلَجْنَا وَبِسْمِ اللَّهِ خَرَجْنَا وَعَلَى اللَّهِ رَبِّنَا تَوَكَّلْنَا

▪ الخروج من المنزل:
بِسْمِ اللَّهِ تَوَكَّلْتُ عَلَى اللَّهِ وَلَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ

اللَّهُمَّ إِنِّي أَعُوذُ بِكَ أَنْ أَضِلَّ أَوْ أُضَلَّ أَوْ أَزِلَّ أَوْ أُزَلَّ أَوْ أَظْلِمَ أَوْ أُظْلَمَ أَوْ أَجْهَلَ أَوْ يُجْهَلَ عَلَيَّ""",

    "khalaa": """🚻 أذكار دخول الخلاء

▪ عند الدخول:
بِسْمِ اللَّهِ — اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْخُبْثِ وَالْخَبَائِثِ

▪ عند الخروج:
غُفْرَانَكَ""",

    "taaam": """🥣 أذكار الطعام والشراب

▪ قبل الأكل:
بِسْمِ اللَّهِ
(إذا نسي في البداية يقول: بِسْمِ اللَّهِ أَوَّلَهُ وَآخِرَهُ)

▪ عند شرب اللبن:
اللَّهُمَّ بَارِكْ لَنَا فِيهِ وَزِدْنَا مِنْهُ

▪ بعد الطعام:
الْحَمْدُ لِلَّهِ الَّذِي أَطْعَمَنِي هَذَا وَرَزَقَنِيهِ مِنْ غَيْرِ حَوْلٍ مِنِّي وَلَا قُوَّةٍ

الْحَمْدُ لِلَّهِ كَثِيرًا طَيِّبًا مُبَارَكًا فِيهِ غَيْرَ مَكْفِيٍّ وَلَا مُوَدَّعٍ وَلَا مُسْتَغْنًى عَنْهُ رَبَّنَا

▪ دعاء الضيف:
أَفْطَرَ عِنْدَكُمُ الصَّائِمُونَ وَأَكَلَ طَعَامَكُمُ الْأَبْرَارُ وَصَلَّتْ عَلَيْكُمُ الْمَلَائِكَةُ""",

    "khatm": """📖 دعاء ختم القرآن الكريم

اللَّهُمَّ ارْحَمْنِي بِالْقُرْآنِ وَاجْعَلْهُ لِي إِمَامًا وَنُورًا وَهُدًى وَرَحْمَةً

اللَّهُمَّ ذَكِّرْنِي مِنْهُ مَا نَسِيتُ وَعَلِّمْنِي مِنْهُ مَا جَهِلْتُ وَارْزُقْنِي تِلَاوَتَهُ آنَاءَ اللَّيْلِ وَأَطْرَافَ النَّهَارِ وَاجْعَلْهُ لِي حُجَّةً يَا رَبَّ الْعَالَمِينَ

اللَّهُمَّ أَصْلِحْ لِي دِينِي الَّذِي هُوَ عِصْمَةُ أَمْرِي وَأَصْلِحْ لِي دُنْيَايَ الَّتِي فِيهَا مَعَاشِي وَأَصْلِحْ لِي آخِرَتِي الَّتِي فِيهَا مَعَادِي

اللَّهُمَّ اجْعَلْ خَيْرَ عُمْرِي آخِرَهُ وَخَيْرَ عَمَلِي خَوَاتِمَهُ وَخَيْرَ أَيَّامِي يَوْمَ أَلْقَاكَ

رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ

وَصَلَّى اللَّهُ عَلَى سَيِّدِنَا مُحَمَّدٍ وَعَلَى آلِهِ وَصَحْبِهِ وَسَلَّمَ""",
}

# ─────────────────────────────────────────────
#   تشغيل البوت
# ─────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_left_member))
    app.add_handler(ChatMemberHandler(on_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))

    # Scheduler
    setup_scheduler(app)

    logger.info("🚀 Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()

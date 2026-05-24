import sqlite3
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputFile
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =========================
# НАЛАШТУВАННЯ
# =========================

TOKEN = "8716475707:AAE2Nypb2OmVso1As_AcCx_Ku-QnQz_9wp8"
ADMIN_ID = 496493116

# Шлях до фото контактів
CONTACTS_PHOTO = "banner.jpg"

# =========================
# SQLITE БАЗА ДАНИХ
# =========================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    first_name TEXT,
    request_type TEXT,
    message TEXT,
    created_at TEXT
)
""")

conn.commit()

# =========================
# РЕЖИМИ КОРИСТУВАЧІВ
# =========================

user_modes = {}

# =========================
# INLINE МЕНЮ
# =========================

inline_menu = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "💰 Дізнатись ціну",
            callback_data="price"
        )
    ],
    [
        InlineKeyboardButton(
            "🛠 Допомога у підборі",
            callback_data="help"
        )
    ],
    [
        InlineKeyboardButton(
            "📞 Контакти",
            callback_data="contacts"
        )
    ]
])

# =========================
# КНОПКА "НАЗАД"
# =========================

back_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("⬅️ Назад")]
    ],
    resize_keyboard=True
)

# =========================
# ПЕРЕВІРКА РОБОЧОГО ЧАСУ
# =========================

def is_working_time():

    now = datetime.now()

    weekday = now.weekday()
    current_hour = now.hour

    # ПН-ПТ
    if weekday in [0, 1, 2, 3, 4]:

        return 9 <= current_hour < 17

    # СБ
    if weekday == 5:

        return 9 <= current_hour < 14

    # НД
    return False

# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Вітаємо!\n\n"
        "Ми допоможемо Вам:\n"
        "• дізнатись актуальну ціну\n"
        "• підібрати побутову техніку\n\n"
        "👇 Оберіть потрібний пункт меню:",
        reply_markup=inline_menu
    )

# =========================
# ВІДПРАВКА КОНТАКТІВ
# =========================

async def send_contacts(message):

    caption = (
        "🏪 <b>СКЛАД ПОБУТОВОЇ ТЕХНІКИ</b>\n\n"

        "📍 <b>Адреса:</b>\n"
        "м. Вінниця,\n"
        "вул. Академіка Янгеля 4\n\n"

        "🗺 <b>Google Maps:</b>\n"
        "https://maps.app.goo.gl/XvLQ9c2A4RNrvXMz6\n\n"

        "📞 <b>Телефони:</b>\n"
        "• 097-969-33-34\n"
        "• 097-251-49-45\n\n"

        "🕒 <b>Графік роботи:</b>\n"
        "• ПН-ПТ: 09:00 - 17:00\n"
        "• СБ: 09:00 - 14:00\n"
        "• НД: вихідний\n\n"

        "🤝 Завжди раді Вам допомогти!"
    )

    try:

        with open(CONTACTS_PHOTO, "rb") as photo:

            await message.reply_photo(
                photo=photo,
                caption=caption,
                parse_mode="HTML",
                reply_markup=inline_menu
            )

    except FileNotFoundError:

        await message.reply_text(
            caption,
            parse_mode="HTML",
            reply_markup=inline_menu
        )
# =========================
# INLINE КНОПКИ
# =========================

async def inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # =========================
    # ДІЗНАТИСЬ ЦІНУ
    # =========================

    if query.data == "price":

        user_modes[user_id] = "price"

        await query.message.reply_text(
            "💰 Надішліть, будь ласка:\n\n"
            "• модель товару\n"
            "• посилання на сторінку з товаром\n"
            "• фото товару\n\n"
            "Наприклад:\n"
            "Samsung WW60A3120BH/LE",
            reply_markup=back_keyboard
        )

        return

    # =========================
    # ДОПОМОГА У ПІДБОРІ
    # =========================

    if query.data == "help":

        user_modes[user_id] = "help"

        await query.message.reply_text(
            "🛠 Для підбору, будь ласка, вкажіть який саме товар Вас цікавить (холодильник, телвізор, пральна машина)\n"
            "• основні характеристики: бажаний колір, розмір\n"            
            "• орієнтовний бюджет\n"
            "• можете також надіслати фото\n\n"
            "Наприклад:\n"
            "Холодильник, сірий, 2м, NoFrost, 20000-25000грн",
            reply_markup=back_keyboard
        )

        return

    # =========================
    # КОНТАКТИ
    # =========================

    if query.data == "contacts":

        await send_contacts(query.message)

        return

# =========================
# КНОПКА "НАЗАД"
# =========================

async def back_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    user_modes.pop(user_id, None)

    await update.message.reply_text(
        "⬅️ Ви повернулись у головне меню",
        reply_markup=inline_menu
    )

# =========================
# ТЕКСТОВІ ПОВІДОМЛЕННЯ
# =========================

async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user
    text = update.message.text
    user_id = user.id

    print(f"Отримано повідомлення: {text}")

    # Ігноруємо повідомлення адміна
    if user_id == ADMIN_ID:
        return

    mode = user_modes.get(user_id)

    # Якщо режим не вибраний
    if not mode:

        await update.message.reply_text(
            "👇 Будь ласка, оберіть пункт меню:",
            reply_markup=inline_menu
        )

        return

    # Тип заявки
    mode_text = (
        "Запит ціни"
        if mode == "price"
        else "Допомога у підборі"
    )

    # =========================
    # ЗБЕРЕЖЕННЯ В БАЗУ
    # =========================

    cursor.execute("""
    INSERT INTO requests (
        user_id,
        username,
        first_name,
        request_type,
        message,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        user.username,
        user.first_name,
        mode_text,
        text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

    # =========================
    # ВІДПРАВКА АДМІНУ
    # =========================

    admin_message = (
        f"📩 Нова заявка\n\n"
        f"Тип: {mode_text}\n"
        f"Ім'я: {user.first_name}\n"
        f"Username: "
        f"@{user.username if user.username else 'немає'}\n"
        f"ID: {user_id}\n\n"
        f"Повідомлення:\n{text}"
    )

    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_message
    )

    # Запам'ятовуємо користувача
    context.bot_data[msg.message_id] = user_id

    # =========================
    # АВТОВІДПОВІДЬ
    # =========================

    if is_working_time():

        answer_text = (
            "✅ Ваш запит успішно відправлено.\n\n"
            "Менеджер відповість найближчим часом."
        )

    else:

        answer_text = (
            "🌙 Ваш запит успішно отримано.\n\n"
            "📅 Наш графік роботи:\n"
            "• ПН-ПТ: 09:00 - 17:00\n"
            "• СБ: 09:00 - 14:00\n"
            "• НД: вихідний\n\n"
            "Ми обов'язково відповімо Вам "
            "у робочий час 🙌"
        )

    await update.message.reply_text(
        answer_text,
        reply_markup=inline_menu
    )

    # Очищаємо режим
    user_modes.pop(user_id, None)

# =========================
# ФОТО
# =========================

async def photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user
    caption = update.message.caption
    user_id = user.id

    # Ігноруємо фото адміна
    if user_id == ADMIN_ID:
        return

    mode = user_modes.get(user_id)

    # Якщо режим не вибраний
    if not mode:

        await update.message.reply_text(
            "👇 Будь ласка, спочатку оберіть пункт меню:",
            reply_markup=inline_menu
        )

        return

    # Тип заявки
    mode_text = (
        "Запит ціни"
        if mode == "price"
        else "Допомога у підборі"
    )

    # Текст для бази
    message_text = caption if caption else "Фото без опису"

    # =========================
    # ЗБЕРЕЖЕННЯ В БАЗУ
    # =========================

    cursor.execute("""
    INSERT INTO requests (
        user_id,
        username,
        first_name,
        request_type,
        message,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        user.username,
        user.first_name,
        mode_text,
        message_text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

    # =========================
    # ВІДПРАВКА ФОТО АДМІНУ
    # =========================

    photo = update.message.photo[-1].file_id

    admin_caption = (
        f"📷 Нова заявка з фото\n\n"
        f"Тип: {mode_text}\n"
        f"Ім'я: {user.first_name}\n"
        f"Username: "
        f"@{user.username if user.username else 'немає'}\n"
        f"ID: {user_id}\n\n"
        f"Коментар:\n"
        f"{message_text}"
    )

    msg = await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=admin_caption
    )

    # Запам'ятовуємо користувача
    context.bot_data[msg.message_id] = user_id

    # =========================
    # АВТОВІДПОВІДЬ
    # =========================

    if is_working_time():

        answer_text = (
            "✅ Фото успішно відправлено.\n\n"
            "Менеджер відповість найближчим часом."
        )

    else:

        answer_text = (
            "🌙 Фото успішно отримано.\n\n"
            "📅 Наш графік роботи:\n"
            "• ПН-ПТ: 09:00 - 17:00\n"
            "• СБ: 09:00 - 14:00\n"
            "• НД: вихідний\n\n"
            "Ми обов'язково відповімо Вам "
            "у робочий час 🙌"
        )

    await update.message.reply_text(
        answer_text,
        reply_markup=inline_menu
    )

    # Очищаємо режим
    user_modes.pop(user_id, None)

# =========================
# ВІДПОВІДЬ АДМІНА
# =========================

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    # Лише адміну
    if user_id != ADMIN_ID:
        return

    # Має бути reply
    if not update.message.reply_to_message:
        return

    replied_msg_id = update.message.reply_to_message.message_id

    # Отримуємо користувача
    target_user_id = context.bot_data.get(replied_msg_id)

    if not target_user_id:
        return

    # Відправляємо відповідь
    await context.bot.send_message(
        chat_id=target_user_id,
        text=(
            "💬 Відповідь консультанта:\n\n"
            f"{update.message.text}"
        )
    )

    await update.message.reply_text(
        "✅ Відповідь успішно надіслано"
    )

# =========================
# ЗАПУСК БОТА
# =========================

app = ApplicationBuilder().token(TOKEN).build()

# /start
app.add_handler(
    CommandHandler("start", start)
)

# Inline-кнопки
app.add_handler(
    CallbackQueryHandler(inline_buttons)
)

# Кнопка "Назад"
app.add_handler(
    MessageHandler(
        filters.Regex("^⬅️ Назад$"),
        back_button
    )
)

# Reply адміна
app.add_handler(
    MessageHandler(
        filters.REPLY & filters.TEXT,
        admin_reply
    )
)

# Фото
app.add_handler(
    MessageHandler(
        filters.PHOTO,
        photo_message
    )
)

# Текст
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        user_message
    )
)

print("Бот запущений...")

app.run_polling()
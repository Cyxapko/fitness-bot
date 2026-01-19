# -*- coding: utf-8 -*-
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# === Загрузка данных ===
with open('data.json', 'r', encoding='utf-8') as f:
    TRAINING_DATA = json.load(f)

# === Генерация коротких ID для упражнений (обход лимита 64 байта) ===
EXERCISE_IDS = {}
ID_TO_EXERCISE = {}
_id = 1

for place, muscles in TRAINING_DATA.items():
    for muscle, exercises in muscles.items():
        for exercise in exercises:
            key = f"{place}:{muscle}:{exercise}"
            EXERCISE_IDS[key] = str(_id)
            ID_TO_EXERCISE[str(_id)] = (place, muscle, exercise)
            _id += 1

# === Константы навигации ===
MAIN_MENU = "main"
CHOOSE_PLACE = "place"
CHOOSE_MUSCLE = "muscle"
CHOOSE_EXERCISE = "exercise"

# === Вспомогательная функция: создание клавиатуры ===
def build_menu(buttons, cols=2, back_to=None, main_menu=True):
    keyboard = [buttons[i:i + cols] for i in range(0, len(buttons), cols)]
    bottom_row = []
    if back_to:
        bottom_row.append(InlineKeyboardButton("🔙 Назад", callback_data=back_to))
    if main_menu:
        bottom_row.append(InlineKeyboardButton("🏠 Главное меню", callback_data=MAIN_MENU))
    if bottom_row:
        keyboard.append(bottom_row)
    return InlineKeyboardMarkup(keyboard)

# === Обработчики меню ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update)

async def show_main_menu(update: Update):
    text = "🏋️‍♂️ Выберите тип тренировки:"
    buttons = [
        InlineKeyboardButton("🏡 Дома", callback_data=f"{CHOOSE_PLACE}:Дома"),
        InlineKeyboardButton("🏋️ В зале", callback_data=f"{CHOOSE_PLACE}:В зале")
    ]
    reply_markup = build_menu(buttons, cols=2, main_menu=False)
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def show_muscle_groups(update: Update, place: str):
    if place not in TRAINING_DATA:
        await update.callback_query.answer("❌ Неизвестный тип тренировки.")
        return
    muscles = list(TRAINING_DATA[place].keys())
    buttons = [InlineKeyboardButton(m, callback_data=f"{CHOOSE_MUSCLE}:{place}:{m}") for m in muscles]
    reply_markup = build_menu(buttons, cols=2, back_to=MAIN_MENU)
    await update.callback_query.edit_message_text(f"📍 Тип: {place}\nВыберите группу мышц:", reply_markup=reply_markup)

async def show_exercises(update: Update, place: str, muscle: str):
    if place not in TRAINING_DATA or muscle not in TRAINING_DATA[place]:
        await update.callback_query.answer("❌ Группа мышц не найдена.")
        return
    exercises = list(TRAINING_DATA[place][muscle].keys())
    buttons = []
    for ex in exercises:
        key = f"{place}:{muscle}:{ex}"
        cb_id = EXERCISE_IDS.get(key)
        if cb_id:
            buttons.append(InlineKeyboardButton(ex, callback_data=f"{CHOOSE_EXERCISE}:{cb_id}"))
        else:
            # На всякий случай (не должно происходить)
            buttons.append(InlineKeyboardButton(ex[:20] + "...", callback_data=MAIN_MENU))
    reply_markup = build_menu(buttons, cols=1, back_to=f"{CHOOSE_PLACE}:{place}")
    await update.callback_query.edit_message_text(f"{place} → {muscle}\nВыберите упражнение:", reply_markup=reply_markup)

async def show_exercise_detail(update: Update, place: str, muscle: str, exercise: str):
    try:
        data = TRAINING_DATA[place][muscle][exercise]
        caption = f"📹 <b>{exercise}</b>\n\n💡 {data['tip']}"
        await update.callback_query.message.reply_video(
            video=data["video_url"],
            caption=caption,
            parse_mode="HTML"
        )
        # Возвращаемся к списку упражнений
        await show_exercises(update, place, muscle)
    except KeyError:
        await update.callback_query.message.reply_text("❌ Упражнение не найдено.")

# === Основной обработчик кнопок ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == MAIN_MENU:
        await show_main_menu(update)

    elif data.startswith(CHOOSE_PLACE):
        _, place = data.split(":", 1)
        await show_muscle_groups(update, place)

    elif data.startswith(CHOOSE_MUSCLE):
        parts = data.split(":", 2)
        if len(parts) == 3:
            _, place, muscle = parts
            await show_exercises(update, place, muscle)
        else:
            await query.message.reply_text("❌ Ошибка данных.")

    elif data.startswith(CHOOSE_EXERCISE):
        _, id_part = data.split(":", 1)
        if id_part in ID_TO_EXERCISE:
            place, muscle, exercise = ID_TO_EXERCISE[id_part]
            await show_exercise_detail(update, place, muscle, exercise)
        else:
            await query.message.reply_text("❌ Упражнение не найдено.")

    else:
        await query.message.reply_text("Неизвестная команда.")

# === Запуск бота ===
if __name__ == "__main__":
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не задан! Укажите его в переменных окружения Railway.")
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот запущен и готов к работе!")
    app.run_polling()

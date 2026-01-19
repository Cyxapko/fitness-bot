import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Загрузка данных
with open('data.json', 'r', encoding='utf-8') as f:
    TRAINING_DATA = json.load(f)

# Константы состояний (можно использовать для FSM, но здесь обходимся через callback_data)
MAIN_MENU = "main"
CHOOSE_PLACE = "place"
CHOOSE_MUSCLE = "muscle"
CHOOSE_EXERCISE = "exercise"

def build_menu(buttons, cols=2, back_to=None, main_menu=True):
    """Универсальная функция для создания клавиатуры с кнопками, 'Назад' и 'Главное меню'"""
    keyboard = [buttons[i:i + cols] for i in range(0, len(buttons), cols)]
    
    bottom_row = []
    if back_to:
        bottom_row.append(InlineKeyboardButton("🔙 Назад", callback_data=back_to))
    if main_menu:
        bottom_row.append(InlineKeyboardButton("🏠 Главное меню", callback_data=MAIN_MENU))
    
    if bottom_row:
        keyboard.append(bottom_row)
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update)

async def show_main_menu(update: Update):
    text = "Выберите тип тренировки:"
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
    muscles = list(TRAINING_DATA[place].keys())
    buttons = [InlineKeyboardButton(m, callback_data=f"{CHOOSE_MUSCLE}:{place}:{m}") for m in muscles]
    reply_markup = build_menu(buttons, cols=2, back_to=MAIN_MENU)
    await update.callback_query.edit_message_text(f"Тип: {place}\nВыберите группу мышц:", reply_markup=reply_markup)

async def show_exercises(update: Update, place: str, muscle: str):
    exercises = list(TRAINING_DATA[place][muscle].keys())
    buttons = [InlineKeyboardButton(e, callback_data=f"{CHOOSE_EXERCISE}:{place}:{muscle}:{e}") for e in exercises]
    reply_markup = build_menu(buttons, cols=1, back_to=f"{CHOOSE_PLACE}:{place}")
    await update.callback_query.edit_message_text(f"{place} → {muscle}\nВыберите упражнение:", reply_markup=reply_markup)

async def show_exercise_detail(update: Update, place: str, muscle: str, exercise: str):
    data = TRAINING_DATA[place][muscle][exercise]
    caption = f"📹 <b>{exercise}</b>\n\n💡 {data['tip']}"
    
    # Отправляем новое сообщение с видео (чтобы не редактировать старое)
    await update.callback_query.message.reply_video(
        video=data["video_url"],
        caption=caption,
        parse_mode="HTML"
    )
    
    # И снова показываем меню упражнений
    await show_exercises(update, place, muscle)

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
        _, place, muscle = data.split(":", 2)
        await show_exercises(update, place, muscle)
        
    elif data.startswith(CHOOSE_EXERCISE):
        _, place, muscle, exercise = data.split(":", 3)
        await show_exercise_detail(update, place, muscle, exercise)

# --- Запуск бота ---
if __name__ == "__main__":
    TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Бот запущен...")
    app.run_polling()
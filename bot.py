# -*- coding: utf-8 -*-
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Çàãðóçêà äàííûõ
with open('data.json', 'r', encoding='utf-8') as f:
    TRAINING_DATA = json.load(f)

# Êîíñòàíòû äëÿ íàâèãàöèè
MAIN_MENU = "main"
CHOOSE_PLACE = "place"
CHOOSE_MUSCLE = "muscle"
CHOOSE_EXERCISE = "exercise"

def build_menu(buttons, cols=2, back_to=None, main_menu=True):
    """Ñîçäà¸ò êëàâèàòóðó ñ êíîïêàìè, 'Íàçàä' è 'Ãëàâíîå ìåíþ'"""
    keyboard = [buttons[i:i + cols] for i in range(0, len(buttons), cols)]
    
    bottom_row = []
    if back_to:
        bottom_row.append(InlineKeyboardButton("?? Íàçàä", callback_data=back_to))
    if main_menu:
        bottom_row.append(InlineKeyboardButton("?? Ãëàâíîå ìåíþ", callback_data=MAIN_MENU))
    
    if bottom_row:
        keyboard.append(bottom_row)
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update)

async def show_main_menu(update: Update):
    text = "?????? Âûáåðèòå òèï òðåíèðîâêè:"
    buttons = [
        InlineKeyboardButton("?? Äîìà", callback_data=f"{CHOOSE_PLACE}:Äîìà"),
        InlineKeyboardButton("??? Â çàëå", callback_data=f"{CHOOSE_PLACE}:Â çàëå")
    ]
    reply_markup = build_menu(buttons, cols=2, main_menu=False)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def show_muscle_groups(update: Update, place: str):
    if place not in TRAINING_DATA:
        await update.callback_query.answer("Îøèáêà: íåèçâåñòíûé òèï òðåíèðîâêè.")
        return
    muscles = list(TRAINING_DATA[place].keys())
    buttons = [InlineKeyboardButton(m, callback_data=f"{CHOOSE_MUSCLE}:{place}:{m}") for m in muscles]
    reply_markup = build_menu(buttons, cols=2, back_to=MAIN_MENU)
    await update.callback_query.edit_message_text(f"?? Òèï: {place}\nÂûáåðèòå ãðóïïó ìûøö:", reply_markup=reply_markup)

async def show_exercises(update: Update, place: str, muscle: str):
    if place not in TRAINING_DATA or muscle not in TRAINING_DATA[place]:
        await update.callback_query.answer("Îøèáêà: ãðóïïà ìûøö íå íàéäåíà.")
        return
    exercises = list(TRAINING_DATA[place][muscle].keys())
    buttons = [InlineKeyboardButton(e, callback_data=f"{CHOOSE_EXERCISE}:{place}:{muscle}:{e}") for e in exercises]
    reply_markup = build_menu(buttons, cols=1, back_to=f"{CHOOSE_PLACE}:{place}")
    await update.callback_query.edit_message_text(f"{place} ? {muscle}\nÂûáåðèòå óïðàæíåíèå:", reply_markup=reply_markup)

async def show_exercise_detail(update: Update, place: str, muscle: str, exercise: str):
    try:
        data = TRAINING_DATA[place][muscle][exercise]
        caption = f"?? <b>{exercise}</b>\n\n?? {data['tip']}"
        
        await update.callback_query.message.reply_video(
            video=data["video_url"],
            caption=caption,
            parse_mode="HTML"
        )
        # Âîçâðàùàåìñÿ ê ñïèñêó óïðàæíåíèé
        await show_exercises(update, place, muscle)
    except KeyError:
        await update.callback_query.message.reply_text("? Óïðàæíåíèå íå íàéäåíî.")

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
            await query.message.reply_text("? Îøèáêà äàííûõ.")
            
    elif data.startswith(CHOOSE_EXERCISE):
        parts = data.split(":", 3)
        if len(parts) == 4:
            _, place, muscle, exercise = parts
            await show_exercise_detail(update, place, muscle, exercise)
        else:
            await query.message.reply_text("? Îøèáêà äàííûõ.")
    else:
        await query.message.reply_text("Íåèçâåñòíàÿ êîìàíäà.")

# --- Çàïóñê ---
if __name__ == "__main__":
    import os
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Ïîæàëóéñòà, óñòàíîâèòå ïåðåìåííóþ îêðóæåíèÿ TELEGRAM_BOT_TOKEN")
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("? Áîò çàïóùåí! Íàæìèòå Ctrl+C ÷òîáû îñòàíîâèòü.")

    app.run_polling()

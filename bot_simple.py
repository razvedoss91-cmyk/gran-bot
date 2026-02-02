import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

TOKEN = os.getenv("TELEGRAM_TOKEN")
KNIVES, LOAD, PEAKS = range(3)

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Сколько ножей? (число):")
    return KNIVES

async def ask_knives(update: Update, context: CallbackContext) -> int:
    try:
        knives = int(update.message.text)
        context.user_data["knives"] = knives
        await update.message.reply_text(
            "Нагрузка?",
            reply_markup=ReplyKeyboardMarkup([["Низкая", "Средняя", "Высокая"]], one_time_keyboard=True)
        )
        return LOAD
    except:
        await update.message.reply_text("Введите число:")
        return KNIVES

async def ask_load(update: Update, context: CallbackContext) -> int:
    context.user_data["load"] = update.message.text
    await update.message.reply_text(
        "Бумы?",
        reply_markup=ReplyKeyboardMarkup([["Нет", "Иногда", "Регулярно", "Постоянно"]], one_time_keyboard=True)
    )
    return PEAKS

async def ask_peaks(update: Update, context: CallbackContext) -> int:
    knives = context.user_data["knives"]
    
    if knives <= 14:
        package = "СТАРТ (9 000 ₽)"
    elif knives <= 21:
        package = "КЛАССИК (13 000 ₽)"
    elif knives <= 28:
        package = "ПРОФИ (17 500 ₽)"
    else:
        package = "ПРЕМИУМ (36 000 ₽)"
    
    await update.message.reply_text(
        f"Рекомендация: {package}\n\n"
        "Для договора:\n📞 +7 (951) 535-77-67",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            KNIVES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_knives)],
            LOAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_load)],
            PEAKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_peaks)],
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: ConversationHandler.END)],
    )
    
    app.add_handler(conv_handler)
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
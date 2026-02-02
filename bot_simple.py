import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler, CallbackContext

TOKEN = os.getenv("TELEGRAM_TOKEN")
KNIVES, LOAD, PEAKS = range(3)

print(f"🤖 Начинаю запуск бота с токеном: {TOKEN[:10]}...")

async def start(update: Update, context: CallbackContext) -> int:
    print(f"Пользователь {update.effective_user.id} запустил бота")
    await update.message.reply_text(
        "🔪 *СКОЛЬКО ИНСТРУМЕНТА В ОБОРОТЕ?*\n\n"
        "Укажите общее количество ножей на кухне:\n\n"
        "*Введите число:* (например: 18)",
        parse_mode="Markdown"
    )
    return KNIVES

async def ask_knives(update: Update, context: CallbackContext) -> int:
    try:
        knives = int(update.message.text)
        context.user_data["knives"] = knives
        keyboard = [["ЛЁГКАЯ", "СРЕДНЯЯ", "ВЫСОКАЯ"]]
        await update.message.reply_text(
            f"✅ {knives} ножей.\n\n"
            "📊 *КАКАЯ СРЕДНЯЯ НАГРУЗКА НА КХНЮ?*\n\n"
            "• ЛЁГКАЯ — до 50 covers в день\n"
            "• СРЕДНЯЯ — 50-150 covers\n"
            "• ВЫСОКАЯ — от 150 covers",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        )
        return LOAD
    except:
        await update.message.reply_text("Введите число (например: 18):")
        return KNIVES

async def ask_load(update: Update, context: CallbackContext) -> int:
    context.user_data["load"] = update.message.text
    keyboard = [["РАВНОМЕРНО", "СЕЗОННО", "СОБЫТИЙНО", "ПОСТОЯННО"]]
    await update.message.reply_text(
        "🚀 *КАК ЧАСТО БЫВАЮТ ПИКОВЫЕ НАГРУЗКИ?*\n\n"
        "• РАВНОМЕРНО — без резких всплесков\n"
        "• СЕЗОННО — по дням недели/времени года\n"
        "• СОБЫТИЙНО — банкеты, праздники\n"
        "• ПОСТОЯННО — всегда высокий темп",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return PEAKS

async def ask_peaks(update: Update, context: CallbackContext) -> int:
    peaks = update.message.text
    knives = context.user_data["knives"]
    load = context.user_data["load"]
    
    # Логика выбора
    if knives <= 14:
        package, price = "СТАРТ", "9 000 ₽"
    elif knives <= 21:
        package, price = "КЛАССИК", "13 000 ₽"
    elif knives <= 28:
        package, price = "ПРОФИ", "17 500 ₽"
    else:
        package, price = "ПРЕМИУМ", "36 000 ₽"
    
    # Кнопки
    keyboard = [
        [InlineKeyboardButton(f"✅ Выбрать {package}", callback_data="select")],
        [InlineKeyboardButton("📞 Позвонить Тимофею", url="tel:+79515357767")],
        [InlineKeyboardButton("✉️ Написать в Telegram", url="https://t.me/pod_pravilnym_ugLom")]
    ]
    
    await update.message.reply_text(
        f"🎯 *РЕКОМЕНДАЦИЯ*\n\n"
        f"*Параметры:*\n"
        f"• Ножей: {knives}\n"
        f"• Нагрузка: {load}\n"
        f"• Пики: {peaks}\n\n"
        f"*Пакет:* **{package}** — {price}/месяц\n\n"
        "Свяжитесь для договора:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✅ *Отлично! Я с Вами свяжусь!*\n\n"
        "📞 +7 (951) 535-77-67\n"
        "✉️ @pod_pravilnym_ugLom\n"
        "🌐 granservice.pro",
        parse_mode="Markdown"
    )
    print(f"✅ Пользователь {query.from_user.id} выбрал пакет")

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Отменено. /start")
    return ConversationHandler.END

async def main():
    print("🤖 Создаю приложение...")
    app = Application.builder().token(TOKEN).build()
    
    print("🤖 Настраиваю диалог...")
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            KNIVES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_knives)],
            LOAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_load)],
            PEAKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_peaks)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот запускается...")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    print("🚀 Запуск бота...")
    asyncio.run(main())

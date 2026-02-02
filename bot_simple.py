import os
import logging
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
    CallbackContext,
)
from threading import Thread

# Токен будет из переменных окружения Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
# Ваш ID в Telegram для уведомлений (вставьте свой)
YOUR_CHAT_ID = "6314983702"  # Узнать можно через @userinfobot

# Состояния диалога
KNIVES, LOAD, PEAKS, CONFIRM = range(4)

# Логика выбора пакета
def get_package_recommendation(knives, load, peaks):
    """Определяем пакет по параметрам"""
    if knives <= 14:
        package = "СТАРТ"
        price = "9 000 ₽"
        details = "• до 14 ножей\n• 2 выезда в месяц\n• без подменного фонда\n• срок: до 48 ч."
    elif knives <= 21:
        package = "КЛАССИК"
        price = "13 000 ₽"
        details = "• до 21 ножа\n• 3 выезда в месяц\n• 1 комплект подменных\n• срок: до 48 ч."
    elif knives <= 28:
        package = "ПРОФИ"
        price = "17 500 ₽"
        details = "• до 28 ножей\n• 4 выезда в месяц\n• 2 комплекта подменных\n• срок: до 48 ч."
    else:
        package = "ПРЕМИУМ"
        price = "36 000 ₽"
        details = "• до 60 ножей\n• 6 выездов в месяц\n• 3 комплекта подменных\n• срок: до 24 ч."
    
    # Корректировка по нагрузке
    if load == "ВЫСОКАЯ" and package in ["СТАРТ", "КЛАССИК"]:
        package = "ПРОФИ"
        price = "17 500 ₽"
        details = "• до 28 ножей\n• 4 выезда в месяц\n• 2 комплекта подменных\n• срок: до 48 ч."
    
    # Корректировка по пикам
    if peaks == "ПОСТОЯННО" and package != "ПРЕМИУМ":
        package = "ПРЕМИУМ"
        price = "36 000 ₽"
        details = "• до 60 ножей\n• 6 выездов в месяц\n• 3 комплекта подменных\n• срок: до 24 ч."
    
    return package, price, details

# Команда /start
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "🔪 *СКОЛЬКО ИНСТРУМЕНТА В ОБОРОТЕ?*\n\n"
        "Укажите общее количество ножей, которые активно используются на вашей кухне:\n\n"
        "• Шеф-нож / поварской\n"
        "• Сенсюки / универсальные\n"
        "• Разделочные\n"
        "• Филейные\n"
        "• Прочие специализированные\n\n"
        "*Введите общее число:* (например: 18)",
        parse_mode="Markdown"
    )
    return KNIVES

# Вопрос 1: Количество ножей
async def ask_knives(update: Update, context: CallbackContext) -> int:
    try:
        knives = int(update.message.text)
        if knives <= 0:
            await update.message.reply_text("Пожалуйста, введите положительное число.")
            return KNIVES
        
        context.user_data["knives"] = knives
        
        keyboard = [["ЛЁГКАЯ", "СРЕДНЯЯ", "ВЫСОКАЯ"]]
        await update.message.reply_text(
            f"✅ Принято: {knives} единиц инструмента.\n\n"
            "📊 *КАКОЙ ОБЪЁМ РАБОТЫ КУХНИ?*\n\n"
            "Оцените среднюю ежедневную нагрузку:\n\n"
            "• *ЛЁГКАЯ* — до 50 покрытий (covers) в день\n"
            "  (небольшие кафе, пекарни, завтраки)\n\n"
            "• *СРЕДНЯЯ* — 50-150 покрытий в день\n"
            "  (рестораны с стабильным потоком, бизнес-ланчи)\n\n"
            "• *ВЫСОКАЯ* — от 150 покрытий в день\n"
            "  (рестораны с живой кухни, вечерние сессии, кейтеринг)",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return LOAD
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число (например: 18).")
        return KNIVES

# Вопрос 2: Нагрузка
async def ask_load(update: Update, context: CallbackContext) -> int:
    load = update.message.text
    if load not in ["ЛЁГКАЯ", "СРЕДНЯЯ", "ВЫСОКАЯ"]:
        keyboard = [["ЛЁГКАЯ", "СРЕДНЯЯ", "ВЫСОКАЯ"]]
        await update.message.reply_text(
            "Пожалуйста, выберите вариант из клавиатуры:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return LOAD
    
    context.user_data["load"] = load
    
    keyboard = [["РАВНОМЕРНО", "СЕЗОННО", "СОБЫТИЙНО", "ПОСТОЯННО"]]
    await update.message.reply_text(
        f"✅ Принято: {load} нагрузка.\n\n"
        "🚀 *КАКИЕ ПИКОВЫЕ НАГРУЗКИ БЫВАЮТ?*\n\n"
        "Как часто кухня работает на пределе возможностей:\n\n"
        "• *РАВНОМЕРНО* — график предсказуем, без резких всплесков\n"
        "• *СЕЗОННО* — зависит от дня недели или времени года\n"
        "• *СОБЫТИЙНО* — банкеты, корпоративы, праздничные дни\n"
        "• *ПОСТОЯННО* — кухня постоянно в высоком темпе (сетевые проекты, фуд-холлы)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PEAKS

# Вопрос 3: Пиковые нагрузки и результат
async def ask_peaks(update: Update, context: CallbackContext) -> int:
    peaks = update.message.text
    if peaks not in ["РАВНОМЕРНО", "СЕЗОННО", "СОБЫТИЙНО", "ПОСТОЯННО"]:
        keyboard = [["РАВНОМЕРНО", "СЕЗОННО", "СОБЫТИЙНО", "ПОСТОЯННО"]]
        await update.message.reply_text(
            "Пожалуйста, выберите вариант из клавиатуры:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return PEAKS
    
    # Получаем данные
    context.user_data["peaks"] = peaks
    knives = context.user_data["knives"]
    load = context.user_data["load"]
    
    # Рассчитываем пакет
    package, price, details = get_package_recommendation(knives, load, peaks)
    context.user_data["recommended_package"] = package
    context.user_data["recommended_price"] = price
    
    # Формируем ответ
    response = (
        f"🎯 *РЕКОМЕНДАЦИЯ*\n\n"
        f"*Параметры вашей кухни:*\n"
        f"• Инструмент: {knives} ножей\n"
        f"• Нагрузка: {load}\n"
        f"• Пики: {peaks}\n\n"
        
        f"*Оптимальный пакет:*\n"
        f"**{package}** — {price}/месяц\n\n"
        
        f"*Что входит:*\n"
        f"{details}\n\n"
        
        f"*Почему этот пакет:*\n"
    )
    
    # Добавляем обоснование
    if knives <= 14:
        response += "Для небольших кухонь с гибким графиком."
    elif knives <= 21:
        response += "Оптимально для стабильной работы без простоев."
    elif knives <= 28:
        response += "Для кухонь с высокой нагрузкой и регулярными пиками."
    else:
        response += "Для крупных кухонь, сетей и постоянных пиковых нагрузок."
    
    # Создаём inline-кнопки
    keyboard = [
        [
            InlineKeyboardButton(f"✅ Выбрать {package}", callback_data="select_package"),
            InlineKeyboardButton("🔄 Начать заново", callback_data="restart")
        ],
        [
            InlineKeyboardButton("📞 Позвонить Тимофею", url="tel:+79515357767"),
            InlineKeyboardButton("✉️ Написать в Telegram", url="https://t.me/pod_pravilnym_ugLom")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    response += "\n\n"
    response += (
        "⚠️ *Это предварительная рекомендация.*\n"
        "Для точного расчёта и составления договора свяжитесь со мной:"
    )
    
    await update.message.reply_text(
        response,
        parse_mode="Markdown",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    
    return CONFIRM

# Обработка нажатия кнопок
async def button_handler(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "select_package":
        # Отправляем уведомление вам
        user = query.from_user
        user_info = (
            f"👤 *НОВАЯ ЗАЯВКА ЧЕРЕЗ БОТА*\n\n"
            f"• Имя: {user.first_name or ''} {user.last_name or ''}\n"
            f"• Username: @{user.username if user.username else 'нет'}\n"
            f"• ID: {user.id}\n\n"
            f"*Параметры кухни:*\n"
            f"• Ножей: {context.user_data.get('knives', 'N/A')}\n"
            f"• Нагрузка: {context.user_data.get('load', 'N/A')}\n"
            f"• Пики: {context.user_data.get('peaks', 'N/A')}\n"
            f"• Рекомендованный пакет: {context.user_data.get('recommended_package', 'N/A')}\n"
            f"• Стоимость: {context.user_data.get('recommended_price', 'N/A')}\n\n"
            f"✅ *Пользователь выбрал пакет!*"
        )
        
        try:
            # Отправляем вам уведомление
            await context.bot.send_message(
                chat_id=YOUR_CHAT_ID,
                text=user_info,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")
        
        # Подтверждаем пользователю
        keyboard = [[
            InlineKeyboardButton("📞 Позвонить Тимофею", url="tel:+79515357767"),
            InlineKeyboardButton("✉️ Написать в Telegram", url="https://t.me/pod_pravilnym_ugLom")
        ]]
        
        await query.edit_message_text(
            "✅ *Отлично! Я уже уведомил Тимофея о вашем выборе!*\n\n"
            "Он свяжется с вами в течение 30 минут в рабочее время (Пн-Пт 10:00-19:00).\n\n"
            "📞 *Тимофей Борздов* — руководитель сервиса «Грань»\n"
            "Связаться можно сразу:\n"
            "[+7 (951) 535-77-67](tel:+79515357767) | "
            "[Telegram](https://t.me/pod_pravilnym_ugLom)\n\n"
            "Сайт: granservice.pro",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
        
        return ConversationHandler.END
    
    elif query.data == "restart":
        await query.edit_message_text(
            "Начинаем заново! Напишите /start",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Диалог отменён. Если хотите начать заново — /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Обработка ошибок
async def error_handler(update: Update, context: CallbackContext):
    logging.error(f"Update {update} caused error {context.error}")
    try:
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, начните заново: /start"
        )
    except:
        pass

# Простейший HTTP-сервер для Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Telegram bot is running!')
    
    def log_message(self, format, *args):
        pass

def run_http_server(port=8080):
    """Запускает HTTP-сервер для Render"""
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"✅ HTTP-сервер запущен на порту {port}")
    server.serve_forever()

async def run_bot():
    """Асинхронный запуск Telegram бота"""
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_TOKEN не установлен!")
        return
    
    print("🤖 Запуск Telegram бота...")
    
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            KNIVES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_knives)],
            LOAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_load)],
            PEAKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_peaks)],
            CONFIRM: [CallbackQueryHandler(button_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    
    print("✅ Бот запущен и готов к работе!")
    await app.run_polling(drop_pending_updates=True)

def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_TOKEN не установлен!")
        return
    
    # Запускаем HTTP-сервер в отдельном потоке
    port = int(os.environ.get("PORT", 8080))
    http_thread = Thread(target=run_http_server, args=(port,))
    http_thread.daemon = True
    http_thread.start()
    print(f"🌐 HTTP-сервер запущен в отдельном потоке на порту {port}")
    
    # Запускаем бота в главном потоке
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()

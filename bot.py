import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext,
)

# Токен будет из переменных окружения Render
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Состояния диалога
KNIVES, LOAD, PEAKS = range(3)

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
    if load == "Высокая" and package in ["СТАРТ", "КЛАССИК"]:
        package = "ПРОФИ"
        price = "17 500 ₽"
        details = "• до 28 ножей\n• 4 выезда в месяц\n• 2 комплекта подменных\n• срок: до 48 ч."
    
    # Корректировка по бумам
    if peaks == "Постоянно" and package != "ПРЕМИУМ":
        package = "ПРЕМИУМ"
        price = "36 000 ₽"
        details = "• до 60 ножей\n• 6 выездов в месяц\n• 3 комплекта подменных\n• срок: до 24 ч."
    
    return package, price, details

# Команда /start
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "🔪 *ГРАНЬ — Подбор пакета обслуживания*\n\n"
        "Ответьте на 3 вопроса, и я подберу оптимальный пакет для вашей кухни.\n\n"
        "1️⃣ *Сколько всего ножей работает на вашей кухне?*\n"
        "(Введите число, например: 15)",
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
        
        keyboard = [["Низкая", "Средняя", "Высокая"]]
        await update.message.reply_text(
            f"✅ Принято: {knives} ножей.\n\n"
            "2️⃣ *Какова нагрузка на кухню?*\n"
            "• Низкая — до 50 covers в день\n"
            "• Средняя — 50-150 covers в день\n"
            "• Высокая — от 150 covers в день",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return LOAD
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число (например: 12).")
        return KNIVES

# Вопрос 2: Нагрузка
async def ask_load(update: Update, context: CallbackContext) -> int:
    load = update.message.text
    if load not in ["Низкая", "Средняя", "Высокая"]:
        keyboard = [["Низкая", "Средняя", "Высокая"]]
        await update.message.reply_text(
            "Пожалуйста, выберите вариант из клавиатуры:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return LOAD
    
    context.user_data["load"] = load
    
    keyboard = [["Нет", "Иногда", "Регулярно", "Постоянно"]]
    await update.message.reply_text(
        f"✅ Принято: {load} нагрузка.\n\n"
        "3️⃣ *Бывают ли срочные «бумы» и с какой периодичностью?*\n"
        "• Нет — работа равномерная\n"
        "• Иногда — раз в 1-2 месяца\n"
        "• Регулярно — несколько раз в месяц\n"
        "• Постоянно — почти каждый день/неделю",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PEAKS

# Вопрос 3: Бумы и результат
async def ask_peaks(update: Update, context: CallbackContext) -> int:
    peaks = update.message.text
    if peaks not in ["Нет", "Иногда", "Регулярно", "Постоянно"]:
        keyboard = [["Нет", "Иногда", "Регулярно", "Постоянно"]]
        await update.message.reply_text(
            "Пожалуйста, выберите вариант из клавиатуры:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return PEAKS
    
    # Получаем данные
    knives = context.user_data["knives"]
    load = context.user_data["load"]
    
    # Рассчитываем пакет
    package, price, details = get_package_recommendation(knives, load, peaks)
    
    # Формируем ответ
    response = (
        f"🎯 *РЕКОМЕНДАЦИЯ*\n\n"
        f"*Ваши параметры:*\n"
        f"• Ножей: {knives}\n"
        f"• Нагрузка: {load}\n"
        f"• Бумы: {peaks}\n\n"
        
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
    
    response += "\n\n"
    response += (
        "⚠️ *Это предварительная рекомендация.*\n"
        "Для точного расчёта и составления договора:\n\n"
        
        "📞 +7 (951) 535-77-67\n"
        "✉️ @pod_pravilnym_ugLom\n"
        "🌐 granservice.pro\n\n"
        
        "Начать заново: /start"
    )
    
    await update.message.reply_text(
        response,
        parse_mode="Markdown",
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
        pass  # Отключаем логи запросов

def run_http_server(port=8080):
    """Запускает HTTP-сервер для Render"""
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"✅ HTTP-сервер запущен на порту {port}")
    server.serve_forever()

def run_bot():
    """Запускает Telegram бота"""
    # Проверяем токен
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_TOKEN не установлен!")
        print("Добавьте переменную TELEGRAM_TOKEN в настройках Render")
        return
    
    print("🤖 Запуск Telegram бота...")
    
    # Создаём приложение
    app = Application.builder().token(TOKEN).build()
    
    # Настраиваем диалог
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            KNIVES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_knives)],
            LOAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_load)],
            PEAKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_peaks)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    
    # Запускаем бота
    print("✅ Бот запущен и готов к работе!")
    app.run_polling(drop_pending_updates=True)

def main():
    """Основная функция"""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Получаем порт из переменной окружения (Render сам назначает)
    port = int(os.environ.get("PORT", 8080))
    
    # Запускаем HTTP-сервер в основном потоке
    print(f"🌐 Запуск HTTP-сервера для Render на порту {port}...")
    run_http_server(port)

if __name__ == "__main__":
    main()

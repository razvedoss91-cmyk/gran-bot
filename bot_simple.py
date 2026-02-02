import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import threading

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Изменено на DEBUG для детальной отладки
)
logger = logging.getLogger(__name__)

# Токен будет из переменных окружения Render
TOKEN = os.getenv("TELEGRAM_TOKEN")
# Ваш ID в Telegram для уведомлений (вставьте свой)
YOUR_CHAT_ID = "6314983702"  # Узнать можно через @userinfobot

# Логика выбора пакета
def get_package_recommendation(knives, load, peaks):
    """Определяем пакет по параметрам"""
    logger.debug(f"Рассчитываем пакет: ножей={knives}, нагрузка={load}, пики={peaks}")
    
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
        logger.debug(f"Корректируем из-за высокой нагрузки")
        package = "ПРОФИ"
        price = "17 500 ₽"
        details = "• до 28 ножей\n• 4 выезда в месяц\n• 2 комплекта подменных\n• срок: до 48 ч."
    
    # Корректировка по пикам
    if peaks == "ПОСТОЯННО" and package != "ПРЕМИУМ":
        logger.debug(f"Корректируем из-за постоянных пиков")
        package = "ПРЕМИУМ"
        price = "36 000 ₽"
        details = "• до 60 ножей\n• 6 выездов в месяц\n• 3 комплекта подменных\n• срок: до 24 ч."
    
    logger.debug(f"Результат: пакет={package}, цена={price}")
    return package, price, details

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Команда /start от пользователя {update.effective_user.id}")
    context.user_data.clear()
    context.user_data["step"] = "knives"
    
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

# Обработка всех сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text
    
    logger.info(f"Сообщение от {user_id}: '{message_text}'")
    logger.debug(f"Текущий шаг: {context.user_data.get('step')}")
    
    # Пропускаем команды
    if message_text.startswith('/'):
        logger.debug(f"Пропускаем команду: {message_text}")
        return
    
    step = context.user_data.get("step", "knives")
    logger.debug(f"Обрабатываем шаг: {step}")
    
    try:
        if step == "knives":
            # Шаг 1: Количество ножей
            logger.debug(f"Шаг 1: обработка количества ножей")
            try:
                knives = int(message_text)
                logger.debug(f"Введено число: {knives}")
                
                if knives <= 0:
                    logger.debug(f"Число не положительное: {knives}")
                    await update.message.reply_text("Пожалуйста, введите положительное число.")
                    return
                
                context.user_data["knives"] = knives
                context.user_data["step"] = "load"
                logger.debug(f"Установлен шаг: load, ножей: {knives}")
                
                keyboard = [["ЛЁГКАЯ", "СРЕДНЯЯ", "ВЫСОКАЯ"]]
                logger.debug("Отправляем запрос о нагрузке")
                
                await update.message.reply_text(
                    f"✅ Принято: {knives} единиц инструмента.\n\n"
                    "📊 *КАКОЙ ОБЪЁМ РАБОТЫ КУХНИ?*\n\n"
                    "Оцените среднюю ежедневную нагрузку:\n\n"
                    "• *ЛЁГКАЯ* — до 50 покрытий (covers) в день\n"
                    "  (небольшие кафе, пекарни, завтраки)\n\n"
                    "• *СРЕДНЯЯ* — 50-150 покрытий в день\n"
                    "  (рестораны с стабильным потоком, бизнес-ланчи)\n\n"
                    "• *ВЫСОКАЯ* — от 150 покрытий в день\n"
                    "  (рестораны с живой кухней, вечерние сессии, кейтеринг)",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                )
                logger.debug("Запрос о нагрузке отправлен успешно")
                
            except ValueError:
                logger.debug(f"Ошибка преобразования в число: {message_text}")
                await update.message.reply_text("Пожалуйста, введите число (например: 18).")
        
        elif step == "load":
            # Шаг 2: Нагрузка
            logger.debug(f"Шаг 2: обработка нагрузки")
            load = message_text.upper()
            logger.debug(f"Получена нагрузка: {load}")
            
            # Нормализуем возможные варианты написания
            load_mapping = {
                "ЛЕГКАЯ": "ЛЁГКАЯ",
                "ЛЁГКАЯ": "ЛЁГКАЯ",
                "СРЕДНЯЯ": "СРЕДНЯЯ", 
                "ВЫСОКАЯ": "ВЫСОКАЯ",
                "ЛЕГКО": "ЛЁГКАЯ",
                "СРЕДНЕ": "СРЕДНЯЯ",
                "ВЫСОКО": "ВЫСОКАЯ"
            }
            
            if load not in load_mapping:
                logger.debug(f"Неизвестная нагрузка: {load}")
                keyboard = [["ЛЁГКАЯ", "СРЕДНЯЯ", "ВЫСОКАЯ"]]
                await update.message.reply_text(
                    "Пожалуйста, выберите вариант из клавиатуры:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                )
                return
            
            load_normalized = load_mapping[load]
            context.user_data["load"] = load_normalized
            context.user_data["step"] = "peaks"
            logger.debug(f"Установлен шаг: peaks, нагрузка: {load_normalized}")
            
            keyboard = [["РАВНОМЕРНО", "СЕЗОННО", "СОБЫТИЙНО", "ПОСТОЯННО"]]
            logger.debug("Отправляем запрос о пиковых нагрузках")
            
            await update.message.reply_text(
                f"✅ Принято: {load_normalized} нагрузка.\n\n"
                "🚀 *КАКИЕ ПИКОВЫЕ НАГРУЗКИ БЫВАЮТ?*\n\n"
                "Как часто кухня работает на пределе возможностей:\n\n"
                "• *РАВНОМЕРНО* — график предсказуем, без резких всплесков\n"
                "• *СЕЗОННО* — зависит от дня недели или времени года\n"
                "• *СОБЫТИЙНО* — банкеты, корпоративы, праздничные дни\n"
                "• *ПОСТОЯННО* — кухня постоянно в высоком темпе (сетевые проекты, фуд-холлы)",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            logger.debug("Запрос о пиковых нагрузках отправлен успешно")
        
        elif step == "peaks":
            # Шаг 3: Пиковые нагрузки
            logger.debug(f"Шаг 3: обработка пиковых нагрузок")
            peaks = message_text.upper()
            logger.debug(f"Получены пики: {peaks}")
            
            # Нормализуем возможные варианты написания
            peaks_mapping = {
                "РАВНОМЕРНО": "РАВНОМЕРНО",
                "СЕЗОННО": "СЕЗОННО",
                "СОБЫТИЙНО": "СОБЫТИЙНО",
                "СОБЫТИЙНЫЕ": "СОБЫТИЙНО",
                "ПОСТОЯННО": "ПОСТОЯННО",
                "ПОСТОЯННЫЕ": "ПОСТОЯННО",
                "РАВНОМЕРНЫЕ": "РАВНОМЕРНО",
                "СЕЗОННЫЕ": "СЕЗОННО"
            }
            
            if peaks not in peaks_mapping:
                logger.debug(f"Неизвестные пики: {peaks}")
                keyboard = [["РАВНОМЕРНО", "СЕЗОННО", "СОБЫТИЙНО", "ПОСТОЯННО"]]
                await update.message.reply_text(
                    "Пожалуйста, выберите вариант из клавиатуры:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                )
                return
            
            peaks_normalized = peaks_mapping[peaks]
            context.user_data["peaks"] = peaks_normalized
            logger.debug(f"Пики сохранены: {peaks_normalized}")
            
            # Получаем все данные
            knives = context.user_data.get("knives", 0)
            load = context.user_data.get("load", "")
            
            logger.debug(f"Все данные: ножей={knives}, нагрузка={load}, пики={peaks_normalized}")
            
            # Рассчитываем пакет
            package, price, details = get_package_recommendation(knives, load, peaks_normalized)
            context.user_data["recommended_package"] = package
            context.user_data["recommended_price"] = price
            logger.debug(f"Рассчитан пакет: {package} за {price}")
            
            # Формируем ответ
            response = (
                f"🎯 *РЕКОМЕНДАЦИЯ*\n\n"
                f"*Параметры вашей кухни:*\n"
                f"• Инструмент: {knives} ножей\n"
                f"• Нагрузка: {load}\n"
                f"• Пики: {peaks_normalized}\n\n"
                
                f"*Оптимальный пакет:*\n"
                f"**{package}** — {price}/месяц\n\n"
                
                f"*Что входит:*\n"
                f"{details}\n\n"
            )
            
            # Добавляем обоснование
            if knives <= 14:
                response += "*Почему этот пакет:* Для небольших кухонь с гибким графиком."
            elif knives <= 21:
                response += "*Почему этот пакет:* Оптимально для стабильной работы без простоев."
            elif knives <= 28:
                response += "*Почему этот пакет:* Для кухонь с высокой нагрузкой и регулярными пиками."
            else:
                response += "*Почему этот пакет:* Для крупных кухонь, сетей и постоянных пиковых нагрузок."
            
            response += "\n\n"
            response += (
                "⚠️ *Это предварительная рекомендация.*\n"
                "Для точного расчёта и составления договора свяжитесь со мной:"
            )
            
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
            
            logger.debug("Пытаемся отправить финальное сообщение")
            
            # Удаляем клавиатуру предыдущего шага и отправляем новый ответ
            await update.message.reply_text(
                response,
                parse_mode="Markdown",
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
            # Сбрасываем шаг, чтобы можно было начать заново
            context.user_data["step"] = "completed"
            logger.debug("Финальное сообщение отправлено успешно, шаг установлен: completed")
        
        else:
            logger.debug(f"Неизвестный шаг: {step}")
            await update.message.reply_text(
                "Диалог завершен. Напишите /start, чтобы начать заново.",
                reply_markup=ReplyKeyboardRemove()
            )
    
    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА в handle_message: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла непредвиденная ошибка. Пожалуйста, начните заново: /start"
        )
        # Сбрасываем состояние
        context.user_data.clear()

# Обработка нажатия кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data
    
    logger.info(f"Callback от {user_id}: {callback_data}")
    await query.answer()
    
    try:
        if callback_data == "select_package":
            logger.debug("Обработка выбора пакета")
            
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
                logger.debug(f"Уведомление отправлено на chat_id: {YOUR_CHAT_ID}")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")
            
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
            logger.debug("Сообщение о выборе пакета отправлено")
        
        elif callback_data == "restart":
            logger.debug("Обработка перезапуска")
            # Очищаем данные и отправляем инструкцию
            context.user_data.clear()
            await query.edit_message_text(
                "Диалог сброшен. Напишите /start, чтобы начать заново.",
                reply_markup=ReplyKeyboardRemove()
            )
            logger.debug("Диалог сброшен")
    
    except Exception as e:
        logger.error(f"Ошибка в button_handler: {e}", exc_info=True)
        await query.edit_message_text(
            "Произошла ошибка. Пожалуйста, начните заново: /start"
        )

# Команда /reset для принудительного сброса
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Команда /reset от пользователя {update.effective_user.id}")
    context.user_data.clear()
    await update.message.reply_text(
        "Все данные сброшены. Начните заново: /start",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка в обработке обновления: {context.error}", exc_info=True)
    try:
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, начните заново: /start"
        )
    except:
        logger.error("Не удалось отправить сообщение об ошибке")

# Простейший HTTP-сервер для Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Telegram bot is running!')
    
    def log_message(self, format, *args):
        pass

def run_http_server():
    """Запускает HTTP-сервер для Render"""
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"✅ HTTP-сервер запущен на порту {port}")
    server.serve_forever()

def main():
    """Главная функция"""
    print("🚀 Запуск бота...")
    
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_TOKEN не установлен!")
        return
    
    # Запускаем HTTP-сервер в отдельном потоке
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Создаем и запускаем бота в главном потоке
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик ошибок
    app.add_error_handler(error_handler)
    
    print("🤖 Бот запущен и готов к работе!")
    
    # Запускаем бота
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

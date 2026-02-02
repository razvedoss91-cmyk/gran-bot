import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import threading

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен будет из переменных окружения Render
TOKEN = os.getenv("TELEGRAM_TOKEN")

# === ВАШИ ДАННЫЕ ===
YOUR_CHAT_ID = 6314983702  # Ваш ID для уведомлений
YOUR_TELEGRAM_USERNAME = "rojdennebesamy"  # Ваш username для лички
YOUR_TELEGRAM_CHANNEL = "pod_pravilnym_uglom"  # Ваш канал
# ===================

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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Полностью очищаем состояние
    context.user_data.clear()
    context.user_data["step"] = "knives"
    
    await update.message.reply_text(
        "🔪 *СКОЛЬКО ИНСТРУМЕНТА В ОБОРОТЕ?*\n\n"
        "Укажите общее количество ножей, которые используются на вашей кухне:\n\n"
        "• Шеф-нож\n"
        "• Универсальный\n"
        "• Разделочный\n"
        "• Филейный\n"
        "• Прочие специализированные\n\n"
        "*Введите общее число:* (например: 18)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()  # Удаляем старую клавиатуру
    )

# Обработка всех сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Пропускаем команды
    if update.message.text.startswith('/'):
        return
    
    step = context.user_data.get("step", "knives")
    logger.info(f"Обработка сообщения от {update.effective_user.id}. Шаг: {step}")
    
    try:
        if step == "knives":
            # Шаг 1: Количество ножей
            try:
                knives = int(update.message.text)
                if knives <= 0:
                    await update.message.reply_text("Пожалуйста, введите положительное число.")
                    return
                
                context.user_data["knives"] = knives
                context.user_data["step"] = "load"
                
                keyboard = [["ЛЁГКАЯ", "СРЕДНЯЯ", "ВЫСОКАЯ"]]
                await update.message.reply_text(
                    f"✅ Принято: {knives} единиц инструмента.\n\n"
                    "📊 *КАКОЙ ОБЪЁМ РАБОТЫ КУХНИ?*\n\n"
                    "Оцените среднюю ежедневную нагрузку:\n\n"
                    "• *ЛЁГКАЯ* — до 50 гостей (covers) в день\n"
                    "  (небольшие кафе, пекарни, завтраки)\n\n"
                    "• *СРЕДНЯЯ* — 50-150 гостей в день\n"
                    "  (рестораны с ужинами, бизнес-ланчи, семейные рестораны)\n\n"
                    "• *ВЫСОКАЯ* — от 150 гостей в день\n"
                    "  (сетевые рестораны, кейтеринг, фуд-холлы)",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                )
            except ValueError:
                await update.message.reply_text("Пожалуйста, введите число (например: 18).")
        
        elif step == "load":
            # Шаг 2: Нагрузка
            load = update.message.text.upper()
            
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
                keyboard = [["ЛЁГКАЯ", "СРЕДНЯЯ", "ВЫСОКАЯ"]]
                await update.message.reply_text(
                    "Пожалуйста, выберите вариант из клавиатуры:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                )
                return
            
            load_normalized = load_mapping[load]
            context.user_data["load"] = load_normalized
            context.user_data["step"] = "peaks"
            
            keyboard = [["ПОСТОЯННЫЙ РИТМ", "ПИК ВЫХОДНОГО ДНЯ", "МЕРОПРИЯТИЯ", "ВЫСОКИЙ ТЕМП"]]
            await update.message.reply_text(
                f"✅ Принято: {load_normalized} нагрузка.\n\n"
                "🚀 *КАКИЕ ПИКОВЫЕ НАГРУЗКИ БЫВАЮТ?*\n\n"
                "Как часто кухня работает на пределе возможностей:\n\n"
                "• *ПОСТОЯННЫЙ РИТМ* — график предсказуем, без резких всплесков\n"
                "• *ПИК ВЫХОДНОГО ДНЯ* — зависит от дня недели\n"
                "• *МЕРОПРИЯТИЯ* — банкеты, корпоративы с высокой нагрузкой\n"
                "• *ВЫСОКИЙ ТЕМП* — кухня постоянно в высоком темпе",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
        
        elif step == "peaks":
            # Шаг 3: Пиковые нагрузки
            peaks = update.message.text.upper()
            
            # Нормализуем возможные варианты написания
            peaks_mapping = {
                "ПОСТОЯННЫЙ РИТМ": "ПОСТОЯННЫЙ РИТМ",
                "ПИК ВЫХОДНОГО ДНЯ": "ПИК ВЫХОДНОГО ДНЯ",
                "МЕРОПРИЯТИЯ": "МЕРОПРИЯТИЯ",
                "ВЫСОКИЙ ТЕМП": "ВЫСОКИЙ ТЕМП",
                "РИТМ": "ПОСТОЯННЫЙ РИТМ",
                "ВЫХОДНЫЕ": "ПИК ВЫХОДНОГО ДНЯ",
                "ВЫХОДНОЙ": "ПИК ВЫХОДНОГО ДНЯ",
                "БАНКЕТЫ": "МЕРОПРИЯТИЯ",
                "КОРПОРАТИВЫ": "МЕРОПРИЯТИЯ",
                "МЕРОПРИЯТИЕ": "МЕРОПРИЯТИЯ",
                "ТЕМП": "ВЫСОКИЙ ТЕМП",
                "ПОСТОЯННО": "ВЫСОКИЙ ТЕМП"
            }
            
            if peaks not in peaks_mapping:
                keyboard = [["ПОСТОЯННЫЙ РИТМ", "ПИК ВЫХОДНОГО ДНЯ", "МЕРОПРИЯТИЯ", "ВЫСОКИЙ ТЕМП"]]
                await update.message.reply_text(
                    "Пожалуйста, выберите вариант из клавиатуры:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                )
                return
            
            peaks_normalized = peaks_mapping[peaks]
            context.user_data["peaks"] = peaks_normalized
            
            # Получаем все данные
            knives = context.user_data.get("knives", 0)
            load = context.user_data.get("load", "")
            
            # Рассчитываем пакет
            package, price, details = get_package_recommendation(knives, load, peaks_normalized)
            context.user_data["recommended_package"] = package
            context.user_data["recommended_price"] = price
            
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
                "Для точного расчёта и составления договора свяжитесь со мной:\n\n"
                f"📞 Телефон: +7 (951) 535-77-67\n"
                f"✉️ Telegram: [@{YOUR_TELEGRAM_USERNAME}](https://t.me/{YOUR_TELEGRAM_USERNAME})\n"
                f"📢 Канал: [@{YOUR_TELEGRAM_CHANNEL}](https://t.me/{YOUR_TELEGRAM_CHANNEL})"
            )
            
            # Создаём inline-кнопки
            keyboard = [
                [
                    InlineKeyboardButton(f"✅ Выбрать {package}", callback_data="select_package"),
                    InlineKeyboardButton("🔄 Начать заново", callback_data="restart")
                ],
                [
                    InlineKeyboardButton("✉️ Написать в личку", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}"),
                    InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{YOUR_TELEGRAM_CHANNEL}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # УДАЛЯЕМ КЛАВИАТУРУ ПРЕДЫДУЩЕГО ШАГА и отправляем новое сообщение
            await update.message.reply_text(
                response,
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove(),  # Удаляем старую Reply-клавиатуру
                disable_web_page_preview=True
            )
            
            # Отправляем отдельное сообщение с inline-кнопками
            await update.message.reply_text(
                "👇 *Выберите действие:*",
                parse_mode="Markdown",
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
            # Устанавливаем финальный шаг
            context.user_data["step"] = "completed"
        
        else:
            # Если шаг не распознан - начинаем заново
            await update.message.reply_text(
                "Начните заново: /start",
                reply_markup=ReplyKeyboardRemove()
            )
            context.user_data.clear()
    
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, начните заново: /start",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()

# Функция отправки уведомления владельцу - ВАРИАНТ С ПРАВИЛЬНЫМ MARKDOWN
async def send_notification_to_owner(context: ContextTypes.DEFAULT_TYPE, user_data: dict, user: dict):
    """Отправляет уведомление владельцу бота"""
    try:
        # Экранируем все пользовательские данные для безопасности Markdown
        first_name = str(user.get('first_name', '')).replace('*', '\\*').replace('_', '\\_')
        last_name = str(user.get('last_name', '')).replace('*', '\\*').replace('_', '\\_')
        username = f"@{user.get('username', 'нет')}" if user.get('username') else 'нет'
        
        # Экранируем данные кухни
        load = str(user_data.get('load', 'N/A')).replace('*', '\\*').replace('_', '\\_')
        peaks = str(user_data.get('peaks', 'N/A')).replace('*', '\\*').replace('_', '\\_')
        package = str(user_data.get('recommended_package', 'N/A')).replace('*', '\\*').replace('_', '\\_')
        price = str(user_data.get('recommended_price', 'N/A')).replace('*', '\\*').replace('_', '\\_')
        
        user_info = (
            f"👤 *НОВАЯ ЗАЯВКА ЧЕРЕЗ БОТА*\n\n"
            f"• Имя: {first_name} {last_name}\n"
            f"• Username: {username}\n"
            f"• ID: `{user.get('id', 'N/A')}`\n\n"
            f"*Параметры кухни:*\n"
            f"• Ножей: {user_data.get('knives', 'N/A')}\n"
            f"• Нагрузка: {load}\n"
            f"• Пики: {peaks}\n"
            f"• Рекомендованный пакет: {package}\n"
            f"• Стоимость: {price}\n\n"
            f"✅ *Пользователь выбрал пакет!*"
        )
        
        # Отправляем уведомление владельцу
        await context.bot.send_message(
            chat_id=YOUR_CHAT_ID,
            text=user_info,
            parse_mode="Markdown"
        )
        logger.info(f"✅ Уведомление отправлено владельцу {YOUR_CHAT_ID}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления владельцу: {e}")
        return False

# Обработка нажатия кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "select_package":
            # Собираем данные пользователя
            user = {
                'first_name': query.from_user.first_name or '',
                'last_name': query.from_user.last_name or '',
                'username': query.from_user.username or 'нет',
                'id': query.from_user.id
            }
            
            # Отправляем уведомление владельцу
            notification_sent = await send_notification_to_owner(context, context.user_data, user)
            
            # Подтверждаем пользователю
            if notification_sent:
                response_text = (
                    "✅ *Отлично! Я уже направил уведомление о Вашем выборе!*\n\n"
                    "Мы свяжемся с Вами в рабочее время (Пн-Пт 9:00-18:00).\n\n"
                    "📞 *Тимофей Борздов* — руководитель сервиса «Грань»\n"
                    "Связаться можно:\n\n"
                    f"📞 Телефон: +7 (951) 535-77-67\n"
                    f"✉️ Telegram: @{YOUR_TELEGRAM_USERNAME}\n"
                    f"📢 Канал: @{YOUR_TELEGRAM_CHANNEL}\n\n"
                    "Сайт: granservice.pro"
                )
            else:
                response_text = (
                    "✅ *Ваш выбор сохранен!*\n\n"
                    "⚠️ *Техническая неполадка:* уведомление не отправлено автоматически.\n"
                    "Пожалуйста, свяжитесь со мной напрямую:\n\n"
                    f"📞 Телефон: +7 (951) 535-77-67\n"
                    f"✉️ Telegram: @{YOUR_TELEGRAM_USERNAME}\n"
                    f"📢 Канал: @{YOUR_TELEGRAM_CHANNEL}\n\n"
                    "Сайт: granservice.pro"
                )
            
            # Создаем кнопки
            keyboard = [
                [
                    InlineKeyboardButton("✉️ Написать в личку", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}"),
                    InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{YOUR_TELEGRAM_CHANNEL}")
                ]
            ]
            
            await query.edit_message_text(
                response_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            
            # Очищаем данные после завершения
            context.user_data.clear()
        
        elif query.data == "restart":
            # Очищаем данные и отправляем инструкцию
            context.user_data.clear()
            await query.edit_message_text(
                "Диалог сброшен. Напишите /start, чтобы начать заново.",
                reply_markup=ReplyKeyboardRemove()
            )
    
    except Exception as e:
        logger.error(f"Ошибка в button_handler: {e}", exc_info=True)
        await query.edit_message_text(
            "Произошла ошибка. Пожалуйста, начните заново: /start",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()

# Команда для теста уведомлений
async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда для проверки уведомлений"""
    try:
        # Отправляем тестовое уведомление
        await context.bot.send_message(
            chat_id=YOUR_CHAT_ID,
            text="✅ *ТЕСТОВОЕ УВЕДОМЛЕНИЕ*\n\n"
                 "Это тестовое сообщение из бота.\n"
                 "Если вы видите это - уведомления работают правильно!",
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(
            "✅ Тестовое уведомление отправлено!\n"
            "Проверьте, пришло ли оно вам в личные сообщения."
        )
    except Exception as e:
        error_msg = str(e)
        await update.message.reply_text(
            f"❌ Ошибка отправки тестового уведомления:\n\n"
            f"`{error_msg[:200]}`\n\n"
            f"Возможные причины:\n"
            f"1. ID {YOUR_CHAT_ID} неверный\n"
            f"2. Бот заблокирован вами\n"
            f"3. Бот никогда не писал вам в личку\n\n"
            f"📌 Решение:\n"
            f"1. Напишите боту что-нибудь в личку\n"
            f"2. Разблокируйте бота, если заблокировали\n"
            f"3. Проверьте ID через @userinfobot",
            parse_mode="Markdown"
        )

# Команда /reset для принудительного сброса
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "✅ Все данные сброшены. Начните заново: /start",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка в обработке обновления: {context.error}", exc_info=True)
    try:
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, начните заново: /start",
            reply_markup=ReplyKeyboardRemove()
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

def run_http_server():
    """Запускает HTTP-сервер для Render"""
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"✅ HTTP-сервер запущен на порту {port}")
    server.serve_forever()

def main():
    """Главная функция"""
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
    app.add_handler(CommandHandler("test", test))  # Тест уведомлений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик ошибок
    app.add_error_handler(error_handler)
    
    print("=" * 50)
    print("🤖 Бот запущен и готов к работе!")
    print(f"📱 ID для уведомлений: {YOUR_CHAT_ID}")
    print(f"💬 Username для лички: @{YOUR_TELEGRAM_USERNAME}")
    print(f"📢 Канал: @{YOUR_TELEGRAM_CHANNEL}")
    print("=" * 50)
    print("\n📌 Команды для проверки:")
    print("/test - проверить уведомления")
    print("/reset - сбросить данные")
    print("/start - начать диалог")
    print("=" * 50)
    
    # Запускаем бота
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import logging
import os
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from datetime import datetime
import threading

# Загружаем переменные окружения
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для запросов с сайта

# ID администраторов
ADMIN_IDS = [1652676928, 327895912]

# Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Путь к файлу для сохранения заявок с сайта
SITE_LEADS_FILE = os.path.join("data", "site_leads.txt")

def send_telegram_notification(report, now, name, phone, service_type):
    """Отправка уведомления в Telegram (синхронная обертка)"""
    async def _send():
        # Отправляем уведомление всем админам
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, report)
                logger.info(f"Заявка отправлена админу {admin_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки админу {admin_id}: {e}")

        # Закрываем сессию бота
        await bot.session.close()

    # Запускаем в новом event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_send())
    finally:
        loop.close()

@app.route('/api/submit-form', methods=['POST'])
def submit_form():
    """Обработка заявки с сайта"""
    try:
        data = request.get_json()

        # Получаем данные из формы
        name = data.get('name', 'Не указано')
        phone = data.get('phone', 'Не указано')
        service_type = data.get('type', 'Не указано')

        # Текущее время
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Формируем сообщение для админов
        report = (
            f"🌐 <b>НОВАЯ ЗАЯВКА С САЙТА!</b>\n\n"
            f"📅 <b>Дата:</b> {now}\n"
            f"👤 <b>Имя:</b> {name}\n"
            f"📞 <b>Телефон:</b> {phone}\n"
            f"🏠 <b>Тип услуги:</b> {service_type}\n\n"
            f"💡 <i>Источник: Лендинг</i>"
        )

        # Отправляем уведомление в отдельном потоке
        thread = threading.Thread(
            target=send_telegram_notification,
            args=(report, now, name, phone, service_type)
        )
        thread.start()

        # Сохраняем заявку в файл
        try:
            os.makedirs("data", exist_ok=True)
            with open(SITE_LEADS_FILE, "a", encoding="utf-8") as f:
                f.write(f"{now} | {name} | {phone} | {service_type}\n")
        except Exception as e:
            logger.error(f"Ошибка записи в файл: {e}")

        return jsonify({
            "success": True,
            "message": "Заявка успешно отправлена!"
        }), 200

    except Exception as e:
        logger.error(f"Ошибка обработки заявки: {e}")
        return jsonify({
            "success": False,
            "message": "Произошла ошибка при отправке заявки"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервера"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Запускаем сервер на порту 5000
    app.run(host='0.0.0.0', port=5000, debug=False)

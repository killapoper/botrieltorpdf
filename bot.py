import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в .env")
    exit(1)

bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ID или юзернейм канала для проверки подписки
CHANNEL_ID = "@metrdlyasebya"
# Список администраторов из .env
allowed_ids_raw = os.getenv("ALLOWED_USER_IDS", "1652676928")
ADMIN_IDS = [int(i.strip()) for i in allowed_ids_raw.split(",")]

async def check_subscription(user_id: int) -> bool:
    """Проверяет, подписан ли пользователь на канал."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Статусы 'member', 'administrator', 'creator' означают, что пользователь в канале
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        # Если бот не админ в канале, проверка может не работать
        return True # В случае ошибки пропускаем, чтобы не блокировать бота совсем

# Создание папки для данных, если она не существует (для докера)
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Пути к файлам
PDF_FILENAME = os.path.join(DATA_DIR, "presentation.pdf")
USERS_FILE = os.path.join(DATA_DIR, "users.txt")
LEADS_FILE = os.path.join(DATA_DIR, "leads.txt")
SITE_LEADS_FILE = os.path.join(DATA_DIR, "site_leads.txt")

def trim_file(filename: str, max_lines: int = 1000):
    """Обрезает файл, оставляя только последние max_lines строк."""
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > max_lines:
                with open(filename, "w", encoding="utf-8") as f:
                    f.writelines(lines[-max_lines:])
    except Exception as e:
        logger.error(f"Ошибка при очистке файла {filename}: {e}")

# Создание заглушки PDF файла, если он не существует
PDF_FILENAME = "presentation.pdf"
def create_dummy_pdf():
    if not os.path.exists(PDF_FILENAME):
        dummy_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 0 >>\nstream\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000213 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n264\n%%EOF"
        with open(PDF_FILENAME, "wb") as f:
            f.write(dummy_pdf_content)
        logger.info(f"Создан файл-заглушка {PDF_FILENAME}")

# FSM Состояния
class QuizStates(StatesGroup):
    q1_rooms = State()
    q2_purpose = State()
    q3_downpayment = State()
    q4_timeline = State()
    q5_contact_method = State()
    q6_phone = State()

class AdminStates(StatesGroup):
    waiting_for_pdf = State()

# Словарь для расшифровки ответов квиза
ANSWERS_MAP = {
    # Q1: Комнаты
    "q1_studio": "Студия",
    "q1_1room": "1-комнатная",
    "q1_2room": "2-комнатная",
    "q1_3plus": "3+ комнатная",
    # Q2: Цель
    "q2_self": "Для себя",
    "q2_invest": "Для инвестиций",
    "q2_relatives": "Для родственников",
    # Q3: Первый взнос
    "q3_0percent": "Без первоначального взноса",
    "q3_1_2m": "1 000 000 - 2 000 000 руб.",
    "q3_2_3m": "2 000 000 - 3 000 000 руб.",
    "q3_3m_plus": "3 000 000 руб. и более",
    "q3_100percent": "100%-я оплата",
    # Q4: Сроки
    "q4_asap": "Как найдем вариант",
    "q4_just_looking": "Просто интересуюсь",
    "q4_money_ready": "Как будут деньги на руках",
    # Контакты
    "contact_telegram": "Telegram",
    "contact_phone": "Телефон"
}

# --- КЛАВИАТУРЫ ---
def get_q1_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Студия", callback_data="q1_studio")],
        [InlineKeyboardButton(text="1-комнатная", callback_data="q1_1room")],
        [InlineKeyboardButton(text="2-комнатная", callback_data="q1_2room")],
        [InlineKeyboardButton(text="3+ комнатная", callback_data="q1_3plus")]
    ])

def get_q2_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Для себя", callback_data="q2_self")],
        [InlineKeyboardButton(text="Для инвестиций", callback_data="q2_invest")],
        [InlineKeyboardButton(text="Для родственников", callback_data="q2_relatives")]
    ])

def get_q3_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Без первоначального взноса", callback_data="q3_0percent")],
        [InlineKeyboardButton(text="1 000 000 - 2 000 000 руб.", callback_data="q3_1_2m")],
        [InlineKeyboardButton(text="2 000 000 - 3 000 000 руб.", callback_data="q3_2_3m")],
        [InlineKeyboardButton(text="3 000 000 руб. и более", callback_data="q3_3m_plus")],
        [InlineKeyboardButton(text="100%-я оплата", callback_data="q3_100percent")]
    ])

def get_q4_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Как найдем вариант", callback_data="q4_asap")],
        [InlineKeyboardButton(text="Просто интересуюсь", callback_data="q4_just_looking")],
        [InlineKeyboardButton(text="Как будут деньги на руках", callback_data="q4_money_ready")]
    ])

def get_contact_method_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Telegram", callback_data="contact_telegram")],
        [InlineKeyboardButton(text="Связь по телефону", callback_data="contact_phone")]
    ])

def get_phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить свой контакт", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📋 Заявки из бота", callback_data="admin_leads")],
        [InlineKeyboardButton(text="🌐 Заявки с сайта", callback_data="admin_site_leads")],
        [InlineKeyboardButton(text="🔄 Обновить PDF", callback_data="admin_update_pdf")]
    ])

# --- ОБРАБОТЧИКИ ---

@dp.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery, state: FSMContext) -> None:
    if await check_subscription(callback.from_user.id):
        await callback.message.delete()
        # Снова вызываем приветствие, передавая данные того, кто нажал на кнопку
        await start_quiz_flow(callback.message, callback.from_user, state)
    else:
        await callback.answer("Вы еще не подписались на канал! ❌", show_alert=True)

async def start_quiz_flow(message: Message, user, state: FSMContext) -> None:
    """Общая логика начала квиза (используется и в /start, и в кнопке проверки)."""
    text = (
        "Здравствуйте! Благодарю вас за подписку на мой телеграм-канал!\n\n"
        "Я помогу вам найти квартиру мечты в Санкт-Петербурге. У меня есть много предложений, в том числе <b>варианты без первоначального взноса</b>.\n\n"
        "Чтобы получить индивидуальную подборку объектов под вашу ситуацию, ответьте на 4 вопроса "
        "и заберите файл, который подойдет именно вам 🤗\n\n"
        "<b>Сколько комнат вы рассматриваете? (1/4)</b>"
    )
    await message.answer(text, reply_markup=get_q1_keyboard())
    await state.set_state(QuizStates.q1_rooms)

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    
    # Сохраняем пользователя в базу для статистики (users.txt)
    try:
        user_id = str(message.from_user.id)
        users = []
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = f.read().splitlines()
        
        if user_id not in users:
            with open(USERS_FILE, "a", encoding="utf-8") as f:
                f.write(user_id + "\n")
            trim_file(USERS_FILE) # Чистим, если превышен лимит
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя: {e}")

    if not await check_subscription(message.from_user.id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
            [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
        ])
        await message.answer(
            f"Для использования бота необходимо подписаться на мой канал {CHANNEL_ID} \n\n"
            "После подписки нажмите кнопку ниже:",
            reply_markup=keyboard
        )
        return

    await start_quiz_flow(message, message.from_user, state)

@dp.callback_query(QuizStates.q1_rooms, F.data.startswith("q1_"))
async def process_q1(callback: CallbackQuery, state: FSMContext) -> None:
    # Сохраняем ответ пользователя в состояние (по желанию)
    await state.update_data(q1_rooms=callback.data)
    
    text = (
        "Цель покупки напрямую определяет параметры поиска, "
        "по которым я делаю отбор лучших вариантов для вас.\n\n"
        "<b>Поэтому поделитесь, для чего планируется покупка (2/4)</b>"
    )
    
    # Удаляем предыдущее сообщение с кнопками
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=get_q2_keyboard())
    await state.set_state(QuizStates.q2_purpose)
    await callback.answer()

@dp.callback_query(QuizStates.q2_purpose, F.data.startswith("q2_"))
async def process_q2(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(q2_purpose=callback.data)
    
    # Получаем данные о комнатах, чтобы подставить цену
    data = await state.get_data()
    rooms_choice = data.get("q1_rooms", "q1_1room")
    
    prices = {
        "q1_studio": "от 3,5 млн руб.",
        "q1_1room": "от 4,5 млн руб.",
        "q1_2room": "от 5,8 млн руб.",
        "q1_3plus": "от 7,5 млн руб."
    }
    
    price_text = prices.get(rooms_choice, "от 5,5 млн руб.")
    
    text = (
        f"Цены на выбранный вами тип жилья в СПб начинаются {price_text} в зависимости от расположения и класса ЖК.\n\n"
        "Обычно первый взнос по ипотеке составляет 20%, но сейчас есть много программ со взносом от 10%, а также <b>варианты совсем без первоначального взноса</b>.\n\n"
        "<b>Какой комфортный первый взнос для вас? (3/4)</b>"
    )
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=get_q3_keyboard())
    await state.set_state(QuizStates.q3_downpayment)
    await callback.answer()

@dp.callback_query(QuizStates.q3_downpayment, F.data.startswith("q3_"))
async def process_q3(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(q3_downpayment=callback.data)
    
    text = (
        "Условия продаж и цены на квартиры меняются каждый месяц, "
        "поэтому важно понимать, <b>когда Вы планируете покупку?(4/4)</b>"
    )
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=get_q4_keyboard())
    await state.set_state(QuizStates.q4_timeline)
    await callback.answer()

@dp.callback_query(QuizStates.q4_timeline, F.data.startswith("q4_"))
async def process_q4(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(q4_timeline=callback.data)
    
    text = (
        "Ваш персональный PDF-каталог готов! 🔥\n\n"
        "Выберите, где вам удобнее получить файл и мою консультацию по этим объектам. Я сразу пришлю подборку сюда, а затем свяжусь с вами, чтобы обсудить детали:"
    )
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=get_contact_method_keyboard())
    await state.set_state(QuizStates.q5_contact_method)
    await callback.answer()

@dp.callback_query(QuizStates.q5_contact_method, F.data.startswith("contact_"))
async def process_contact_method(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(contact_method=callback.data)
    
    if callback.data == "contact_telegram":
        # Если выбрали Телеграм, не просим номер, а сразу финализируем
        await callback.message.delete()
        await callback.message.answer("Принято! Ловите вашу подборку. Я изучу ваш запрос подробнее и напишу вам в Telegram в ближайшее время, чтобы ответить на все вопросы.")
        
        # Вызываем функцию завершения (отправка PDF), передавая пользователя
        await finalize_quiz(callback.message, callback.from_user, state)
    else:
        # Если выбрали телефон, просим номер
        text = (
            "Хорошо! Оставьте ваш номер телефона — я сразу пришлю файл сюда, а позже перезвоню, чтобы рассказать подробности по выбранным объектам."
        )
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=get_phone_keyboard())
        await state.set_state(QuizStates.q6_phone)
    
    await callback.answer()

@dp.message(QuizStates.q6_phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    # Записываем телефон
    phone = ""
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()

    await state.update_data(phone=phone)
    await finalize_quiz(message, message.from_user, state)

async def finalize_quiz(message: Message, user, state: FSMContext) -> None:
    """Финальный этап: отправка PDF, уведомление админа и запись в файл."""
    user_data = await state.get_data()
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Отправляем PDF пользователю
    await message.answer("Ваша индивидуальная подборка готова ⬇️", reply_markup=ReplyKeyboardRemove())
    
    try:
        pdf_file = FSInputFile(PDF_FILENAME)
        await message.answer_document(
            document=pdf_file,
            caption="Вот PDF-подборка объектов из 350+ ЖК по вашему запросу."
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке PDF: {e}")
        await message.answer("К сожалению, произошла ошибка при отправке файла.")

    # Подготовка данных для отчета
    contact_info = user_data.get('phone', 'Не указан (выбран Telegram)')
    method = ANSWERS_MAP.get(user_data.get('contact_method'), 'Не выбран')
    username = f"@{user.username}" if user.username else "нет юзернейма"
    
    q1 = ANSWERS_MAP.get(user_data.get('q1_rooms'), '—')
    q2 = ANSWERS_MAP.get(user_data.get('q2_purpose'), '—')
    q3 = ANSWERS_MAP.get(user_data.get('q3_downpayment'), '—')
    q4 = ANSWERS_MAP.get(user_data.get('q4_timeline'), '—')

    report = (
        f"📅 <b>Дата:</b> {now}\n"
        f"👤 <b>Имя:</b> {user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"📱 <b>Username:</b> {username}\n"
        f"📞 <b>Способ связи:</b> {method}\n"
        f"☎️ <b>Контакт:</b> {contact_info}\n\n"
        f"📊 <b>ОТВЕТЫ КЛИЕНТА:</b>\n"
        f"1️⃣ <b>Комнат:</b> {q1}\n"
        f"2️⃣ <b>Цель:</b> {q2}\n"
        f"3️⃣ <b>Взнос:</b> {q3}\n"
        f"4️⃣ <b>Сроки:</b> {q4}\n"
    )

    # 1. Отправка админам
    try:
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, f"🚀 <b>НОВЫЙ ЛИД!</b>\n\n{report}")
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Ошибка при уведомлении админов: {e}")

    # 2. Запись в файл leads.txt (каждый пук записан)
    try:
        with open(LEADS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{now} | {user.id} | {username} | {contact_info} | {q1}/{q2}/{q3}/{q4}\n")
        trim_file(LEADS_FILE) # Чистим старые заявки, если их слишком много
    except Exception as e:
        logger.error(f"Ошибка при записи в файл: {e}")

    await state.clear()

async def main() -> None:
    create_dummy_pdf()
    logger.info("Квиз-бот запущен!")
    await dp.start_polling(bot)

# --- АДМИН-ПАНЕЛЬ ---

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🛠 <b>Панель администратора</b>\nВыберите действие:", reply_markup=get_admin_keyboard())

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return

    total_users = 0
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            total_users = len(f.read().splitlines())

    total_leads = 0
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            total_leads = len(f.read().splitlines())

    total_site_leads = 0
    if os.path.exists(SITE_LEADS_FILE):
        with open(SITE_LEADS_FILE, "r", encoding="utf-8") as f:
            total_site_leads = len(f.read().splitlines())

    text = (
        "📈 <b>Аналитика бота</b>\n\n"
        f"👥 Всего пользователей (открыли бота): {total_users}\n"
        f"📝 Заявок из бота (прошли квиз): {total_leads}\n"
        f"🌐 Заявок с сайта: {total_site_leads}\n"
        f"📊 Всего заявок: {total_leads + total_site_leads}\n"
        f"🎯 Конверсия бота: {round(total_leads/total_users*100, 1) if total_users > 0 else 0}%"
    )
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "admin_leads")
async def admin_leads(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return

    if not os.path.exists(LEADS_FILE):
        await callback.message.answer("Заявок из бота пока нет.")
        return

    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()[-10:] # Берем последние 10

    text = "📋 <b>Последние 10 заявок из бота:</b>\n\n" + "".join(lines)
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "admin_site_leads")
async def admin_site_leads(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return

    if not os.path.exists(SITE_LEADS_FILE):
        await callback.message.answer("Заявок с сайта пока нет.")
        return

    with open(SITE_LEADS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()[-10:] # Берем последние 10

    text = "🌐 <b>Последние 10 заявок с сайта:</b>\n\n" + "".join(lines)
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(F.data == "admin_update_pdf")
async def admin_update_pdf_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS: return
    await callback.message.answer("📤 Пожалуйста, отправьте новый PDF-файл. Он автоматически заменит текущий файл презентации.")
    await state.set_state(AdminStates.waiting_for_pdf)
    await callback.answer()

@dp.message(AdminStates.waiting_for_pdf, F.document)
async def process_new_pdf(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    
    if not message.document.file_name.lower().endswith(".pdf"):
        await message.answer("❌ Это не PDF-файл. Попробуйте еще раз.")
        return
        
    file_info = await bot.get_file(message.document.file_id)
    await bot.download_file(file_info.file_path, PDF_FILENAME)
    
    await message.answer(f"✅ Файл <b>{PDF_FILENAME}</b> успешно обновлен!")
    await state.clear()

if __name__ == "__main__":
    asyncio.run(main())

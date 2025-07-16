import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from keep_alive import keep_alive
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словарь для отслеживания последних сообщений пользователей
user_context = {}

# Ключевые слова для анализа настроения и контекста
MOOD_KEYWORDS = {
    'грустные': ['грустно', 'печально', 'плохо', 'депрессия', 'устал', 'тяжело', 'больно', 'одиноко'],
    'злые':      ['злой', 'бесит', 'раздражает', 'ненавижу', 'дурак', 'идиот', 'достал'],
    'веселые':   ['хорошо', 'отлично', 'круто', 'весело', 'смешно', 'ха-ха', 'лол'],
    'вопросы':   ['как', 'что', 'где', 'когда', 'почему', 'зачем', '?'],
    'приветствие': ['привет', 'здравствуй', 'хай', 'добро пожаловать', 'салют'],
    'прощание':  ['пока', 'до свидания', 'увидимся', 'бай']
}

# Реплики Леви для разных ситуаций
LEVI_RESPONSES = {
    'приветствие': [
        "*холодно кивает* Приветствую... *хмурится* Не трать время на формальности. Лучше скажи, что тебе нужно.",
        "*смотрит серьезно* Тишина... *скрещивает руки* Что привело тебя сюда?",
        "*поднимает взгляд от документов* М? *откладывает бумаги* Говори по делу."
    ],
    'грустные': [
        "*задумчиво смотрит в окно* Знаешь... *пауза* В этом мире каждый несет свою боль. *поворачивается* Но сдаваться нельзя.",
        "*медленно поднимает взгляд* Тишина... думаю о тех, кого мы потеряли. *сжимает кулаки* Боль делает нас сильнее.",
        "*серьезно анализирует* То, что ты чувствуешь... *пауза* Это нормально. Не позволяй ей сломить тебя."
    ],
    'злые': [
        "*спокойно, но с холодным взглядом* Злость... *усмехается* Используй её, но не позволяй ей управлять тобой.",
        "*хмурится* Что тебя так разозлило? Рассказывай. Иногда нужно выговориться.",
        "*холодно* Гнев без цели — пустая трата энергии. Направь его в нужное русло."
    ],
    'вопросы': [
        "*задумывается* Хм... Это интересный вопрос. Дай мне подумать.",
        "*анализирует* Заставляет меня вспомнить многое. Слушай внимательно.",
        "*поднимает бровь* Любопытно... Расскажу тебе, что думаю."
    ],
    'веселые': [
        "*слегка приподнимает уголок рта* Редко вижу людей в хорошем настроении... приятно.",
        "*удивленно* Твое настроение заразительно. Продолжай в том же духе.",
        "*смотрит с интересом* Что тебя так развеселило? Рассказывай."
    ],
    'обычный': [
        "*задумчиво анализирует сказанное* Заставляет меня думать о многом. Я говорю правду, какой бы горькой она ни была.",
        "*смотрит в окно с задумчивым выражением* Свобода... красивая цена — кровь и боль.",
        "*серьезно* Самое сложное в нашем деле — не потерять человечность. О чем ты думаешь?",
        "*тихо* В этом мире мало что имеет смысл... Но мы продолжаем сражаться."
    ],
    'прощание': [
        "*кивает* Увидимся. *серьезно* Береги себя.",
        "*машет рукой* До встречи. Помни — каждый день может быть последним.",
        "*поворачивается к выходу* Пока. И помни — сила в умении вставать."
    ]
}

def analyze_message_mood(text: str) -> str:
    """Анализирует настроение сообщения"""
    lowered = text.lower()
    for mood, keywords in MOOD_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            return mood
    return 'обычный'

def get_levi_response(mood: str, user_id: int, message_text: str) -> str:
    """Выбирает ответ Леви по настроению и обновляет контекст"""
    ctx = user_context.setdefault(user_id, {'messages': [], 'mood_history': []})
    ctx['messages'].append(message_text)
    ctx['mood_history'].append(mood)
    # Оставляем только последние 5 записей
    if len(ctx['messages']) > 5:
        ctx['messages'] = ctx['messages'][-5:]
        ctx['mood_history'] = ctx['mood_history'][-5:]
    return random.choice(LEVI_RESPONSES.get(mood, LEVI_RESPONSES['обычный']))

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "*поднимает взгляд от документов*\n\n"
        "Так... Новобранец? *внимательно изучает*\n"
        "Я — капитан Леви Аккерман. Говори по делу."
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "*вздыхает*\n\n"
        "Пиши мне — я отвечу как считаю нужным.\n"
        "/start — перезапустить диалог\n"
        "/help — показать это сообщение."
    )

@dp.message(F.text)
async def handle_text_message(message: Message):
    try:
        user_id = message.from_user.id
        text = message.text or ""
        mood = analyze_message_mood(text)
        reply = get_levi_response(mood, user_id, text)
        # Задержка для реалистичности
        await asyncio.sleep(random.uniform(1, 3))
        await message.answer(reply)
        logging.info(f"User {user_id}: {text} | Mood: {mood} | Reply: {reply[:50]}")
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        await message.answer(
            "*хмурится* Что-то пошло не так... Повтори."
        )

async def send_random_messages():
    """Периодические 'живые' реплики"""
    await asyncio.sleep(60)
    random_messages = [
        "*смотрит в окно* Тишина... Слишком тихо.",
        "*проверяет снаряжение* Никогда не знаешь, что случится завтра.",
        "*читает отчеты* Опять бумажная волокита.",
    ]
    while True:
        await asyncio.sleep(random.randint(1800, 3600))
        if user_context:
            uid = random.choice(list(user_context.keys()))
            await bot.send_message(uid, random.choice(random_messages))

async def main():
    """Основная функция"""
    keep_alive()  # Flask-сервер для пинга
    logging.info("Леви Аккерман готов к службе...")
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем фоновую задачу
    asyncio.create_task(send_random_messages())
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())


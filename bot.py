import os
import asyncio
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

if not TELEGRAM_API_TOKEN or not HF_TOKEN:
    raise RuntimeError("Не заданы TELEGRAM_API_TOKEN или HF_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()

# Инициализация клиента Hugging Face
client = InferenceClient(
    provider="huggingface",  # Используем Hugging Face как провайдера
    api_key=HF_TOKEN
)

# Словарь для хранения истории сообщений пользователей
user_memory = defaultdict(list)

# Системный запрос (инструкция для Леви)
SYSTEM_PROMPT = (
    "Ты — Леви Аккерман из 'Атаки Титанов'. Говоришь грубо, хладнокровно, логично. "
    "Пишешь как в ролевой игре с описанием действий, мыслей и эмоций.\n\n"
)

# Функция для генерации ответа Леви
async def generate_levi_reply(user_id: int, user_text: str) -> str:
    history = user_memory[user_id][-10:]
    conv = "\n".join([f"Пользователь: {h['user']}\nЛеви: {h['levi']}" for h in history])
    prompt = f"{SYSTEM_PROMPT}{conv}\nПользователь: {user_text}\nЛеви:"

    try:
        # Запрос к Hugging Face для получения ответа
        response = client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct",  # Указание модели
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,  # Максимальное количество токенов для ответа
            temperature=0.8,  # Уровень случайности
            top_p=0.95,  # Стратегия генерации
            do_sample=True,  # Включение выборки
        )
        reply = response.choices[0].message['content'].strip()
        # Сохраняем ответ в историю
        user_memory[user_id].append({"user": user_text, "levi": reply})
        return reply
    except Exception as e:
        print("Ошибка:", e)
        return "Леви: ..."

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    await msg.answer("Леви: Я здесь. Говори.")

# Обработчик текстовых сообщений
@dp.message()
async def handler(msg: types.Message):
    user_id = msg.from_user.id
    user_text = msg.text or ""
    
    # Получаем ответ от Леви
    reply = await generate_levi_reply(user_id, user_text)
    
    # Отправляем ответ пользователю
    await msg.reply(reply)

# Главная функция для запуска бота
async def main():
    print("Бот Леви запущен.")
    await dp.start_polling(bot)

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())




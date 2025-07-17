import os
import asyncio
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import asyncpg

# Загружаем переменные окружения из .env (если он есть)
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TELEGRAM_API_TOKEN or not HF_TOKEN or not DATABASE_URL:
    raise RuntimeError("Нужны TELEGRAM_API_TOKEN, HF_TOKEN и DATABASE_URL")

bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()

client = InferenceClient(
    provider="together",  # Используем Together для Kimi модели
    api_key=HF_TOKEN,
)

user_memory = defaultdict(list)

SYSTEM_PROMPT = (
    "Ты — Леви Аккерман из 'Атаки Титанов'. Говоришь грубо, хладнокровно, логично. "
    "Пишешь как в ролевой игре с описанием действий, мыслей и эмоций.\n\n"
)

# Асинхронное подключение к базе данных
async def get_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print("Ошибка подключения к БД:", e)
        return None

# Сохраняем сообщения в базу данных
async def save_message(user_id: int, user_msg: str, levi_reply: str):
    conn = await get_db()
    if not conn:
        print("Соединение с БД не установлено.")
        return
    try:
        await conn.execute(
            "INSERT INTO messages (user_id, user_msg, levi_reply) VALUES ($1, $2, $3)",
            user_id, user_msg, levi_reply
        )
    except Exception as e:
        print("Ошибка записи в БД:", e)
    finally:
        await conn.close()

async def generate_levi_reply(user_id: int, user_text: str) -> str:
    history = user_memory[user_id][-10:]
    conv = "\n".join([f"Пользователь: {h['user']}\nЛеви: {h['levi']}" for h in history])
    prompt = f"{SYSTEM_PROMPT}{conv}\nПользователь: {user_text}\nЛеви:"

    try:
        response = client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.8,
            top_p=0.95
        )
        reply = response.choices[0].message["content"].strip()
        user_memory[user_id].append({"user": user_text, "levi": reply})
        await save_message(user_id, user_text, reply)
        return reply
    except Exception as e:
        print("Ошибка генерации:", e)
        return "Леви: ..."

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    await msg.answer("Леви: Я здесь. Говори.")

@dp.message()
async def handler(msg: types.Message):
    user_id = msg.from_user.id
    user_text = msg.text or ""
    reply = await generate_levi_reply(user_id, user_text)
    await msg.reply(reply)

async def main():
    print("Бот Леви запущен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())





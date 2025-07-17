import os
import asyncio
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import asyncpg

load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TELEGRAM_API_TOKEN or not HF_TOKEN or not DATABASE_URL:
    raise RuntimeError("Нужны TELEGRAM_API_TOKEN, HF_TOKEN и DATABASE_URL")

bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()

client = InferenceClient(
    provider="together",  # Важно: используем Together для Kimi модели
    api_key=HF_TOKEN,
)

user_memory = defaultdict(list)

SYSTEM_PROMPT = (
    "Ты — Леви Аккерман из 'Атаки Титанов'. Говоришь грубо, хладнокровно, логично. "
    "Пишешь как в ролевой игре с описанием действий, мыслей и эмоций.\n\n"
)

# Подключение к базе данных
async def get_db():
    return await asyncpg.connect(DATABASE_URL)

# Сохраняем сообщения в базу данных
async def save_message(user_id: int, user_msg: str, levi_reply: str):
    try:
        conn = await get_db()
        await conn.execute(
            "INSERT INTO messages (user_id, user_msg, levi_reply) VALUES ($1, $2, $3)",
            user_id, user_msg, levi_reply
        )
        await conn.close()
    except Exception as e:
        print("DB Error:", e)

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





import os
import asyncio
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from huggingface_hub import InferenceClient
import asyncpg
from dotenv import load_dotenv
import logging

# Загрузка переменных из .env
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TELEGRAM_API_TOKEN or not HF_TOKEN or not DATABASE_URL:
    raise RuntimeError("Не заданы TELEGRAM_API_TOKEN, HF_TOKEN или DATABASE_URL")

bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()
client = InferenceClient(token=HF_TOKEN)
user_memory = defaultdict(list)

logging.basicConfig(level=logging.INFO)

SYSTEM_PROMPT = (
    "Ты — Леви Аккерман из 'Атаки Титанов'. Говоришь грубо, хладнокровно, логично. "
    "Пишешь как в ролевой игре с описанием действий, мыслей и эмоций.\n\n"
)

# Асинхронное подключение к PostgreSQL
async def get_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

# Пример асинхронного запроса для сохранения сообщений пользователя в базе данных
async def save_user_message(pool, user_id, message):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO user_messages (user_id, message) VALUES ($1, $2)", user_id, message
        )

async def generate_levi_reply(user_id: int, user_text: str, pool) -> str:
    history = user_memory[user_id][-10:]
    conv = "\n".join([f"Пользователь: {h['user']}\nЛеви: {h['levi']}" for h in history])
    prompt = f"{SYSTEM_PROMPT}{conv}\nПользователь: {user_text}\nЛеви:"

    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: client.text_generation(
                prompt,
                model="tiiuae/falcon-7b-instruct",
                max_new_tokens=500,
                temperature=0.8,
                top_p=0.95,
                do_sample=True,
            )
        )
        reply = resp.strip().split("Пользователь:")[0].strip()
        user_memory[user_id].append({"user": user_text, "levi": reply})
        await save_user_message(pool, user_id, user_text)
        return reply
    except Exception as e:
        logging.exception("Ошибка в generate_levi_reply")
        return "Леви: ..."

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    await msg.answer("Леви: Я здесь. Говори.")

@dp.message()
async def handler(msg: types.Message):
    txt = msg.text or ""
    if not txt.strip():
        await msg.reply("Пожалуйста, напиши текст.")
        return
    try:
        pool = await get_db_pool()
        reply = await generate_levi_reply(msg.from_user.id, txt, pool)
        await msg.reply(reply)
        await pool.close()
    except Exception as e:
        logging.exception("Ошибка в handler")
        await msg.reply("Произошла ошибка. Попробуйте еще раз.")

async def main():
    print("Бот Леви запущен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



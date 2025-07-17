import os
import asyncio
import random
import logging
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from huggingface_hub import InferenceClient
import psycopg2
from dotenv import load_dotenv

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

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def save_user_message(user_id, message):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO user_messages (user_id, message) VALUES (%s, %s)", (user_id, message))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка при сохранении сообщения в БД: {e}")

SYSTEM_PROMPT = (
    "Ты — Леви Аккерман из 'Атаки Титанов'. Говоришь грубо, хладнокровно, логично. "
    "Пишешь как в ролевой игре с описанием действий, мыслей и эмоций.\n\n"
)

async def generate_levi_reply(user_id: int, user_text: str) -> str:
    history = user_memory[user_id][-10:]
    conv = "\n".join([f"Пользователь: {h['user']}\nЛеви: {h['levi']}" for h in history])
    prompt = f"{SYSTEM_PROMPT}{conv}\nПользователь: {user_text}\nЛеви:"

    try:
        # Используем асинхронный вызов, если поддерживается
        resp = await asyncio.to_thread(
            client.text_generation,
            prompt,
            model="tiiuae/falcon-7b-instruct",
            max_new_tokens=500,
            temperature=0.8,
            top_p=0.95,
            do_sample=True,
        )
        reply = resp.strip().split("Пользователь:")[0].strip()
        user_memory[user_id].append({"user": user_text, "levi": reply})
        save_user_message(user_id, user_text)
        return reply if reply else "Леви: (ответ пустой)"
    except Exception as e:
        logging.error(f"Ошибка генерации ответа: {e}")
        return f"Леви: (ошибка генерации — {e})"

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    await msg.answer("Леви: Я здесь. Говори.")

@dp.message()
async def handler(msg: types.Message):
    txt = msg.text or ""
    reply = await generate_levi_reply(msg.from_user.id, txt)
    await msg.reply(reply)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот Леви запущен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



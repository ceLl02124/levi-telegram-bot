import os
import asyncio
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

from keep_alive import keep_alive  # импорт keep_alive

load_dotenv()  # Поддержка локального запуска с .env

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
if not TELEGRAM_API_TOKEN or not HF_TOKEN:
    raise RuntimeError("Не заданы TELEGRAM_API_TOKEN или HF_TOKEN")

bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()

keep_alive()  # запуск веб-сервера для keep-alive

client = InferenceClient(token=HF_TOKEN)
user_memory = defaultdict(list)

SYSTEM_PROMPT = (
    "Ты — Леви Аккерман из 'Атаки Титанов'. Говоришь грубо, хладнокровно, логично. "
    "Пишешь как в ролевой игре с описанием действий, мыслей и эмоций.\n\n"
)

async def generate_levi_reply(user_id: int, user_text: str) -> str:
    history = user_memory[user_id][-10:]
    conv = "\n".join([f"Пользователь: {h['user']}\nЛеви: {h['levi']}" for h in history])
    prompt = f"{SYSTEM_PROMPT}{conv}\nПользователь: {user_text}\nЛеви:"
    try:
        resp = client.text_generation(
            prompt,
            model="tiiuae/falcon-7b-instruct",
            max_new_tokens=500,
            temperature=0.8,
            top_p=0.95,
            do_sample=True,
        )
        reply = resp.get("generated_text", "").strip().split("Пользователь:")[0].strip()
        user_memory[user_id].append({"user": user_text, "levi": reply})
        return reply
    except Exception as e:
        print("Ошибка:", e)
        return "Леви: ..."

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    await msg.answer("Леви: Я здесь. Говори.")

@dp.message()
async def handler(msg: types.Message):
    txt = msg.text or ""
    reply = await generate_levi_reply(msg.from_user.id, txt)
    await msg.reply(reply)

async def main():
    print("Бот Леви запущен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


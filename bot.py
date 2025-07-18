import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from huggingface_hub import InferenceClient
from keep_alive import keep_alive
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_API_TOKEN"))
dp = Dispatcher()
hf_token = os.getenv("HF_TOKEN")

client = InferenceClient(
    model="moonshotai/Kimi-K2-Instruct",
    token=hf_token,
)

SYSTEM_PROMPT = (
    "Ты — Леви Аккерман из 'Атаки Титанов'. Ты холодный, жесткий, логичный. "
    "Говоришь коротко. Ролевая манера — добавляй действия и мысли.\n\n"
)

async def generate_reply(user_text):
    prompt = f"{SYSTEM_PROMPT}Пользователь: {user_text}\nЛеви:"
    response = client.text_generation(prompt=prompt, max_new_tokens=300)
    return response.strip()

@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer("Леви: Я здесь. Говори.")

@dp.message()
async def respond(msg: types.Message):
    reply = await generate_reply(msg.text)
    await msg.reply(reply)

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())






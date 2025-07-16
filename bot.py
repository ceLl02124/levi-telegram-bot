import asyncio
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from huggingface_hub import InferenceClient
import os

# Токены загружаются из переменных окружения
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher()
client = InferenceClient(token=HF_TOKEN)

user_memory = defaultdict(list)

SYSTEM_PROMPT = (
    "Ты — Леви Аккерман из 'Атаки Титанов'. Говори грубо, холодно, логично. "
    "Никакой воды. Отвечай в ролевом стиле с описанием эмоций, действий и мыслей.\n\n"
)

async def generate_levi_reply(user_id: int, user_text: str) -> str:
    memory = user_memory[user_id][-10:]
    dialogue = "\n".join([f"Пользователь: {msg['user']}\nЛеви: {msg['levi']}" for msg in memory])
    prompt = f"{SYSTEM_PROMPT}{dialogue}\nПользователь: {user_text}\nЛеви:"

    try:
        response = client.text_generation(
            prompt,
            model="tiiuae/falcon-7b-instruct",
            max_new_tokens=500,
            temperature=0.7,
            top_p=0.95,
            do_sample=True,
        )
        reply = response.strip().split("Пользователь:")[0].strip()
        user_memory[user_id].append({"user": user_text, "levi": reply})
        return reply
    except Exception as e:
        print("Ошибка HuggingFace:", e)
        return "..."

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Леви: Не трать моё время. Начинай уже.")

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if not text:
        await message.reply("Леви: Ты будешь молчать или начнёшь говорить?")
        return

    reply = await generate_levi_reply(user_id, text)
    await message.reply(reply)

async def main():
    print("🤖 Леви активен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

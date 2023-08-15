from aiogram import Bot
from aiogram.types import Message


async def get_start(message: Message, bot: Bot):
    await bot.send_message(message.from_user.id, f'<b>Привет {message.from_user.first_name}. Рад тебя видеть!</b>')
    await message.answer(f'<s>Привет {message.from_user.first_name}</s>. Это answer.')
    await message.reply(f'<s>Привет {message.from_user.first_name}</s>. Это reply.')

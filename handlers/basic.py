from aiogram import Bot
from aiogram.types import Message
from keyboards.meters import get_meters_keyboard


async def get_meters(message: Message, bot: Bot):
    await message.answer(f'Привет, {message.from_user.first_name}. Инлайн-клавиатура с командами по счетчикам',
                         reply_markup=get_meters_keyboard())


async def get_start(message: Message, bot: Bot):
    await message.answer(f'<s>Привет {message.from_user.first_name}</s>. Это answer.')
    await message.reply(f'<s>Привет {message.from_user.first_name}</s>. Это reply.')

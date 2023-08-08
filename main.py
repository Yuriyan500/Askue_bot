import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.enums.dice_emoji import DiceEmoji

import config

# Включаем логгирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=config.BOT_API_TOKEN)
# Диспетчер
dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")


# Хэндлер на команду /test1
@dp.message(Command("test1"))
async def cmd_test1(message: types.Message):
    await message.reply("This is test command #1")


# Хэндлер на команду /test2
@dp.message(Command("test2"))
async def cmd_test2(message: types.Message):
    await message.reply("This is test command #2")


@dp.message(Command("answer"))
async def cmd_answer(message: types.Message):
    await message.answer("This is simple answer")


@dp.message(Command("reply"))
async def cmd_reply(message: types.Message):
    await message.reply("This is simple reply")


@dp.message(Command("dice"))
async def cmd_dice(message: types.Message):
    await message.answer_dice(emoji=DiceEmoji.BOWLING)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

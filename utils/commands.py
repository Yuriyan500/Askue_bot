from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command='start',
            description='Начало работы'
        ),
        # BotCommand(
        #     command='help',
        #     description='Помощь'
        # ),
        BotCommand(
            command='meters',
            description='Работа со счетчиками'
        ),
        BotCommand(
            command='request',
            description='HTTP-запрос'
        ),
        BotCommand(
            command='cancel',
            description='Отмена внесения показаний'
        )
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

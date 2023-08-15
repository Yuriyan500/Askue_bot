import asyncio
import json
import logging

from aiogram import Bot, Dispatcher, F, types

from config_reader import config
from handlers import questions, different_types
from typing import Dict
from handlers.basic import get_start


async def start_bot(bot: Bot):
    await bot.send_message(config.admin_id, text='Бот запущен')

async def stop_bot(bot: Bot):
    await bot.send_message(config.admin_id, text='Бот остановлен')


async def get(message: types.Message):
    data_message = message.model_dump()
    print(json.dumps(data_message, default=str))
    result_data_message = await get_data_message(data_message=data_message)
    for key, value in result_data_message.items():
        print(f'{key} - {value}')
        if isinstance(value, str):
            print(f'Используя magic filter к данным {key} можно обратиться через через F.{key} == "{value}"')
        elif isinstance(value, int):
            print(f'Используя magic filter к данным {key} можно обратиться через через F.{key} == {value}')


async def get_data_message(data_message: Dict, prefix: str = '', sep: str = ''):
    correct_dict = {}
    for key, value in data_message.items():
        if isinstance(value, Dict):
            correct_dict.update(await get_data_message(data_message=value, prefix=f'{prefix}{key}{sep}'))
        else:
            correct_dict[f'{prefix}{key}'] = value
    return correct_dict


async def main():
    # Включаем логгирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", )

    # Объект бота
    # Для записей с типом Secret* необходимо вызывать метод get_secret_value(),
    # чтобы получить настоящее содержимое вместо '*******'
    bot = Bot(token=config.bot_token.get_secret_value(), parse_mode='HTML')

    # Диспетчер
    dp = Dispatcher()

    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    # dp.message.register(get_start)

    dp.include_router(questions.router)
    dp.include_router(different_types.router)

    try:
        # Запускаем бота и пропускаем все накопленные входящие
        # Да, этот метод можно вызвать даже если у вас поллинг
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import json
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

from typing import Dict

from config_reader import config
from handlers import questions, different_types
from handlers.basic import get_meters_commands
from handlers.callback import select_meters_commands, get_meters_serial, get_meters_value, write_meters_value
from utils.commands import set_commands
from utils.callbackdata import MetersInfo
from middlewares.counter import CounterMiddleware
from utils.MetersEntriesStates import MetersEntries
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage: MemoryStorage = MemoryStorage()
# Создаем объект диспетчера
dp: Dispatcher = Dispatcher(storage=storage)


async def start_bot(bot: Bot):
    await set_commands(bot)
    await bot.send_message(config.admin_id, text='Бот запущен')


async def stop_bot(bot: Bot):
    await bot.send_message(config.admin_id, text='Бот остановлен')


# Этот хэндлер будет срабатывать на команду "/cancel" в состоянии
# по умолчанию и сообщать, что эта команда работает внутри машины состояний
@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(text='Отменять нечего. Вы вне машины состояний\n\n'
                              'Чтобы перейти к командам счетчиков - '
                              'отправьте команду /meters или выберите нужный пункт меню')


# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключать машину состояний
@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(text='Вы вышли из машины состояний\n\n'
                              'Чтобы снова перейти к командам счетчиков - '
                              'отправьте команду /meters или выберите нужный пункт меню')
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


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

    # storage: MemoryStorage = MemoryStorage()
    # # Диспетчер
    # dp = Dispatcher(storage=storage)

    # Мидлварь необходимо регистрировать ранее, чем хэндлеры
    dp.message.middleware.register(CounterMiddleware())

    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    # Обработчик команды вызова инлайн-клавиатуры по счетчикам meters
    dp.message.register(get_meters_commands, Command(commands='meters'))

    # Обработчик на нажатие кнопок инлайн-клавиатуры meters
    dp.callback_query.register(select_meters_commands, MetersInfo.filter(), StateFilter(default_state))

    # Обработчик выбора кнопки инлайн-клавиатуры с серийными номерами счетчиков
    dp.callback_query.register(get_meters_serial, MetersInfo.filter(), StateFilter(MetersEntries.get_meter_serial))

    # Обработчик выбора кнопки инлайн-клавиатуры с показателями выбранного по серийнику счетчика
    dp.callback_query.register(get_meters_value, MetersInfo.filter(),
                               StateFilter(MetersEntries.get_meter_parameter))

    # Обработчик ввода цифрового значения - выбранного показателя счетчика
    dp.message.register(write_meters_value, StateFilter(MetersEntries.get_meter_value))

    # Регистрируем роутеры в диспетчере, которые отработают, если фильтры выше не сработали
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

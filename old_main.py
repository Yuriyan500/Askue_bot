import asyncio
import json
import logging
from random import randint

from aiogram import Bot, Dispatcher, types, html, F
from aiogram.filters.command import Command, CommandObject
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.types import FSInputFile, URLInputFile, BufferedInputFile
from aiogram.utils.markdown import hide_link
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config_reader import config
from typing import Dict
from datetime import datetime
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest
from typing import Optional
from aiogram.filters.callback_data import CallbackData

# Диспетчер
dp = Dispatcher()

# Объект бота
# Для записей с типом Secret* необходимо вызывать метод get_secret_value(),
# чтобы получить настоящее содержимое вместо '*******'
bot = Bot(token=config.bot_token.get_secret_value(), parse_mode='HTML')

user_data = {}

# Хэндлер на команду /start
# При старте организуем обычную клавиатуру с обычными кнопками
# (kb - массив массивов, а если проще - массив рядов кнопок)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="С пюрешкой"),
            types.KeyboardButton(text="Без пюрешки")
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,  # для уменьшения кнопок до приемлемого размера
        input_field_placeholder="Выберите способ подачи"
    )
    await message.answer("С чем подавать <u>котлеты</u>?", reply_markup=keyboard)
    # json_str = json.dumps(message.model_dump(), default=str)
    # print(json_str)


@dp.message(F.text == "С пюрешкой")
async def with_puree(message: types.Message):
    await message.reply("Отличный выбор!", reply_markup=types.ReplyKeyboardRemove())
    # json_str = json.dumps(message.model_dump(), default=str)
    # print(json_str)


@dp.message(F.text == "Без пюрешки")
async def with_puree(message: types.Message):
    await message.reply("Так невкусно!", reply_markup=types.ReplyKeyboardRemove())


# Хэндлер на команду /name, выводит введенное значение (параметр) после команды
@dp.message(Command("name"))
async def cmd_name(message: types.Message, command: CommandObject):
    if command.args:
        await message.answer(f"Привет, {html.bold(html.quote(command.args))}!")
    else:
        await message.answer("Пожалуйста, укажите своё имя после команды /name!")


# Хэндлер для иллюстрации построения обычных кнопок через reply_builder
@dp.message(Command("reply_builder"))
async def reply_builder(message: types.Message):
    builder = ReplyKeyboardBuilder()
    for i in range(1, 17):
        builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(4)
    await message.answer(
        "Выберите число:",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


# Хэндлер для иллюстрации работы специальных кнопок
@dp.message(Command("special_buttons"))
async def cmd_special_buttons(message: types.Message):
    builder = ReplyKeyboardBuilder()
    # метод row позволяет явным образом сформировать ряд
    # из одной или нескольких кнопок. Например, первый ряд
    # будет состоять из двух кнопок...
    builder.row(
        types.KeyboardButton(text="Запросить геолокацию", request_location=True),
        types.KeyboardButton(text="Запросить контакт", request_contact=True)
    )
    # ... второй из одной ...
    builder.row(types.KeyboardButton(
        text="Создать викторину",
        request_poll=types.KeyboardButtonPollType(type="quiz"))
    )
    # ... а третий снова из двух
    builder.row(
        types.KeyboardButton(
            text="Выбрать премиум пользователя",
            request_user=types.KeyboardButtonRequestUser(
                request_id=1,
                user_is_premium=True
            )
        ),
        types.KeyboardButton(
            text="Выбрать супергруппу с форумами",
            request_chat=types.KeyboardButtonRequestChat(
                request_id=2,
                chat_is_channel=False,
                chat_is_forum=True
            )
        )
    )
    await message.answer(
        "Выберите действие:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    # json_str = json.dumps(message.model_dump(), default=str)
    # print(json_str)


# Хэндлер для обработки запроса контакта
@dp.message(F.contact)
async def request_contact(message: types.Message):
    await message.reply("Ваш контакт!", reply_markup=types.ReplyKeyboardRemove())
    # json_str = json.dumps(message.model_dump(), default=str)
    # print(json_str)


# Хэндлер для обработки команды inline_url - рисования инлайн-кнопок
@dp.message(Command("inline_url"))
async def cmd_inline_url(message: types.Message, bot: Bot):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="GitHub", url="https://github.com")
    )
    builder.row(types.InlineKeyboardButton(
        text="Оф. канал Telegram",
        url="tg://resolve?domain=telegram")
    )

    # Чтобы иметь возможность показать ID-кнопку,
    # У юзера должен быть False флаг has_private_forwards
    user_id = 1189184041
    chat_info = await bot.get_chat(user_id)
    if not chat_info.has_private_forwards:
        builder.row(types.InlineKeyboardButton(
            text="Какой-то пользователь",
            url=f"tg://user?id={user_id}")
        )

    await message.answer(
        'Выберите ссылку',
        reply_markup=builder.as_markup(),
    )


# Хэндлер, который строит callback-кнопку
@dp.message(Command("random"))
async def cmd_random(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Нажми меня",
        callback_data="random_value")
    )
    await message.answer(
        "Нажмите на кнопку, чтобы бот отправил число от 1 до 10",
        reply_markup=builder.as_markup()
    )


# Хэндлер, обработчик нажатия на callback-кнопку
@dp.callback_query(F.data == "random_value")
async def send_random_value(callback: types.CallbackQuery):
    await callback.message.answer(str(randint(1, 10)))
    result = await get_data_message(callback.model_dump())
    for key, value in result.items():
        print(f'{key} - {value}')


def get_keyboard():
    buttons = [
        [
            types.InlineKeyboardButton(text="-1", callback_data="num_decr"),
            types.InlineKeyboardButton(text="+1", callback_data="num_incr")
        ],
        [types.InlineKeyboardButton(text="Подтвердить", callback_data="num_finish")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def update_num_text(message: types.Message, new_value: int):
    with suppress(TelegramBadRequest):
        await message.edit_text(
            f"Укажите число: {new_value}",
            reply_markup=get_keyboard()
        )


@dp.message(Command("numbers"))
async def cmd_numbers(message: types.Message):
    user_data[message.from_user.id] = 0
    await message.answer("Укажите число: 0", reply_markup=get_keyboard())


@dp.callback_query(F.data.startswith("num_"))
async def callbacks_num(callback: types.CallbackQuery):
    user_value = user_data.get(callback.from_user.id, 0)
    action = callback.data.split("_")[1]

    if action == "incr":
        user_data[callback.from_user.id] = user_value+1
        await update_num_text(callback.message, user_value+1)
    elif action == "decr":
        user_data[callback.from_user.id] = user_value-1
        await update_num_text(callback.message, user_value-1)
    elif action == "finish":
        await callback.message.edit_text(f"Итого: {user_value}")

    await callback.answer()


class NumbersCallbackFactory(CallbackData, prefix="fabnum"):
    action: str
    value: Optional[int]


def get_keyboard_fab():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="-2", callback_data=NumbersCallbackFactory(action="change", value=-2)
    )
    builder.button(
        text="-1", callback_data=NumbersCallbackFactory(action="change", value=-1)
    )
    builder.button(
        text="+1", callback_data=NumbersCallbackFactory(action="change", value=1)
    )
    builder.button(
        text="+2", callback_data=NumbersCallbackFactory(action="change", value=2)
    )
    builder.button(
        text="Подтвердить", callback_data=NumbersCallbackFactory(action="finish", value=3)
    )
    # Выравниваем кнопки по 4 в ряд, чтобы получилось 4 + 1
    builder.adjust(4)
    return builder.as_markup()


async def update_num_text_fab(message: types.Message, new_value: int):
    with suppress(TelegramBadRequest):
        await message.edit_text(
            f"Укажите число: {new_value}",
            reply_markup=get_keyboard_fab()
        )


@dp.message(Command("numbers_fab"))
async def cmd_numbers_fab(message: types.Message):
    user_data[message.from_user.id] = 0
    await message.answer("Укажите число: 0", reply_markup=get_keyboard_fab())


# Нажатие на одну из кнопок: -2, -1, +1, +2
@dp.callback_query(NumbersCallbackFactory.filter(F.action == "change"))
async def callbacks_num_change_fab(
        callback: types.CallbackQuery,
        callback_data: NumbersCallbackFactory
):
    # Текущее значение
    user_value = user_data.get(callback.from_user.id, 0)

    user_data[callback.from_user.id] = user_value + callback_data.value
    await update_num_text_fab(callback.message, user_value + callback_data.value)
    await callback.answer()


# Нажатие на кнопку "подтвердить"
@dp.callback_query(NumbersCallbackFactory.filter(F.action == "finish"))
async def callbacks_num_finish_fab(callback: types.CallbackQuery):
    # Текущее значение
    user_value = user_data.get(callback.from_user.id, 0)

    await callback.message.edit_text(f"Итого: {user_value}")
    await callback.answer()


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


# # Хэндлер для примера работы с выводом дополнительной информации, например, текущего времени
# @dp.message(F.text)
# async def echo_with_time(message: types.Message):
#     # Получаем текущее время в часовом поясе нашего ПК, метку времени
#     timestamp = datetime.now().strftime('%H:%M')
#     # Создаем подчеркнутый текст
#     added_text = html.underline(f"Создано в {timestamp}")
#     # Отправляем новое сообщение с меткой времени
#     await message.answer(f"{message.html_text}\n\n{added_text}")


# # Хэндлер для примера работы с message.entities (массив объектов типа MessageEntity)
# @dp.message(F.text)
# async def extract_data(message: types.Message):
#     data = {
#         "url": "<N/A>",
#         "email": "<N/A>",
#         "code": "<N/A>"
#     }
#     entities = message.entities or []
#     for item in entities:
#         if item.type in data.keys():
#             # Неправильно
#             # data[item.type] = message.text[item.offset : item.offset+item.length]
#             # Правильно
#             data[item.type] = item.extract_from(message.text)
#     await message.reply(
#         "Вот что я нашёл:\n"
#         f"URL: {html.quote(data['url'])}\n"
#         f"E-mail: {html.quote(data['email'])}\n"
#         f"Пароль: {html.quote(data['code'])}"
#     )

@dp.message(Command('hidden_link'))
async def upload_photo(message: types.Message):
    await message.answer(
        f"{hide_link('https://www.ejin.ru/wp-content/uploads/2017/09/7-667.jpg')}"
        f"Спрятанная *ссылка*:\n"
    )


# Хэндлер для скачивания изображения с контент-тайпом photo (скачиваем в папку /tmp с расширением .jpg)
@dp.message(F.photo)
async def download_photo(message: types.Message, bot: Bot):
    await message.answer("Это точно какое-то изображение!")
    await bot.download(
        message.photo[-1],
        destination=f"/tmp/{message.photo[-1].file_id}.jpg"
    )


# Хэндлер для скачивания стикеров с контент-тайпом sticker (скачиваем в папку /tmp с расширением .webp)
@dp.message(F.sticker)
async def download_sticker(message: types.Message, bot: Bot):
    await bot.download(
        message.sticker,
        # для Windows пути надо подправить
        destination=f"/tmp/{message.sticker.file_id}.webp"
    )


# Хэндлер для обработки gif-анимации
@dp.message(F.animation)
async def echo_gif(message: types.Message):
    await message.reply_animation(message.animation.file_id)


# Хэндлер для обработки загрузки файлов на сервер телеграм на примере загрузки изображений
@dp.message(Command('images'))
async def upload_photo(message: types.Message):
    # Сюда будем помещать file_id отправленных файлов, чтобы потом ими воспользоваться
    file_ids = []
    # Чтобы продемонстрировать BufferedInputFile, воспользуемся "классическим"
    # открытием файла через `open()`. Но, вообще говоря, этот способ
    # лучше всего подходит для отправки байтов из оперативной памяти
    # после проведения каких-либо манипуляций, например, редактированием через Pillow
    with open("buffer_emulation.jpg", "rb") as image_from_buffer:
        result = await message.answer_photo(
            BufferedInputFile(
                image_from_buffer.read(),
                filename="image from buffer.jpg"
            ),
            caption="Изображение из буфера"
        )
        file_ids.append(result.photo[-1].file_id)

    # Отправка файла из файловой системы
    image_from_pc = FSInputFile("image_from_pc.jpg")
    result = await message.answer_photo(
        image_from_pc,
        caption="Изображение из файла на компьютере"
    )
    file_ids.append(result.photo[-1].file_id)

    # Отправка файла по ссылке
    image_from_url = URLInputFile(
        "https://sdelanounas.ru/i/d/3/d/d3d3Lm1vcy5ydS91cGxvYWQvbmV3c2ZlZWQvYXJ0aWNsZXMvNDA5Ni0yNzMxLW1heF8oMikoMjUpLmpwZz9fX2lkPTE1MzE4OQ==.jpg",
        bot)
    result = await message.answer_photo(
        image_from_url,
        caption="Изображение по ссылке"
    )
    file_ids.append(result.photo[-1].file_id)
    await message.answer("Отправленные файлы:\n" + "\n".join(file_ids))


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
    # Включаем логгирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO)

    dp.message.register(get)
    # dp.callback_query.register(send_random_value)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

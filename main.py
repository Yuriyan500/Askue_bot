import asyncio
import logging
from aiogram import Bot, Dispatcher, types, html, F
from aiogram.filters.command import Command, CommandObject
from aiogram.enums.dice_emoji import DiceEmoji
from aiogram.types import FSInputFile, URLInputFile, BufferedInputFile
from aiogram.utils.markdown import hide_link
from config_reader import config
from datetime import datetime

# Включаем логгирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
# Для записей с типом Secret* необходимо
# вызывать метод get_secret_value(),
# чтобы получить настоящее содержимое вместо '*******'
# bot = Bot(token=config.BOT_API_TOKEN)
bot = Bot(token=config.bot_token.get_secret_value(), parse_mode='HTML')
# Диспетчер
dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello, <u>world</u>!")


# Хэндлер на команду /name, выводит введенное значение (параметр) после команды
@dp.message(Command("name"))
async def cmd_name(message: types.Message, command: CommandObject):
    if command.args:
        await message.answer(f"Привет, {html.bold(html.quote(command.args))}!")
    else:
        await message.answer("Пожалуйста, укажите своё имя после команды /name!")


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
    image_from_url = URLInputFile("https://sdelanounas.ru/i/d/3/d/d3d3Lm1vcy5ydS91cGxvYWQvbmV3c2ZlZWQvYXJ0aWNsZXMvNDA5Ni0yNzMxLW1heF8oMikoMjUpLmpwZz9fX2lkPTE1MzE4OQ==.jpg", bot)
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
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

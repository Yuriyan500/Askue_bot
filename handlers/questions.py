from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from filters.chat_id import ChatIdFilter
from filters.user_id import UserIdFilter
from middlewares.accounts import get_users_id

from keyboards.for_questions import get_yes_no_kb

router = Router()
users_id = get_users_id()
router.message.filter(UserIdFilter(users_id))

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Вы довольны своей работой?",
        reply_markup=get_yes_no_kb()
    )


@router.message(F.text == "Да")
async def answer_yes(message: Message):
    await message.answer(
        "Это здорово!",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(F.text == "Нет")
async def answer_no(message: Message):
    await message.answer(
        "Жаль...",
        reply_markup=ReplyKeyboardRemove()
    )

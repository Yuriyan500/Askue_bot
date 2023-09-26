from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state

router = Router()


@router.message(F.text)
async def message_with_text(message: Message, state: FSMContext):
    context_data = await state.get_data()
    current_state = context_data.get('current_state')
    print(f'current_state = {current_state}')
    # await message.answer(f'current_state = {current_state}')
    if (current_state is not None) and (current_state != StateFilter(default_state)):
        await message.answer(text=f'Вы в процессе внесения показаний счетчика. '
                                  f'Для выхода из процесса введите команду /cancel')

    await message.answer("Текст")


@router.message(F.sticker)
async def message_with_sticker(message: Message):
    await message.answer("Это стикер.")


@router.message(F.animation)
async def message_with_gif(message: Message):
    await message.answer("Это GIF.")

import re

from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsDigitsCheck(BaseFilter):
    # Фильтр на то, чтобы пользователь вводил только цифры при вводе показаний счетчика
    pattern = re.compile(r"^\d*[.,]?\d*$")

    def __init__(self, message: Message):
        self.message = message

    async def __call__(self, message: Message) -> bool:

        return bool(self.pattern.match(message.text))


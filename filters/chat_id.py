from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message


class ChatIdFilter(BaseFilter):
    def __init__(self, chat_id: Union[int, list]):
        self.chat_id = chat_id

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_id, int):
            return message.chat.id == self.chat_id
        else:
            print('chat_id filter')
            return message.chat.id in self.chat_id

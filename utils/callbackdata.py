from aiogram.filters.callback_data import CallbackData
from typing import Optional


class MetersInfo(CallbackData, prefix='meters'):
    meter_command: Optional[str] = ''
    meter_serial: Optional[str] = ''
    meter_id_uspd: Optional[int] = 0
    meter_id_channel: Optional[int] = 0
    meter_id_pp: Optional[int] = 0
    meter_name: Optional[str] = ''

# TODO - сделать вариант с сохранением тестового представления выбранного параметра в классе MetersInfo (т.к.
#  кириллица занимает много места, а размер одного колбэк-сообщения - 64 кБ)

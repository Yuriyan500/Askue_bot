from aiogram.filters.callback_data import CallbackData


class MetersInfo(CallbackData, prefix='meters'):
    meter_number: str

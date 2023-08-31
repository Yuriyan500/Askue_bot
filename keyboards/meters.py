from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.callbackdata import MetersInfo


def get_meters_keyboard():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text='Последние показания', callback_data=MetersInfo(meter_number='all_meters'))
    keyboard_builder.button(text='Внести показания', callback_data=MetersInfo(meter_number='make_entries_for_meters'))
    keyboard_builder.button(text='Третья команда', callback_data=MetersInfo(meter_number='third_meters_command'))

    keyboard_builder.adjust(1)
    return keyboard_builder.as_markup()

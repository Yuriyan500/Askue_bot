from aiogram.fsm.state import StatesGroup, State


class MetersEntries(StatesGroup):
    get_meter_serial = State()
    get_meter_parameter = State()
    get_meter_value = State()

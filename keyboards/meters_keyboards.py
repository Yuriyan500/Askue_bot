from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.callbackdata import MetersInfo


def get_meters_commands_keyboard():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text='Последние показания',
                            callback_data=MetersInfo(meter_command='all_meters', meter_serial=''))
    keyboard_builder.button(text='Внести показания',
                            callback_data=MetersInfo(meter_command='make_entries_for_meters', meter_serial=''))

    keyboard_builder.adjust(1)
    return keyboard_builder.as_markup()


def get_meters_serial_keyboard(serial_results):
    keyboard_builder = InlineKeyboardBuilder()

    for row in serial_results:
        # row[1] - MeterInfo.SN,
        # row[2] - ModuleTypes.NameType,
        # row[3] - USD.Name,
        # row[4] - USD.ID_USPD
        if row[3] is None:  # Если нет ввода, то выводим тип и номер счетчика
            keyboard_builder.button(text=row[1] + ', ' + row[2],
                                    callback_data=MetersInfo(meter_command='make_entries_for_meters',
                                                             meter_name=row[2],
                                                             meter_serial=str(row[1]),
                                                             meter_id_uspd=0))
        else:
            keyboard_builder.button(text=row[1] + ', ' + row[2] + ', ' + row[3],
                                    callback_data=MetersInfo(meter_command='make_entries_for_meters',
                                                             meter_name=row[2],
                                                             meter_serial=str(row[1]),
                                                             meter_id_uspd=row[4]))

    keyboard_builder.adjust(1)
    return keyboard_builder.as_markup()


def get_meters_parameter_keyboard(parameter_results, meter_id_uspd, meter_serial):
    keyboard_builder = InlineKeyboardBuilder()
    # приходится анализировать meter_id_uspd, чтобы рисовать клавиатуры с разными значениями класса MeterInfo
    if meter_id_uspd == 0:
        for row in parameter_results:
            # row[0] - PointParams.ID_PP,
            # row[1] - PointParamTypes.ParamName, имя параметра
            # row[2] - Units.ShortName, единица измерения
            keyboard_builder.button(text=row[1] + ', ' + row[2],
                                    callback_data=MetersInfo(meter_command='make_entries_for_meters',
                                                             meter_serial=meter_serial,
                                                             meter_id_uspd=0,
                                                             meter_id_channel=0,
                                                             meter_id_pp=row[0]))
    else:
        for row in parameter_results:
            # row[0] - Channels_Main.ID_Channel,
            # row[1] - Channels_Main.ID_USPD,
            # row[2] - Channels_Main.Name, имя параметра
            # row[3] - Units.ShortName, единица измерения
            keyboard_builder.button(text=row[2] + ', ' + row[3],
                                    callback_data=MetersInfo(meter_command='make_entries_for_meters',
                                                             meter_serial=meter_serial,
                                                             meter_id_uspd=row[1],
                                                             meter_id_channel=row[0],
                                                             meter_id_pp=0))

    keyboard_builder.adjust(1)
    return keyboard_builder.as_markup()


def enter_meters_value_keyboard(callback_data):
    keyboard_builder = InlineKeyboardBuilder()
    # Будем просто перезаписывать значения класса MeterInfo
    keyboard_builder.button(text='Внести показания',
                            callback_data=MetersInfo(meter_command='Input value',
                                                     meter_serial=callback_data.meter_serial,
                                                     meter_id_uspd=callback_data.meter_id_uspd,
                                                     meter_id_channel=callback_data.meter_id_channel,
                                                     meter_id_pp=callback_data.meter_id_pp,
                                                     meter_name=callback_data.meter_name))

    keyboard_builder.adjust(1)
    return keyboard_builder.as_markup()

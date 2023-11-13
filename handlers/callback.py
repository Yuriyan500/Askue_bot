import re
from aiogram import F
from aiogram.types import CallbackQuery, Message
from utils.callbackdata import MetersInfo
from utils.dbconnect import create_db_connection
from datetime import datetime
from utils.MetersEntriesStates import MetersEntries
from aiogram.fsm.context import FSMContext
from keyboards.meters_keyboards import (get_meters_serial_keyboard, get_meters_parameter_keyboard,
                                        enter_meters_value_keyboard)
from utils.querytexts import (all_meters_readings_query_usd, all_meters_readings_query_manual, meters_serial_query,
                              meter_value_query_manual, meter_value_query_usd, write_meters_value_query_manual,
                              meters_readings_query_manual_with_serial, meters_readings_query_usd_with_id)


# TODO - добавить проверки на вводимые в машине состояний данные (текст, либо цифры, либо еще что)


# Функция определяет, какая кнопка главного меню работы со счетчиками нажата,
# и в зависимости от этого вызывает нужную функцию второго уровня
async def select_meters_commands(call: CallbackQuery, callback_data: MetersInfo, state: FSMContext):
    meter_command = callback_data.meter_command
    meter_serial = callback_data.meter_serial

    print(f'select_meters_commands. meter_command: {meter_command}, meter_serial: {meter_serial}')
    context_data = await state.get_data()
    current_state = context_data.get('current_state')
    print(f'current_state = {current_state}')

    if meter_command == 'all_meters':
        await all_meters_readings(call)
    elif meter_command == 'make_entries_for_meters':
        await make_entries_for_meters(call, state)
    else:
        pass


# Функция чтения показаний для всех счетчиков. Используется ХП [READ_NI_BY_ID_AND_DT],
# вычисляющая накопительный итог по каналу на заданную дату
async def all_meters_readings(call):
    connection = create_db_connection()
    if not connection:
        return

    # строка (пока строка) для возвращения результата
    str_results = ''
    date_today = datetime.today().strftime('%Y%m%d')
    last_date = date_today

    cursor = connection.cursor()

    query_text = all_meters_readings_query_usd()
    cursor.execute(query_text)
    main_results = cursor.fetchall()

    for row in main_results:
        # запускаем запрос - хранимую процедуру по вычислению накопительного итога по каждому каналу (id)
        # на заданную дату
        query_text = (f"DECLARE @return_value int EXEC @return_value = READ_NI_BY_ID_AND_DT  @ID = {row.id}, "
                      f" @D1 = N'{date_today}'")
        cursor.execute(query_text)

        query_result = cursor.fetchall()
        if int(cursor.rowcount) == 0:
            continue

        # Возвращается список с одним элементом - кортежем, содержащим показания по id и дату.
        # Преобразуем кортеж в список
        result_list = list(query_result[0])

        # Первый элемент в преобразованном списке - нужное нам показание.
        # Если там 0 или None - проходим по циклу далее
        if result_list[0] is None or result_list[0] == 0:
            continue

        row.res_value = round(result_list[0], 2)
        try:
            last_date = str(result_list[1])
        except:
            last_date = date_today

        # преобразуем строку из запроса в строковое значение, перебор колонок через запятую
        str_results = (str_results + str(row.Name_USD) + ', ' + str(row.Type_USD) + ', ' + last_date + ', '
                       + str(row.Channel_Name) + ', ' + str(row.res_value) + ' ' + str(row.Unit) + '\n')

    # Теперь запускаем запрос для счетчиков, данные для которых вводятся вручную через "Ручной ввод".
    query_text = all_meters_readings_query_manual()
    cursor.execute(query_text)

    main_results = cursor.fetchall()

    for row in main_results:
        # запускаем запрос - функцию по вычислению введенных значений по (pp.ID_PP)
        query_text = f"SELECT top 1 * FROM dbo.PP_NIs_PP({row[2]}, null, null) ORDER BY DT DESC"
        cursor.execute(query_text)

        query_result = cursor.fetchall()
        if int(cursor.rowcount) == 0:
            continue

        # Возвращается список с одним элементом - кортежем, содержащим дату DT, показания Val и состояние State.
        # Преобразуем кортеж в список
        result_list = list(query_result[0])

        row.res_value = round(result_list[1], 2)

        try:
            last_date = str(result_list[0])
        except:
            last_date = date_today

        # преобразуем строку из запроса в строковое значение, перебор колонок через запятую
        str_results = (str_results + str(row.NameType) + ', s/n ' + str(row.SN) + ', '
                       + str(row.ParamName) + ', ' + last_date + ', ' + str(row.res_value) + ' ' + str(row.Unit) + '\n')

    # закрываем соединение
    connection.close()

    await call.message.answer(str_results)
    await call.answer()


async def make_entries_for_meters(message: Message, state: FSMContext):
    # Здесь будем действовать через FSMContext:
    # - выводим инлайн-клавиатуру со счетчиками и ожидаем нажатия на нужный счетчик
    # - запрашиваем показатель (например, активная энергия)
    # - запрашиваем величину показателя цифрой
    # - записываем значение в базу через ХП

    connection = create_db_connection()
    if not connection:
        return

    cursor = connection.cursor()
    # Запрос на выборку счетчиков и их серийных номеров.
    # Выбираем необходимые поля, основная таблица - MeterMountHist.
    query_text = meters_serial_query()
    cursor.execute(query_text)
    main_results = cursor.fetchall()

    # закрываем соединение
    connection.close()

    # Переводим FSM в состояние state_get_meter_serial
    await state.update_data(current_state='state_get_meter_serial')
    await state.set_state(MetersEntries.get_meter_serial)

    # строим следующую инлайн-клавиатуру, где кнопки - это счетчики с серийниками
    await message.answer(f'{message.from_user.first_name}, выберите счетчик:\n '
                         f'Для выхода введите команду /cancel',
                         reply_markup=get_meters_serial_keyboard(main_results))


# Функция вызывается при выборе определенного счетчика в состоянии MetersEntries.get_meter_serial.
# В функции будем для выбранного по серийному номеру счетчика выдавать пользователю текущие показания,
# а также выводить кнопку "Ввести показания" для дальнейшего ввода показаний
async def meters_serial_selected(call: CallbackQuery, callback_data: MetersInfo, state: FSMContext):
    meter_command = callback_data.meter_command
    meter_serial = callback_data.meter_serial
    meter_id_uspd = callback_data.meter_id_uspd
    meter_name = callback_data.meter_name

    print(f'meters_serial_selected. meter_command: {meter_command}, meter_serial: {meter_serial}, '
          f'meter_ID_USPD: {meter_id_uspd}')
    context_data = await state.get_data()
    current_state = context_data.get('current_state')
    print(f'current_state = {current_state}')

    # строка (пока строка) для возвращения результата
    str_results = ''
    date_today = datetime.today().strftime('%Y-%m-%d')
    last_date = date_today

    # Создаем запрос, вытаскиваем все показатели для выбранного серийника
    connection = create_db_connection()
    if not connection:
        return

    cursor = connection.cursor()

    if meter_id_uspd == 0:  # счетчик, не привязанный ко вводу, к УСПД (USD), данные по таким вводятся вручную
        # Необходимо вывести последние показания по выбранному счетчику:
        query_text = meters_readings_query_manual_with_serial(meter_serial)
        cursor.execute(query_text)
        main_results = cursor.fetchall()

        for row in main_results:
            # запускаем запрос - функцию по вычислению введенных значений по (pp.ID_PP)
            callback_data.meter_id_pp = row[2]
            query_text = f"SELECT top 1 * FROM dbo.PP_NIs_PP({callback_data.meter_id_pp}, null, null) ORDER BY DT DESC"
            cursor.execute(query_text)

            query_result = cursor.fetchall()
            if int(cursor.rowcount) == 0:
                # преобразуем строку из запроса в строковое значение, перебор колонок через запятую
                str_results = (str_results + str(row.ParamName) + ', 0 ' + str(row.Unit) + '\n')
                continue

            # Возвращается список с одним элементом - кортежем, содержащим дату DT, показания Val и состояние State.
            # Преобразуем кортеж в список
            result_list = list(query_result[0])

            try:
                row.res_value = round(result_list[1], 2)
                last_date = str(result_list[0])
            except:
                row.res_value = 0
                last_date = date_today

            # преобразуем строку из запроса в строковое значение, перебор колонок через запятую
            str_results = (str_results + str(row.ParamName) + ', ' + str(row.res_value) + ' ' + str(row.Unit) + '\n')

        await call.message.answer(f"Последние показания:\n Cчетчик {meter_serial}, {meter_name}, \n Дата: {last_date}, "
                                  f"\n {str_results}",
                                  reply_markup=enter_meters_value_keyboard(callback_data))

        # # Выбираем необходимые поля, основная таблица - MeterInfo, MeterMountHist и PointParams.
        # # Условие на MeterInfo.SN = meter_serial
        # query_text = meter_value_query_manual(meter_serial)
        # cursor.execute(query_text)
    else:
        # Необходимо вывести последние показания по выбранному счетчику:
        query_text = meters_readings_query_usd_with_id(meter_id_uspd)
        cursor.execute(query_text)
        main_results = cursor.fetchall()

        for row in main_results:
            # запускаем запрос - хранимую процедуру по вычислению накопительного итога по каждому каналу (id)
            # на заданную дату
            callback_data.meter_id_channel = row.id
            query_text = (f"DECLARE @return_value int EXEC @return_value = READ_NI_BY_ID_AND_DT  @ID = {row.id}, "
                          f" @D1 = N'{date_today}'")
            cursor.execute(query_text)

            query_result = cursor.fetchall()
            if int(cursor.rowcount) == 0:
                continue

            # Возвращается список с одним элементом - кортежем, содержащим показания по id и дату.
            # Преобразуем кортеж в список
            result_list = list(query_result[0])

            # Первый элемент в преобразованном списке - нужное нам показание.
            # Если там 0 или None - проходим по циклу далее
            if result_list[0] is None or result_list[0] == 0:
                continue

            try:
                row.res_value = round(result_list[0], 2)
                last_date = str(result_list[1])
            except:
                row.res_value = 0
                last_date = date_today

            # преобразуем строку из запроса в строковое значение, перебор колонок через запятую
            str_results = (str_results + str(row.Channel_Name) + ', ' + str(row.res_value) + ' ' + str(row.Unit) + '\n')

        # Также строим следующую инлайн-клавиатуру, где будет одна кнопка - предложение ввести показания
        await call.message.answer(f"Последние показания:\n Cчетчик {meter_serial}, {meter_name}, \n Дата: {last_date}, "
                                  f"\n {str_results}",
                                  reply_markup=enter_meters_value_keyboard(callback_data))


    # закрываем соединение
    connection.close()

    # # Апдейтим текущее состояние current_state в state: FSMContext
    # await state.update_data(current_state='state_get_meter_parameter')

    # Записываем в состояние серийный номер и УСПД.
    await state.update_data(meter_serial=meter_serial)
    await state.update_data(meter_id_uspd=meter_id_uspd)
    # Переводим FSM в состояние state_get_meter_serial
    # await state.set_state(MetersEntries.get_meter_parameter)
    await call.answer()


# Функция вызывается при выборе определенного параметра счетчика в состоянии MetersEntries.state_get_meter_parameter,
# установленном в функции meters_serial_selected на предыдущем шаге выбора серийного номера счетчика.
# В функции будем для выбранного по серийному номеру счетчика и выбранного параметра запрашивать величину параметра
async def get_meters_value(call: CallbackQuery, callback_data: MetersInfo, state: FSMContext):
    # Вытаскиваем всё нужное из класса:
    meter_command = callback_data.meter_command
    meter_serial = callback_data.meter_serial
    meter_id_uspd = callback_data.meter_id_uspd
    meter_id_channel = callback_data.meter_id_channel
    meter_id_pp = callback_data.meter_id_pp
    # meter_parameter_name = callback_data.meter_parameter_name

    print(f'get_meters_value. meter_command: {meter_command}, meter_serial: {meter_serial}, '
          f'meter_ID_USPD: {meter_id_uspd}, meter_id_channel: {meter_id_channel}')
    context_data = await state.get_data()
    current_state = context_data.get('current_state')
    print(f'current_state = {current_state}')

    if not meter_id_channel and not meter_id_pp:
        await call.message.answer(text=f"Выбран некорректный пункт меню! Пожалуйста вернитесь к выбору параметра "
                                       f"или введите команду /cancel для выхода из процедуры ввода.")
        return

    # Запрашиваем величину показателя
    await call.message.answer(f"Выбран счетчик '{meter_serial}'.\n "
                              f"{call.from_user.first_name}, введите величину показателя:")

    # Переводим FSM в состояние state_get_meter_value, а также будем апдейтить meter_serial
    # при выборе кнопки другого счетчика
    await state.update_data(current_state='state_get_meter_value')
    await state.update_data(meter_id_channel=meter_id_channel)
    await state.update_data(meter_id_uspd=meter_id_uspd)
    await state.update_data(meter_id_pp=meter_id_pp)
    await state.update_data(meter_serial=meter_serial)
    # await state.update_data(meter_parameter_name=meter_parameter_name)
    await state.set_state(MetersEntries.get_meter_value)
    await call.answer()


async def write_meters_value(message: Message, state: FSMContext):
    print(f'Данные состояния state: {await state.get_data()}')
    print(f'Само состояние state: {await state.get_state()}')

    r = re.compile(r"^\d*[.,]?\d*$")

    state_data = await state.get_data()

    meter_value = float(message.text.replace(',', '.'))
    # Вытаскиваем meter_id_pp, meter_serial, meter_id_channel, meter_parameter_name из сохраненного значения state_data
    meter_id_pp = state_data['meter_id_pp']
    meter_serial = state_data['meter_serial']
    meter_id_channel = state_data['meter_id_channel']
    meter_id_uspd = state_data['meter_id_uspd']
    # meter_parameter_name = state_data['meter_parameter_name']

    # Сохраняем введенное значение в хранилище по ключу "value"
    await state.update_data(value=message.text)
    await message.answer(text=f"Выбран счетчик '{meter_serial}'.\n"
                              f"Введена величина {message.text}")

    # Создаем запрос, вытаскиваем все показатели для выбранного серийника
    connection = create_db_connection()
    if not connection:
        return

    # Пытаемся записать всё в БД Энергосферы.
    # В зависимости от того, привязан ли счетчик к вводу, или не привязан (ручной ввод), будут использоваться
    # разные процедуры.
    if meter_id_channel == 0:
        # Для ручного ввода - запись в таблицу PointNIs_On_Main_Stack
        # через ХП PP_NIs_Write_PP(PointParams.ID_PP, Date, Value, State=16384).
        cursor = connection.cursor()

        query_text = write_meters_value_query_manual(meter_id_pp, meter_value)

        cursor.execute(query_text)

        # main_result = cursor.fetchall()
        # print(main_result)
        # print(cursor.rowcount)
        # TODO - необходимо разобраться с возможными вариантами возвращаемого результата выполнения
        #  команды cursor.execute(query_text) и корректно их отрабатывать
        connection.commit()
        await message.answer(text=f"Для выбранного счетчика '{meter_serial}' "
                                  f"записаны показания:\n '{message.text}'")

    else:
        # Для привязанного счетчика - запись в таблицы NI
        # через ХП WRITE_NI_CHAN(Channels_Main.ID_Channel, Date, Value, State=?)

        cursor = connection.cursor()

        # Подготовим служебные переменные для записи в таблицы:
        # тип блока информации. На сегодня распознаются: 'USPD','Module','Channel'
        type_info = 'Channel'
        # Блок информации (несколько строк формата ПАРАМЕТР=ЗНАЧЕНИЕ, разделенных переводами строк)
        info = 'Name=Активная энергия прямого направления\n Unit=кВт*ч'
        # Номер модуля внутри ЭКОМа. При @TypeInfo<>'Module' игнорируется
        module_num = 0

        query_text = (f"DECLARE\n"
                      f"@return_curdate datetime,\n"
                      f"@State int = 0\n"
                      f"set @State = 0\n"
                      f"-- находим текущую дату\n"
                      f"EXEC @return_curdate = [dbo].[FncGetDate]\n"
                      f"-- записываем новое значение в таблицы NIs через ХП\n"
                      f"EXEC dbo.WRITE_NI_CHAN {meter_id_channel}, @return_curdate, {meter_value}, @State, NULL, 0\n"
                      f"-- записываем логи в AutoInfo\n"
                      f"EXEC dbo.WRITE_INFO '{type_info}', {meter_id_uspd}, {module_num}, {meter_id_channel}, '{info}',"
                      f"@return_curdate")

        cursor.execute(query_text)

        connection.commit()
        await message.answer(text=f"Для выбранного счетчика {meter_serial} "
                                  f"записаны показания:\n '{message.text}'")

    # закрываем соединение
    connection.close()

    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


async def warning_not_meters_value(message: Message, state: FSMContext):
    await message.answer(text=f"Введите корректное числовое значение выбранного показателя.\n "
                              f"Если вы хотите прервать ввод данных - введите команду /cancel")


from aiogram.types import CallbackQuery, Message
from utils.callbackdata import MetersInfo
from utils.dbconnect import create_db_connection
from datetime import datetime
from utils.MetersEntriesStates import MetersEntries
from aiogram.fsm.context import FSMContext
from keyboards.meters_keyboards import get_meters_serial_keyboard, get_meters_parameter_keyboard


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

    cursor = connection.cursor()
    # Выбираем необходимые поля, основная таблица - Channels_Main.
    # Тип получаемых ограничиваем 29, 20 - активная энергия и объём воды
    cursor.execute('SELECT c.ID_Channel as id, usd.Name as Name_USD, usd.TypeUSD as Type_USD, c.Name as '
                   'Channel_Name, 0 as res_value, u.ShortName as Unit '
                   ' FROM Channels_Main as c '
                   ' left join Units as u on c.ID_Units = u.ID_Units '
                   ' left join ValueTypes as v on c.ID_ValueType = v.ID_ValueType '
                   ' left join USD as usd on c.ID_USPD = usd.ID_USPD '
                   ' where c.ID_ValueType in (29, 20) '
                   )
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
        print(query_result)
        # преобразуем строку из запроса в строковое значение, перебор колонок через запятую
        # str_results = str_results + ', '.join(str(x) for x in row) + '\n'
        str_results = (str_results + str(row.Name_USD) + ', ' + str(row.Type_USD) + ', '
                       + str(row.Channel_Name) + ', ' + str(row.res_value) + ' ' + str(row.Unit) + '\n')

    print('str_results:', str_results)

    # Теперь запускаем запрос для счетчиков, данные для которых вводятся вручную через "Ручной ввод".
    # Данные по таким счетчикам хранятся в PointNIs_On_Main_Stack, вытаскивать их будем через функцию PP_NIs_PP,
    # для которой на вход нужен ID_PP, поэтому в дополнение к основной информации о таком счетчике (название и серийный
    # номер) добираемся до ID_PP
    cursor.execute(' select minfo.SN as SN, minfo.NameType as NameType, pp.ID_PP, pp.ParamName as ParamName, '
                   'pp.ShortName as Unit, 0 as res_value '
                   ' from (SELECT ID_MMH, ID_Point, ID_MeterInfo FROM MeterMountHist where ID_Module is NULL) as mmh '
                   ' left join (select mi.ID_MeterInfo, mi.SN, mt.NameType from MeterInfo as mi '
                   ' left join ModuleTypes as mt on mi.ID_ModuleType = mt.ID_Type) as minfo '
                   ' on mmh.ID_MeterInfo = minfo.ID_MeterInfo '
                   'left join (select pp.ID_PP, pp.ID_Point, ppt.ParamName, ppt.ShortName from PointParams as pp '
                   '        left join (select ppt.ParamName, ppt.ID_Param, units.ShortName from PointParamTypes as ppt '
                   '                    left join (select vt.ID_ValueType, u.ShortName from ValueTypes as vt '
                   '                                left join Units as u on vt.ID_BaseUnits = u.ID_Units) as units '
                   '            on ppt.ID_ValueType = units.ID_ValueType) as ppt on pp.ID_Param = ppt.ID_Param) '
                   ' as pp on mmh.ID_Point = pp.ID_Point '
                   ' where minfo.SN is not NULL ')

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
        print(query_result)
        # преобразуем строку из запроса в строковое значение, перебор колонок через запятую
        # str_results = str_results + ', '.join(str(x) for x in row) + '\n'
        str_results = (str_results + str(row.NameType) + ', s/n ' + str(row.SN) + ', '
                       + str(row.ParamName) + ', ' + str(row.res_value) + ' ' + str(row.Unit) + '\n')

    # закрываем соединение
    connection.close()

    await call.message.answer(str_results)
    await call.answer()


async def make_entries_for_meters(call, state):
    # Здесь будем действовать через FSMContext:
    # - выводим инлайн-клавиатуру со счетчиками и ожидаем нажатия на нужный счетчик
    # - запрашиваем показатель (например, активная энергия)
    # - запрашиваем величину показателя цифрой
    # - записываем значение в базу через ХП

    connection = create_db_connection()
    if not connection:
        return

    cursor = connection.cursor()
    # Выбираем необходимые поля, основная таблица - MeterMountHist.
    cursor.execute('SELECT mmh.ID_MMH, mi.SN, mi.NameType, usds.Name, usds.ID_USPD '
                   ' FROM MeterMountHist mmh '
                   ' left join (SELECT mi.ID_MeterInfo, mt.NameType, mi.SN '
                   '            FROM MeterInfo as mi left join ModuleTypes as mt on mi.ID_ModuleType = mt.ID_Type '
                   '            where SN is not NULL) mi on mmh.ID_MeterInfo = mi.ID_MeterInfo '
                   ' left join '
                   ' (SELECT m.ID_Module, m.ID_USPD, u.Name FROM Modules m left join USD u on m.ID_USPD = u.ID_USPD) '
                   ' usds on mmh.ID_Module = usds.ID_Module '
                   ' where mi.SN is not NULL '
                   ' order by ID_MMH '
                   )
    main_results = cursor.fetchall()

    for row in main_results:
        print(row)

    # закрываем соединение
    connection.close()

    # строим следующую инлайн-клавиатуру, где кнопки - это счетчики с серийниками
    await call.message.answer(f'{call.from_user.first_name}, выберите счетчик:',
                              reply_markup=get_meters_serial_keyboard(main_results))
    # Переводим FSM в состояние state_get_meter_serial
    await state.update_data(current_state='state_get_meter_serial')
    await state.set_state(MetersEntries.get_meter_serial)
    await call.answer()


# Функция вызывается при выборе определенного счетчика в состоянии MetersEntries.get_meter_serial, установленном в
# функции make_entries_for_meters на предыдущем шаге "Внести показания". В функции будем для выбранного по серийному
# номеру счетчика выдавать пользователю возможные параметры (активная энергия и т.д.)
async def get_meters_serial(call: CallbackQuery, callback_data: MetersInfo, state: FSMContext):
    meter_command = callback_data.meter_command
    meter_serial = callback_data.meter_serial
    meter_id_uspd = callback_data.meter_id_uspd
    print(f'get_meters_serial. meter_command: {meter_command}, meter_serial: {meter_serial}, '
          f'meter_ID_USPD: {meter_id_uspd}')
    context_data = await state.get_data()
    current_state = context_data.get('current_state')
    print(f'current_state = {current_state}')

    # Создаем запрос, выстаскиваем все показатели для выбранного серийника
    connection = create_db_connection()
    if not connection:
        return

    cursor = connection.cursor()

    if meter_id_uspd == 0:  # счетчик, не привязанный ко вводу, к УСПД (USD)
        # Выбираем необходимые поля, основная таблица - MeterInfo, MeterMountHist и PointParams.
        # Условие на MeterInfo.SN = meter_serial
        cursor.execute(f' select pparams.ID_PP, pparams.ParamName, pparams.ShortName '
                       f' from '
                       f'(select mi.ID_MeterInfo, mi.SN from MeterInfo as mi where mi.SN = {meter_serial}) as minfo '
                       f' left join '
                       f'(SELECT ID_Point, ID_MeterInfo FROM MeterMountHist where ID_Module is NULL) '
                       f' as mmh on mmh.ID_MeterInfo = minfo.ID_MeterInfo '
                       f' left join (select pp.ID_PP, pp.ID_Param, pp.ID_Point, ppt.ParamName, ppt.ID_ValueType, '
                       f' ppt.ShortName from (select ID_PP, ID_Point, ID_Param from PointParams where ManuIn = 1) as pp'
                       f' left join (select pointpt.ParamName, pointpt.ID_Param, pointpt.ID_ValueType, units.ShortName '
                       f'from PointParamTypes as pointpt left join (select vt.ID_ValueType, u.ShortName from ValueTypes'
                       f' as vt left join Units as u on vt.ID_BaseUnits = u.ID_Units) as units '
                       f' on pointpt.ID_ValueType = units.ID_ValueType) as ppt on pp.ID_Param = ppt.ID_Param) '
                       f' as pparams on mmh.ID_Point = pparams.ID_Point'
                       )
    else:
        # Выбираем необходимые поля, основная таблица - Channels_Main.
        cursor.execute(f"SELECT ID_Channel, ID_USPD, Name, u.ShortName as Unit "
                       f" FROM Channels_Main as c left join Units as u on c.ID_Units = u.ID_Units where "
                       f" TypeChan in ('B','S','M','C') and NumChan = 1 and ID_USPD = {meter_id_uspd}"
                       )
    main_results = cursor.fetchall()

    for row in main_results:
        print(row)

    # закрываем соединение
    connection.close()

    # Строим следующую инлайн-клавиатуру, где кнопки - это показатели для выбранного серийника
    await call.message.answer(f"Выбран счетчик '{meter_serial}'.\n {call.from_user.first_name}, "
                              f"выберите показатель для внесения:",
                              reply_markup=get_meters_parameter_keyboard(main_results, meter_id_uspd, meter_serial))

    # Апдейтим текущее состояние current_state в state: FSMContext
    await state.update_data(current_state='state_get_meter_parameter')
    # Записываем в состояние серийный номер и УСПД.
    await state.update_data(meter_serial=meter_serial)
    await state.update_data(meter_id_uspd=meter_id_uspd)
    # Переводим FSM в состояние state_get_meter_serial
    await state.set_state(MetersEntries.get_meter_parameter)
    await call.answer()


# Функция вызывается при выборе определенного параметра счетчика в состоянии MetersEntries.state_get_meter_parameter,
# установленном в функции get_meters_serial на предыдущем шаге выбора серийного номера счетчика.
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

    # Запрашиваем величину показателя
    await call.message.answer(f"Выбран счетчик '{meter_serial}'.\n "
                              f"{call.from_user.first_name}, введите величину показателя:")

    # Переводим FSM в состояние state_get_meter_value
    await state.update_data(current_state='state_get_meter_value')
    await state.update_data(meter_id_channel=meter_id_channel)
    await state.update_data(meter_id_pp=meter_id_pp)
    # await state.update_data(meter_parameter_name=meter_parameter_name)
    await state.set_state(MetersEntries.get_meter_value)
    await call.answer()


async def write_meters_value(message: Message, state: FSMContext):
    print(f'Данные состояния state: {await state.get_data()}')
    print(f'Само состояние state: {await state.get_state()}')

    state_data = await state.get_data()

    # Сохраняем введенное имя в хранилище по ключу "value"
    meter_value = float(message.text.replace(',', '.'))
    # Вытаскиваем meter_id_pp, meter_serial, meter_id_channel, meter_parameter_name из сохраненного значения state_data
    meter_id_pp = state_data['meter_id_pp']
    meter_serial = state_data['meter_serial']
    meter_id_channel = state_data['meter_id_channel']
    meter_id_uspd = state_data['meter_id_uspd']
    # meter_parameter_name = state_data['meter_parameter_name']

    await state.update_data(value=message.text)
    await message.answer(text=f"Выбран счетчик '{meter_serial}'.\n"
                              f"Введена величина {message.text}")

    # Создаем запрос, выстаскиваем все показатели для выбранного серийника
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

        query_text = (f"DECLARE	@return_curdate datetime, @return_nearest_date datetime, @DT_Old datetime, @Val float,\n "
                      f" @Val_old float, @Minutes int, @return_value int, @IsAdded tinyint, @State int = 0, \n"
                      f" @ID_PP int = 0 \n"
                      f" set @Minutes = 30 \n"
                      f" set @State = 16384 \n"
                      f" set @ID_PP = {meter_id_pp} \n"
                      f" set @Val = {meter_value} \n"
                      f"-- находим текущую дату \n"
                      f" EXEC	@return_curdate = [dbo].[FncGetDate] \n"
                      f"-- запускаем процедуру для вытаскивания последнего значения и последней даты, запоминаем их \n "
                      f" SELECT top 1 @DT_Old = DT, @Val_Old = Val \n"
                      f" FROM dbo.PP_NIs_PP({meter_id_pp}, null, @return_curdate) ORDER BY DT DESC\n "
                      f"-- округляем дату до ближайшего временного интервала \n "
                      f"EXEC @return_nearest_date = [dbo].[DT_RoundDateTimeToNearestInterval] @return_curdate, @Minutes\n"
                      f"-- записываем новое значение в PointNIs_On_Main_Stack через ХП \n "
                      f" EXEC	@return_value = [dbo].[PP_NIs_Write_PP]	@ID_PP,	@DT = @return_nearest_date,	\n"
                      f" @Val = @Val, @State = @State\n"
                      f"-- записываем в логи P_Log_Nfo, P_Log_IDs старые и новые значения \n "
                      f" DECLARE @ID_Log int\n"
                      f" EXEC P_Log_HI @ID_Log out, @ID_PP, 5, "
                      f" @return_nearest_date, @DT_Old, @return_nearest_date, @Val, @Val_Old, Null ")
        # query_text = (
        #     f" SET NOCOUNT ON; DECLARE @return_value int "
        #     f" EXEC @return_value = dbo.PP_NIs_Write_PP 12, N'20230907 17:30:00', 8089, 16384 \n"
        #     f" select  @return_value "
        #     )

        cursor.execute(query_text)

        # main_result = cursor.fetchall()
        # print(main_result)
        # print(cursor.rowcount)
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



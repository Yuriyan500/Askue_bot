from aiogram.types import CallbackQuery
from utils.callbackdata import MetersInfo
from utils.dbconnect import create_db_connection
from datetime import datetime
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


class MetersEntries(StatesGroup):
    get_meter_number = State()
    get_meter_parameter = State()
    get_meter_value = State()


async def select_meters_commands(call: CallbackQuery, callback_data: MetersInfo):
    meter_number = callback_data.meter_number
    print(f'meter_number: {meter_number}')

    if meter_number == 'all_meters':
        await all_meters_readings(call)
    elif meter_number == 'make_entries_for_meters':
        await make_entries_for_meters(call)
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
    # Тип получаемых ограничиваем 29,30 - активная энергия и объём воды
    cursor.execute('SELECT c.ID_Channel as id, usd.Name as Name_USD, usd.TypeUSD as Type_USD, c.Name as '
                   'Channel_Name, 0 as res_value, u.ShortName as Unit, v.ShortName as Channel_Short_Name'
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

        # нас интересует одна строка результата
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
        str_results = str_results + ', '.join(str(x) for x in row) + '\n'

    print('str_results:', str_results)

    # закрываем соединение
    connection.close()

    await call.message.answer(str_results)
    await call.answer()


async def make_entries_for_meters(call):
    # Здесь будем действовать через FSMContext:
    # - запросить № счетчика,
    # - запросить показатель (например, активная энергия),
    # - ввести значение в базу

    connection = create_db_connection()
    if not connection:
        return

    # строка (пока строка) для возвращения результата
    str_results = 'test'
    date_today = datetime.today().strftime('%Y%m%d')

    cursor = connection.cursor()

    print('str_results:', str_results)

    # закрываем соединение
    connection.close()

    await call.message.answer(str_results)
    await call.answer()

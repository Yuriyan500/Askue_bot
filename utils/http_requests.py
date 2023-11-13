import requests
from requests.exceptions import ConnectionError, ConnectTimeout
from datetime import datetime
import time
from aiogram.types import Message
from utils.dbconnect import create_db_connection
from utils.querytexts import (return_max_date_and_id_query, return_serial_and_id_query,
                              write_meters_value_for_specific_half_hour_query)


async def make_request(message: Message):
    url = 'http://172.17.5.27/?1;123;2'
    try:
        html_content = requests.get(url, timeout=(1, 2))  # 172.17.5.27

        data = html_content.json()
        print('data: ', data)

        ticks_list = []

        for html_tag in data:
            print(html_tag.keys())
            print(html_tag.values())
            print(html_tag.items())
            ticks_list.extend([value for key, value in html_tag.items() if key == 'ticks'])

        print(ticks_list)

        print(time.ctime())

        html_content.close()

    except ConnectTimeout:
        print('REQUEST CONNECTION ERROR')
    except ConnectionError:
        print('REQUEST CONNECTION TIMEOUT')


async def make_scheduled_request():

    general_result = []

    # Создаем запрос, вытаскиваем максимальную дату DT для каждого ID_PP из таблицы [PointNIs_On_Main_Stack]
    # БД Энергосферы
    connection = create_db_connection()
    if not connection:
        return

    cursor = connection.cursor()

    query_text = return_max_date_and_id_query()
    cursor.execute(query_text)

    main_results = cursor.fetchall()

    for row_main in main_results:
        # результат запроса запишем в список словарей general_result
        general_result.append(dict(ID_PP=row_main.ID_PP, DT=row_main.DT))

    # теперь из базы вытащим соответствие серийного номера и ID_PP
    query_text = return_serial_and_id_query()
    cursor.execute(query_text)

    serial_id_results = cursor.fetchall()

    for row_sn in serial_id_results:
        # запишем в каждый словарь из списка general_result серийный номер SN
        dict_founded = next(item for item in general_result if item['ID_PP'] == row_sn.ID_PP)
        dict_founded['SN'] = row_sn.SN

        # добавим к каждому словарю представление даты DT в формате unix timestamp
        d = datetime.date(dict_founded['DT'])
        dict_founded['DT_unix_time'] = time.mktime(d.timetuple())

        # Здесь же запишем коэффициент для импульсов каждого счетчика. Зависит от серийного номера счетчика,
        # а именно: счетчики с номерами 1169, 6737, 1305 - 600 импульсов на 1 кВт/ч, 1089 - 400 импульсов на 1 кВт/ч
        if dict_founded['SN'] == 1089:
            dict_founded['coefficient'] = 400
        else:
            dict_founded['coefficient'] = 600

    # получим текущее время и найдем количество получасовок для каждой записи списка general_result
    now = time.time()

    for current_dict in general_result:
        half_hour_quant = (now - current_dict['DT_unix_time']) // 1800
        if half_hour_quant <= 0:
            current_dict['half_hour_quant'] = 0
        else:
            current_dict['half_hour_quant'] = min(10, half_hour_quant)
        print(f"current_dict.SN = {current_dict['SN']}, current_dict.DT = {current_dict['DT']}, "
              f"current_dict.ID_PP = {current_dict['ID_PP']}, "
              f"current_dict.DT_unix_time = {current_dict['DT_unix_time']}, "
              f"current_dict.half_hour_quant = {current_dict['half_hour_quant']}, "
              f"current_dict.coefficient = {current_dict['coefficient']}")

    # теперь будем перебирать список general_result и для каждой записи делать request-запрос с параметрами
    for current_dict in general_result:

        url = f"http://172.17.5.27/?{current_dict['SN']};{current_dict['DT_unix_time']};{current_dict['half_hour_quant']}"

        try:
            html_content = requests.get(url, timeout=(1, 10))  # 172.17.5.27

            data = html_content.json()
            print('data: ', data)

            ticks_list = []
            time_list = []

            transaction = connection.begin()

            for html_tag in data:
                print('')
                print('html_tag: ', html_tag)
                # ticks_list.extend([value for key, value in html_tag.items() if key == 'ticks'])
                # time_list.extend([value for key, value in html_tag.items() if key == 'time'])

                # анализируем в первую очередь status, при значении False - не пишем за эту получасовку в базу ничего
                if not html_tag['status']:
                    continue

                meter_value = html_tag['ticks'] // current_dict['coefficient']

                sql_time = datetime.fromtimestamp(html_tag['time']).strftime('%Y-%m-%d %H:%M:%S')

                query_text = write_meters_value_for_specific_half_hour_query(html_tag['number'], sql_time, meter_value)

                cursor.execute(query_text)

            # TODO - разобраться с возможными вариантами возвращаемого результата выполнения
            #  команды cursor.execute(query_text) и корректно их отработать
            try:
                transaction.commit()
            except Exception as E:
                print(f"The error {E} is occurred!")
                transaction.rollback()

            # print('ticks_list: ', ticks_list)
            # print('time_list: ', time_list)

            for time_tag in time_list:
                sql_time = datetime.fromtimestamp(time_tag).strftime('%Y-%m-%d %H:%M:%S')
                print('sql_time', sql_time)

            # print(time.ctime())

            html_content.close()
            print(html_content.status_code)
            time.sleep(1)

        except ConnectTimeout:
            print('REQUEST CONNECTION ERROR')
        except ConnectionError:
            print('REQUEST CONNECTION TIMEOUT')


def all_meters_readings_query_usd():
    # Выбираем необходимые поля, основная таблица - Channels_Main - данные, получаемые с УСПД.
    # Тип получаемых ограничиваем 29, 20 - активная энергия и объём воды
    query_text = (f'SELECT c.ID_Channel as id, usd.Name as Name_USD, usd.TypeUSD as Type_USD, c.Name as '
                  f'Channel_Name, 0 as res_value, u.ShortName as Unit '
                  f'FROM Channels_Main as c '
                  f'left join Units as u on c.ID_Units = u.ID_Units '
                  f'left join ValueTypes as v on c.ID_ValueType = v.ID_ValueType '
                  f'left join USD as usd on c.ID_USPD = usd.ID_USPD '
                  f'where c.ID_ValueType in (29, 20) ')

    return query_text


def all_meters_readings_query_manual():
    # Запрос для счетчиков, данные для которых вводятся вручную через "Ручной ввод".
    # Данные по таким счетчикам хранятся в PointNIs_On_Main_Stack, вытаскивать их будем через функцию PP_NIs_PP,
    # для которой на вход нужен ID_PP, поэтому в дополнение к основной информации о таком счетчике (название и серийный
    # номер) добираемся до ID_PP
    query_text = (' select minfo.SN as SN, minfo.NameType as NameType, pp.ID_PP, pp.ParamName as ParamName, '
                  'pp.ShortName as Unit, 0 as res_value '
                  'from (SELECT ID_MMH, ID_Point, ID_MeterInfo FROM MeterMountHist where ID_Module is NULL) as mmh '
                  'left join (select mi.ID_MeterInfo, mi.SN, mt.NameType from MeterInfo as mi '
                  'left join ModuleTypes as mt on mi.ID_ModuleType = mt.ID_Type) as minfo '
                  'on mmh.ID_MeterInfo = minfo.ID_MeterInfo '
                  'left join (select pp.ID_PP, pp.ID_Point, ppt.ParamName, ppt.ShortName from PointParams as pp '
                  '        left join (select ppt.ParamName, ppt.ID_Param, units.ShortName from PointParamTypes as ppt '
                  '                    left join (select vt.ID_ValueType, u.ShortName from ValueTypes as vt '
                  '                                left join Units as u on vt.ID_BaseUnits = u.ID_Units) as units '
                  '            on ppt.ID_ValueType = units.ID_ValueType) as ppt on pp.ID_Param = ppt.ID_Param) '
                  'as pp on mmh.ID_Point = pp.ID_Point '
                  'where minfo.SN is not NULL ')
    return query_text


def meters_readings_query_usd_with_id(id_uspd):
    # Выбираем необходимые поля, основная таблица - Channels_Main - данные, получаемые с УСПД.
    # Тип получаемых ограничиваем 29, 20 - активная энергия и объём воды
    query_text = (f'SELECT c.ID_Channel as id, usd.Name as Name_USD, usd.TypeUSD as Type_USD, c.Name as '
                  f'Channel_Name, 0 as res_value, u.ShortName as Unit '
                  f'FROM Channels_Main as c '
                  f'left join Units as u on c.ID_Units = u.ID_Units '
                  f'left join ValueTypes as v on c.ID_ValueType = v.ID_ValueType '
                  f'left join USD as usd on c.ID_USPD = usd.ID_USPD '
                  f'where c.ID_ValueType in (29, 20) and c.ID_Units in (61, 26) '
                  f'and c.NumChan = 1 and c.ID_USPD = {id_uspd}')

    return query_text


def meters_readings_query_manual_with_serial(meter_serial):
    # Запрос для счетчиков, данные для которых вводятся вручную через "Ручной ввод".
    # Данные по таким счетчикам хранятся в PointNIs_On_Main_Stack, вытаскивать их будем через функцию PP_NIs_PP,
    # для которой на вход нужен ID_PP, поэтому в дополнение к основной информации о таком счетчике (название и серийный
    # номер) добираемся до ID_PP
    query_text = (f' select minfo.SN as SN, minfo.NameType as NameType, pp.ID_PP, pp.ParamName as ParamName, '
                  f'pp.ShortName as Unit, 0 as res_value '
                  f'from (SELECT ID_MMH, ID_Point, ID_MeterInfo FROM MeterMountHist where ID_Module is NULL) as mmh '
                  f'left join (select mi.ID_MeterInfo, mi.SN, mt.NameType from MeterInfo as mi '
                  f'left join ModuleTypes as mt on mi.ID_ModuleType = mt.ID_Type where mi.SN = {meter_serial}) as minfo '
                  f'on mmh.ID_MeterInfo = minfo.ID_MeterInfo '
                  f'left join (select pp.ID_PP, pp.ID_Point, ppt.ParamName, ppt.ShortName from PointParams as pp '
                  f'        left join (select ppt.ParamName, ppt.ID_Param, units.ShortName from PointParamTypes as ppt '
                  f'                    left join (select vt.ID_ValueType, u.ShortName from ValueTypes as vt '
                  f'                                left join Units as u on vt.ID_BaseUnits = u.ID_Units) as units '
                  f'            on ppt.ID_ValueType = units.ID_ValueType) as ppt on pp.ID_Param = ppt.ID_Param) '
                  f'as pp on mmh.ID_Point = pp.ID_Point '
                  f'where minfo.SN is not NULL ')
    return query_text


def meters_serial_query():
    # Запрос на выборку счетчиков и их серийных номеров.
    # Выбираем необходимые поля, основная таблица - MeterMountHist.
    query_text = ('SELECT mmh.ID_MMH, mi.SN, mi.NameType, usds.Name, usds.ID_USPD '
                  'FROM MeterMountHist mmh '
                  'left join (SELECT mi.ID_MeterInfo, mt.NameType, mi.SN '
                  '            FROM MeterInfo as mi left join ModuleTypes as mt on mi.ID_ModuleType = mt.ID_Type '
                  '            where SN is not NULL) mi on mmh.ID_MeterInfo = mi.ID_MeterInfo '
                  ' left join '
                  ' (SELECT m.ID_Module, m.ID_USPD, u.Name FROM Modules m left join USD u on m.ID_USPD = u.ID_USPD) '
                  ' usds on mmh.ID_Module = usds.ID_Module '
                  ' where mi.SN is not NULL '
                  ' order by ID_MMH ')
    return query_text


def meter_value_query_manual(meter_serial):

    if not meter_serial:
        return ''

    # Запрос на вывод возможных показателей для серийника meter_serial, выбранного на предыдущем шаге FSM.
    # В данном случае находятся показатели для счетчиков, данные по которым вводятся вручную
    query_text = (f" select pparams.ID_PP, pparams.ParamName, pparams.ShortName "
                  f" from "
                  f"(select mi.ID_MeterInfo, mi.SN from MeterInfo as mi where mi.SN = {meter_serial}) as minfo "
                  f" left join "
                  f"(SELECT ID_Point, ID_MeterInfo FROM MeterMountHist where ID_Module is NULL) "
                  f" as mmh on mmh.ID_MeterInfo = minfo.ID_MeterInfo "
                  f" left join (select pp.ID_PP, pp.ID_Param, pp.ID_Point, ppt.ParamName, ppt.ID_ValueType, "
                  f" ppt.ShortName from (select ID_PP, ID_Point, ID_Param from PointParams where ManuIn = 1) as pp"
                  f" left join (select pointpt.ParamName, pointpt.ID_Param, pointpt.ID_ValueType, units.ShortName "
                  f"from PointParamTypes as pointpt left join (select vt.ID_ValueType, u.ShortName from ValueTypes"
                  f" as vt left join Units as u on vt.ID_BaseUnits = u.ID_Units) as units "
                  f" on pointpt.ID_ValueType = units.ID_ValueType) as ppt on pp.ID_Param = ppt.ID_Param) "
                  f" as pparams on mmh.ID_Point = pparams.ID_Point"
                  )
    return query_text


def meter_value_query_usd(meter_id_uspd):
    if not meter_id_uspd:
        return ''

    # Запрос на вывод возможных показателей для серийника meter_serial, выбранного на предыдущем шаге FSM.
    # В данном случае находятся показатели для счетчиков, данные по которым опрашиваются через УСПД
    query_text = (f"SELECT ID_Channel, ID_USPD, Name, u.ShortName as Unit "
                  f" FROM Channels_Main as c left join Units as u on c.ID_Units = u.ID_Units where "
                  f" TypeChan in ('B','S','M','C') and NumChan = 1 and ID_USPD = {meter_id_uspd}"
                  )
    return query_text


def write_meters_value_query_manual(meter_id_pp, meter_value):

    if not meter_id_pp:
        return ''

    query_text = (
        f"DECLARE	@return_curdate datetime, @return_nearest_date datetime, @DT_Old datetime, @Val float,\n "
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
    return query_text


def write_meters_value_for_specific_half_hour_query(meter_id_pp, sql_time, meter_value):

    if not meter_id_pp:
        return ''

    query_text = (
        f"DECLARE	@return_curdate datetime, @return_half_hour datetime, @return_nearest_date datetime, "
        f" @DT_Old datetime, @Val float,\n "
        f" @Val_old float, @Minutes int, @return_value int, @IsAdded tinyint, @State int = 0, \n"
        f" @ID_PP int = 0 \n"
        f" set @Minutes = 30 \n"
        f" set @State = 16384 \n"
        f" set @ID_PP = {meter_id_pp} \n"
        f" set @Val = {meter_value} \n"
        f" set @return_half_hour = {sql_time} \n"
        f"-- находим текущую дату \n"
        f" EXEC	@return_curdate = [dbo].[FncGetDate] \n"
        f"-- запускаем процедуру для вытаскивания последнего значения и последней даты, запоминаем их \n "
        f" SELECT top 1 @DT_Old = DT, @Val_Old = Val \n"
        f" FROM dbo.PP_NIs_PP({meter_id_pp}, null, @return_curdate) ORDER BY DT DESC\n "
        f"-- округляем дату до ближайшего временного интервала \n "
        f"EXEC @return_nearest_date = [dbo].[DT_RoundDateTimeToNearestInterval] @return_half_hour, @Minutes\n"
        f"-- записываем новое значение в PointNIs_On_Main_Stack через ХП \n "
        f" EXEC	@return_value = [dbo].[PP_NIs_Write_PP]	@ID_PP,	@DT = @return_nearest_date,	\n"
        f" @Val = @Val, @State = @State\n"
        f"-- записываем в логи P_Log_Nfo, P_Log_IDs старые и новые значения \n "
        f" DECLARE @ID_Log int\n"
        f" EXEC P_Log_HI @ID_Log out, @ID_PP, 5, "
        f" @return_nearest_date, @DT_Old, @return_nearest_date, @Val, @Val_Old, Null ")
    return query_text

def return_max_date_and_id_query():

    query_text = (
        f"SELECT t1.* FROM [PointNIs_On_Main_Stack] t1"
        f"  LEFT OUTER JOIN [PointNIs_On_Main_Stack] t2"
        f"    ON (t1.ID_PP = t2.ID_PP AND t1.DT < t2.DT)"
        f"WHERE t2.ID_PP IS NULL and t1.ID_PP in (9, 10, 12, 31)"
    )
    return query_text


def return_serial_and_id_query():

    query_text = (
        f"select minfo.SN, mmh.ID_Point, pparams.ID_PP "
        f"from (select mi.ID_MeterInfo, mi.SN from MeterInfo as mi where mi.SN in (1305, 1089, 1169, 6737)) as minfo "
        f"left join ( "
        f"SELECT ID_Point, ID_MeterInfo FROM MeterMountHist where ID_Module is NULL "
        f") as mmh on mmh.ID_MeterInfo = minfo.ID_MeterInfo "
        f"left join "
        f"( "
        f"select pp.ID_PP, pp.ID_Point from (select ID_PP, ID_Point from PointParams where ManuIn = 1) as pp "
        f") as pparams on mmh.ID_Point = pparams.ID_Point "
    )
    return query_text

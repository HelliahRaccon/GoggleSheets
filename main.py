from urllib.request import urlopen
from xml.etree import ElementTree as ETree
from datetime import date, datetime
import time

from oauth2client.service_account import ServiceAccountCredentials
import httplib2
from apiclient import discovery
import psycopg2
import telebot


# Получение актуального курса доллара по ЦБ РФ
def get_course():
    with urlopen("https://www.cbr.ru/scripts/XML_daily.asp", timeout=10) as r:
        course = ETree.parse(r).findtext('.//Valute[@ID="R01235"]/Value')
    return float(course.split(',')[0] + '.' + course.split(',')[1])



# Получение и редактирование данных
def get_values():
    # Подключение к Google Sheets
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'creds.json',
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive']
    )
    http_auth = credentials.authorize(httplib2.Http())
    service = discovery.build('sheets', 'v4', http=http_auth)

    # Получение данных
    values = service.spreadsheets().values().get(
        spreadsheetId='1bp5Ixxg9fgfaVTxOoUifo5mfcyXbxL6VJiaCbg9kMh8',
        range='A2:D',
        majorDimension='ROWS'
    ).execute()

    # Получение курса и редактирование данных
    course = get_course()
    for value in values['values']:
        value[3] = "DATE '" + value[3].split('.')[2] + '-' + value[3].split('.')[1] + '-' + value[3].split('.')[0] + "'"
        value.append(str(round(int(value[2]) * course, 2)))
        value[3], value[4] = value[4], value[3]
    return values['values']


# Подключение к базе данных и отправка данных
def push_db(DATABASES):
    # Подключение к базе данных
    con = psycopg2.connect(
        database=DATABASES['NAME'],
        user=DATABASES['USER'],
        password=DATABASES['PASSWORD'],
        host=DATABASES['HOST'],
        port=DATABASES['PORT'],
        # DATABASES,
    )
    cur = con.cursor()

    cur.execute("delete from home_GoogleSheets;")

    for value in get_values():
        # Ищем number_id
        some_number_id = cur.execute("select * from home_GoogleSheets where number_id = %s", (value[1],))
        # Получение даты и сравнение её с текущей
        data_value = value[4].split("'")[1].split('-')
        if int(data_value[0]) < datetime.now().year:
            send_db_message(408, value[1])
        else:
            if int(data_value[1]) < datetime.now().month:
                send_db_message(408, value[1])
            else:
                if (int(data_value[1]) == datetime.now().month) and (int(data_value[2]) < datetime.now().day):
                    send_db_message(408, value[1])

        # Если number_id не найден, то создаем новую запись
        if str(some_number_id) == None:
            print('l;ko')
            cur.execute(
                f"INSERT INTO home_GoogleSheets(id, number_id, price_dollar, price_rub, data_get) VALUES ({value[0]}, {value[1]}, {value[2]}, {value[3]}, {value[4]});")
        # else: # Если number_id найден, то проверям данные, если есть изменения, то записываем
        #     last_value = cur.fetchall()[0]
        #     if last_value[3] != float(value[3]):
        #         cur.execute(
        #             f"UPDATE home_GoogleSheets SET price_rub = {value[3]} where number_id = {value[1]};"
        #         )
        #     if last_value[2] != float(value[2]):
        #         cur.execute(
        #             f"UPDATE home_GoogleSheets SET price_dollar = {value[2]} where number_id = {value[1]};"
        #         )
        #     if last_value[0] != float(value[0]):
        #         cur.execute(
        #             f"UPDATE home_GoogleSheets SET id = {value[0]} where number_id = {value[1]};"
        #         )
        #     if str(last_value[4]) != value[4].split("'")[1]:
        #         cur.execute(
        #             f"UPDATE home_GoogleSheets SET data_get = {value[4]} where number_id = {value[1]};"
        #         )
    
    con.commit()
    con.close()

    # Раскометировать для получения сообщений об обновлении базы данных
    # send_db_message(200)


# Блок относится к запуску телеграмм бота
# Создаем экземпляр бота
bot = telebot.TeleBot('5530513392:AAG89CLkxSe_ytQvCMTJQZOfRF-NqbOov4A')


def send_db_message(code, failed_values=None):
    if code == 200:
        message_failed = 'База данных обновлена без ошибок'
    elif code == 408:
        message_failed = 'Просроченная дата у заказа номер: ' + str(failed_values)
    file = open("chats_ud.txt", "r")
    for chat_id in file:
        try:
            bot.send_message(chat_id, message_failed)
        finally:
            pass



# Данные для подключения к PostgreSQL
DATABASES = {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'ec2-34-227-120-79.compute-1.amazonaws.com',
        'NAME': 'dd212sl28fmep8',
        'USER': 'blaglwvvggtjyy',
        'PORT': '5432',
        'PASSWORD': '612f14c4e9d39173c3bda4c94199a5f211b16ae871e41bdec620b5e3d6c62685',
    }

# Счетчик итераций
i = 0
# Обновление базы данных
while True:
    push_db(DATABASES)
    print('Iteration: ', i)
    i += 1
    time.sleep(60)

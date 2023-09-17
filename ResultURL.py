from urllib.parse import urlparse
import hashlib
import decimal
import datetime
import sqlite3


# Получение уведомления об исполнении операции (ResultURL).
def parse_response(request: str) -> dict:
    """
    :param request: Link.
    :return: Dictionary.
    """
    params = {}

    for item in urlparse(request).query.split('&'):
        key, value = item.split('=')
        params[key] = value
    return params


def calculate_signature(*args) -> str:
    """Create signature MD5.
    """
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


def check_signature_result(
    order_number: int,  # invoice number
    received_sum: decimal,  # cost of goods, RU
    received_signature: hex,  # SignatureValue
    password: str  # Merchant password
) -> bool:
    signature = calculate_signature(received_sum, order_number, password)
    if signature.lower() == received_signature.lower():
        return True
    return False


def create_table():
    connect = sqlite3.connect("db.db")
    cursor = connect.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      user_name TEXT,
                      tarif TEXT
                   )''')
    connect.commit()
def add(user_id, user_name, tarif, expiration_date):
    create_table()
    #подключаем нашу базу данных
    connect = sqlite3.connect("db.db")
    #курсор для работы с таблицами
    cursor = connect.cursor()
    cursor.execute('INSERT INTO subscriptions (user_id, user_name, tarif, expiration_date) VALUES (?, ?, ?, ?)',
                   (user_id, user_name, tarif, expiration_date))
    connect.commit()

def result_payment(merchant_password_2: str, request: str) -> str:
    """Verification of notification (ResultURL).
    :param request: HTTP parameters.
    """
    param_request = parse_response(request)
    cost = param_request['OutSum']
    number = param_request['InvId']
    signature = param_request['SignatureValue']

    #успех
    if check_signature_result(number, cost, signature, merchant_password_2):
        #разрезаем число на нужные данные
        str_num = str(number)
        len_user = int(str_num[0])
        player_id = str_num[1:len_user + 1]
        len_button = int(str_num[len_user + 1])
        button = int(str_num[len_user + 2:len_user + 2 + len_button])
        days = int(str_num[len_user + len_button + 2:])

        #bot.send_message(player_id, "Поздравляем с покупкой!")

        # Получить текущую дату и время
        current_datetime = datetime.datetime.now()
        # Преобразовать текущую дату и время в текстовый формат (строку)
        #current_datetime_text = current_datetime.strftime("%d.%m.%Y %H:%M:%S")
        # Прибавить нужный тариф
        if days == 1:
            expiration = current_datetime + datetime.timedelta(days=1)
        elif days == 30: # Прибавить месяц
            expiration = current_datetime.replace(month=current_datetime.month + 1)
        else: # Прибавить год
            expiration = current_datetime.replace(year=current_datetime.year + 1)

        # Преобразовать новые даты и время в текстовый формат (строку)
        one_month_later_text = expiration.strftime("%d.%m.%Y %H:%M:%S")

        all_names_of_tarifs = ['Демка', 'База', 'СССР', 'Котики', 'НЕЙРО']
        if len_button < 3:
            text = all_names_of_tarifs[button]
            add(player_id, "sakuharo", text, one_month_later_text)
        else:
            for text in all_names_of_tarifs[1:]:
                add(player_id, "sakuharo", text, one_month_later_text)

        return f'OK{param_request["InvId"]}'
    return "bad sign"


# Проверка параметров в скрипте завершения операции (SuccessURL).

def check_success_payment(merchant_password_1: str, request: str) -> str:
    """ Verification of operation parameters ("cashier check") in SuccessURL script.
    :param request: HTTP parameters
    """
    param_request = parse_response(request)
    cost = param_request['OutSum']
    number = param_request['InvId']
    signature = param_request['SignatureValue']


    if check_signature_result(number, cost, signature, merchant_password_1):
        return "Thank you for using our service"
    return "bad sign"
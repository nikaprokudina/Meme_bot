#Timer 2 рабочие
import telebot
import random
import string
import math
from telebot import types
from io import BytesIO
from PIL import Image
import requests
import concurrent.futures
import io
import threading
import sqlite3

import decimal
import hashlib
from urllib import parse
from collections import OrderedDict
import datetime
import copy




bot = telebot.TeleBot("6227889329:AAHP40wbfEJ0ZWgMCb7tqGBT9DoDtLWfOKY")
#bot = telebot.TeleBot("6478379933:AAG_OaYSRm0vZDIT565vT4aON5v6_oyFtmU") #guy



# Словарь для хранения активных игр
active_games = {}
cards_on_table = {}
battle_cards = {} #голоса за карты
kolvo_players_that_send_mem = {}
voted_players = {}
players_order = {}
id_and_names = {} #по id можно расшифровать имя игрока

photo_bar_players = {}

# Словарь для хранения сообщения списка игроков
message_list_of_players = {}
usernames = {}
rating = {} #действующий рейтинг игроков (если игроков мало, то среди них есть бот
flag_vse_progolos = {}
flag_pl_otpravil = {}
messages_ids = {}
all_combined_images = {}
blank_table = {} #пустой стол голсования
chosen_photos = {}
#chosen_memes = {}
players_hand = {}

#все доступные тарифы meme 0,1,2,3,4
all_available_tarifs_memes = {}
nazat_tarifs_memes = {}

all_available_tarifs_sit = {}
nazat_tarifs_sit = {}

deck_of_sit_cards = {}
trash_sit = {}

deck_of_meme_cards = {} #колода карт мемов в игре
trash_memes = {} #сброс мемов

#запонимнаем список игроков с прошлого раунда
remember_players = {}

mozno_li_nazat_gotovo = {}
mozno_obnovlat = {}

ids_chose_lots_all = {} #хранение всех id сообщений с выбором лотов, которые нужно будет удалить после нажатия на кнопку обновить
now_obnov = {} #содержится в ids_3_otmena отмена или обновть

ids_3_otmena = {}
robocassa_first_time = {} #bool нажата ли робокасса или нет

ids_3_gotovo = {} #словарь, где хранятся 3 id сообщений с кнопками (выбор мемов и ситуаций) + кнопка готово
mozno_nazad_v_menu = {}



# Создаем блокировку для синхронизации доступа к словарю message_list_of_players
message_list_lock = threading.Lock()

def send_message_to_players(game_code, message):
    players = active_games[game_code]['players']
    for player_id in players:
        bot.send_message(player_id, message)

def create_players_message(game_code, creator_id):
    players = active_games[game_code]['players']
    users = active_games[game_code]['usernames']
    name = id_and_names[game_code][creator_id]
    message = "Игроки:\n" + "\n".join(users)

    #message = f"Игроки:\n{name}"
    mes = bot.send_message(creator_id, message)
    message_id = mes.message_id
    with message_list_lock:
        message_list_of_players[game_code] = {}
        message_list_of_players[game_code][creator_id] = message_id


def update_players_message(game_code, new_player_id, creator_name):
    players = active_games[game_code]['players']
    users = active_games[game_code]['usernames']

    message = "Игроки:\n" + "\n".join(users)

    for player_id in players:
        if new_player_id == player_id:
            if len(players) > 1:
                bot.send_message(player_id, text=f"Вы вошли в игру с кодом {game_code}!")
            mes = bot.send_message(player_id, message)
            message_id = mes.message_id
            if len(players) > 1:
                bot.send_message(player_id, text=f"Ждём, когда все зайдут и {creator_name} запустит игру")


            # Захватываем блокировку перед обновлением словаря
            with message_list_lock:
                message_list_of_players[game_code][new_player_id] = message_id
        else:
            # Захватываем блокировку перед чтением словаря
            with message_list_lock:
                message_id = message_list_of_players[game_code].get(player_id)

            if message_id is not None:
                bot.edit_message_text(chat_id=player_id, message_id=message_id, text=message)


def generate_game_code():
    code = ''.join(random.choices(string.digits, k=6))
    #return code
    return "000000"



# старт: присоединиться к игре или создать новую
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    new_game_button = types.InlineKeyboardButton("Новая игра", callback_data="new_game")
    join_game_button = types.InlineKeyboardButton("Присоединиться к игре", callback_data="join_game")
    rules_button = types.InlineKeyboardButton("Правила игры", callback_data="rules")
    markup.add(new_game_button, join_game_button, rules_button)
    bot.send_message(message.chat.id, text="Добро пожаловать! Я мемобот:)", reply_markup=markup)


#выход в главное меню и удаление игры из активных, если ушёл криэйтор
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('menu:'))
def main_menu(callback_query):
    data = callback_query.data.split(':')
    player_id = callback_query.from_user.id
    game_code = data[1]
    #удаляем прошлое сообщение
    message_id = callback_query.message.message_id
    bot.delete_message(player_id, message_id)

    if game_code in active_games and player_id == active_games[game_code]['creator']:
        delete_stuff(game_code)

        del id_and_names[game_code]

        del all_available_tarifs_memes[game_code]
        del nazat_tarifs_memes[game_code]
        del all_available_tarifs_sit[game_code]
        del nazat_tarifs_sit[game_code]
        del deck_of_sit_cards[game_code]
        del trash_sit[game_code]
        del deck_of_meme_cards[game_code]
        del trash_memes[game_code]


    markup = types.InlineKeyboardMarkup(row_width=1)
    new_game_button = types.InlineKeyboardButton("Новая игра", callback_data="new_game")
    join_game_button = types.InlineKeyboardButton("Присоединиться к игре", callback_data="join_game")
    rules_button = types.InlineKeyboardButton("Правила игры", callback_data="rules")
    markup.add(new_game_button, join_game_button, rules_button)
    bot.send_message(player_id, text="А ну-ка, выбирай", reply_markup=markup)

# правила игры
@bot.callback_query_handler(func=lambda message: message.data == 'rules')
def rules(message):
    message_id = message.message.message_id
    player_id = message.message.chat.id
    bot.delete_message(player_id, message_id)

    game_code = -1
    callback_data_leave = f"menu:{game_code}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    back_button = types.InlineKeyboardButton("Назад в меню", callback_data=callback_data_leave)
    markup.add(back_button)
    bot.send_message(player_id, f"ляля тут будут правила", reply_markup=markup)


#смотрим на подписки юзера
def get_user_subscriptions(user_id):
    connect = sqlite3.connect("db.db")
    cursor = connect.cursor()

    cursor.execute('SELECT * FROM subscriptions WHERE user_id = ?', (user_id,))
    user_subscriptions = cursor.fetchall()

    connect.close()
    return user_subscriptions

@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('meme_tarif:'))
def chose_tarif_meme(callback_query):
    with message_list_lock:
        global all_available_tarifs_memes
        global nazat_tarifs_memes
        data = callback_query.data.split(':')
        player_id = callback_query.from_user.id
        game_code = data[1]
        button = int(data[2])

        #удаляем прошлое сообщение
        message_id = callback_query.message.message_id
        #bot.delete_message(player_id, message_id)
        if button not in all_available_tarifs_memes[game_code]:
            robocassa(player_id, button, game_code)
        else:
            if button not in nazat_tarifs_memes[game_code]: #кнопка ненажата -> нажата = зеленый
                nazat_tarifs_memes[game_code].append(button)
            else: #кнопка была нажата, теперь нет -> белый
                nazat_tarifs_memes[game_code].remove(button)
            logos = []
            for number in range(5): #проходимся по всем кнопкам
                if number in nazat_tarifs_memes[game_code]: #должна быть зелёной
                    logos.append("🟢️ ")
                elif number in all_available_tarifs_memes[game_code]: #доступна, но не нажата (белый)
                    logos.append("⚪️ ")
                else: #замок
                    logos.append("💰")

            # выбор мемов
            demo_meme = f"meme_tarif:{game_code}:{0}"
            base_meme = f"meme_tarif:{game_code}:{1}"
            cccp_meme = f"meme_tarif:{game_code}:{2}"
            cats_meme = f"meme_tarif:{game_code}:{3}"
            neiro_meme = f"meme_tarif:{game_code}:{4}"
            markup = types.InlineKeyboardMarkup(row_width=2)
            demo = types.InlineKeyboardButton(f"{logos[0]}Демка (по 10 из всех сетов)", callback_data=demo_meme)
            base = types.InlineKeyboardButton(f"{logos[1]}База (250 шт.)", callback_data=base_meme)
            cccp = types.InlineKeyboardButton(f"{logos[2]}СССР (250 шт.)", callback_data=cccp_meme)
            cats = types.InlineKeyboardButton(f"{logos[3]}Котики (250 шт.)", callback_data=cats_meme)
            neiro = types.InlineKeyboardButton(f"{logos[4]}НЕЙРО (250 шт.)", callback_data=neiro_meme)
            markup.row(demo)
            markup.add(base, cccp, cats, neiro)
            #bot.send_message(player_id, text=f"Приятель, тебе придётся выбрать набор мемов-картинок:", reply_markup=markup)
            '''for i in nazat_tarifs_memes[game_code]:
                bot.send_message(player_id, str(i))
            bot.send_message(player_id, "---")'''
            bot.edit_message_text(chat_id=player_id, message_id=callback_query.message.message_id, text="Приятель, тебе придётся выбрать набор мемов-картинок:",
                                  reply_markup=markup)
            #bot.edit_message_text(chat_id=player_id, message_id=message_id, text=f"Приятель, тебе придётся выбрать набор мемов-картинок:", reply_markup=markup)


#из документации
def calculate_signature(*args) -> str:
    """Create signature MD5.
    """
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


# Формирование URL переадресации пользователя на оплату.

def generate_payment_link(
    merchant_login: str,  # Merchant login
    merchant_password_1: str,  # Merchant password
    cost: decimal,  # Cost of goods, RU
    InvId: int,  # Invoice number
    description: str,  # Description of the purchase
    is_test = 1,
    robokassa_payment_url = 'https://auth.robokassa.ru/Merchant/Index.aspx',
) -> str:
    """URL for redirection of the customer to the service.
    """
    signature = calculate_signature(
        merchant_login,
        cost,
        InvId,
        merchant_password_1
    )

    data = {
        'MerchantLogin': merchant_login,
        'OutSum': cost,
        'InvId': InvId,
        'Description': description,
        'SignatureValue': signature,
        'IsTest': is_test
    }
    return f'{robokassa_payment_url}?{parse.urlencode(data)}'



all_names_of_tarifs = ['Демка', 'МЕМЫ: Весело и в точку!', 'МЕМЫ 2: СССР и 90-е', 'МЕМЫ 3: Котики и пр. нелюди', 'МЕМЫ НЕЙРО']


#робокасса (менюшки с выбором лотов)

def robocassa(user_id, button, game_code):
    global ids_3_otmena
    #длина юзернейма, юзернейм, длина числа кнопки, кнопка, которую нажали(номер тарифа)
    len_user = len(str(user_id))
    if button >= 10:
        len_button = 2
    else:
        len_button = 1
    for_all = str(len_user) + str(user_id) + str(len_button) + str(button)
    #при выборе всех набор, номер будет 100
    full_len_button = 3
    full_for_all = str(len_user) + str(user_id) + str(full_len_button) + str(100)

    #удаляем кнопку готово
    if robocassa_first_time[game_code]:
        gotovo_id = ids_3_gotovo[game_code][2]
        ids_3_gotovo[game_code].pop()
        bot.delete_message(user_id, gotovo_id)

    # генерация ссылки на 1 день (пока тестовая)
    payment_link_day = generate_payment_link(
        merchant_login="memesparty",
        merchant_password_1="economicustest1",
        cost=decimal.Decimal("0"),
        InvId=int(for_all + str(1)),  # номер счёта составить хитро
        description="Техническая документация по ROBOKASSA"
    )

    # генерация ссылки на 1 месяц (пока тестовая)
    payment_link_month = generate_payment_link(
        merchant_login="memesparty",
        merchant_password_1="economicustest1",
        cost=decimal.Decimal("0"),
        InvId=int(for_all + str(30)),  # номер счёта составить хитро
        description="Техническая документация по ROBOKASSA"
    )

    # генерация ссылки на 1 год (пока тестовая)
    payment_link_year = generate_payment_link(
        merchant_login="memesparty",
        merchant_password_1="economicustest1",
        cost=decimal.Decimal("0"),
        InvId=int(for_all + str(365)),  # номер счёта составить хитро
        description="Техническая документация по ROBOKASSA"
    )

    # full генерация ссылки на 1 день (пока тестовая)
    full_payment_link_day = generate_payment_link(
        merchant_login="memesparty",
        merchant_password_1="economicustest1",
        cost=decimal.Decimal("0"),
        InvId=int(full_for_all + str(1)),  # номер счёта составить хитро
        description="Техническая документация по ROBOKASSA"
    )

    # full_ генерация ссылки на 1 месяц (пока тестовая)
    full_payment_link_month = generate_payment_link(
        merchant_login="memesparty",
        merchant_password_1="economicustest1",
        cost=decimal.Decimal("0"),
        InvId=int(full_for_all + str(30)),  # номер счёта составить хитро
        description="Техническая документация по ROBOKASSA"
    )

    # full_ генерация ссылки на 1 год (пока тестовая)
    full_payment_link_year = generate_payment_link(
        merchant_login="memesparty",
        merchant_password_1="economicustest1",
        cost=decimal.Decimal("0"),
        InvId=int(full_for_all + str(365)),  # номер счёта составить хитро
        description="Техническая документация по ROBOKASSA"
    )

    keyboard_1 = telebot.types.InlineKeyboardMarkup()
    pay_button_day = types.InlineKeyboardButton(text=f"день: 100 ₽.", url=payment_link_day)
    pay_button_month = telebot.types.InlineKeyboardButton(text=f"мес: 300 ₽.",
                                                    url=payment_link_month)
    pay_button_year = telebot.types.InlineKeyboardButton(text=f"год: 900 ₽.",
                                                    url=payment_link_year)
    keyboard_1.add(pay_button_day, pay_button_month, pay_button_year)
    if button == 1:
        emoji = "🎯"
    elif button == 2:
        emoji = "🕺"
    elif button == 3:
        emoji = "😻"
    else:
        emoji = "⚡️"
    if not robocassa_first_time[game_code]:
        try:
            message_1 = bot.edit_message_text(chat_id=user_id, message_id=ids_3_otmena[game_code][0],
                                         text=f"Купить <b>доступ к сету «{all_names_of_tarifs[button]}{emoji}»</b> (250 мемов + 100 ситуаций) на период:",
                                         reply_markup=keyboard_1, parse_mode="HTML")
            message_1_id = ids_3_otmena[game_code][0]
        except:
            message_1_id = ids_3_otmena[game_code][0]
    else:
        message_1 = bot.send_message(user_id, text=f"Купить <b>доступ к сету «{all_names_of_tarifs[button]}{emoji}»</b> (250 мемов + 100 ситуаций) на период:", reply_markup=keyboard_1, parse_mode="HTML")
        message_1_id = message_1.message_id


    keyboard_2 = telebot.types.InlineKeyboardMarkup()
    pay_button_day = telebot.types.InlineKeyboardButton(text=f"день: 600 ₽.",
                                                        url=full_payment_link_day)
    pay_button_month = telebot.types.InlineKeyboardButton(text=f"мес: 1800 ₽.",
                                                          url=full_payment_link_month)
    pay_button_year = telebot.types.InlineKeyboardButton(text=f"год: 5400 ₽.",
                                                         url=full_payment_link_year)
    keyboard_2.add(pay_button_day, pay_button_month, pay_button_year)
    if not robocassa_first_time[game_code]:
        message_2_id = ids_3_otmena[game_code][1]
    else:
        message_2 = bot.send_message(user_id,
                     text="Купить <b>полный доступ</b> ко всем существующим и будущим сетам на период:",
                     reply_markup=keyboard_2, parse_mode="HTML")
        message_2_id = message_2.message_id

    #call_data = f"otmena_pokupki:{game_code}"
    call_data = f"pay_mem:{game_code}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    mozno_obnovlat[game_code] = True
    chestno = types.InlineKeyboardButton(text="Вернуться к выбору карт для игры", callback_data=call_data)
    markup.row(chestno)

    if not robocassa_first_time[game_code]:
        message_3_id = ids_3_otmena[game_code][2]
    else:
        robocassa_first_time[game_code] = False
        message_3 = bot.send_message(chat_id=user_id, text="Чтобы продолжить нажми на кнопку", reply_markup=markup)
        message_3_id = message_3.message_id


    ids_3_otmena[game_code] = [message_1_id, message_2_id, message_3_id]




@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('pay_mem:'))
def payment(callback_query):
    global now_obnov
    global mozno_li_nazat_gotovo
    data = callback_query.data.split(':')
    game_code = data[1]
    player_id = callback_query.from_user.id
    if mozno_obnovlat[game_code]:
        mozno_obnovlat[game_code] = False
        # удаляем все прошлые сообщения
        for mes_id in ids_3_gotovo[game_code]:
            bot.delete_message(player_id, mes_id)
        for mes_id in ids_3_otmena[game_code]:
            bot.delete_message(player_id, mes_id)
        ids_3_otmena[game_code] = []
        ids_3_gotovo[game_code] = []

        # высылаем новые сообщения с кнопками и готово
        message_id_1, message_id_2 = chose_deck_of_cards(player_id, game_code)
        ids_3_gotovo[game_code].append(message_id_1)
        ids_3_gotovo[game_code].append(message_id_2)

        markup = types.InlineKeyboardMarkup(row_width=1)
        callback_data_podtverdit = f"podtverdit:{game_code}"
        mozno_li_nazat_gotovo[game_code] = True
        podtverdit_choice = types.InlineKeyboardButton("Готово!", callback_data=callback_data_podtverdit)
        now_obnov[game_code] = False
        robocassa_first_time[game_code] = True
        markup.add(podtverdit_choice)
        message = bot.send_message(player_id, "Когда выберешь колоды, жми", reply_markup=markup)
        message_id = message.message_id

        ids_3_gotovo[game_code].append(message_id)  # добавили 3 элементом id сообщения "готово"




@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('otmena_pokupki:'))
def payment(callback_query):
    global mozno_li_nazat_gotovo
    global now_obnov
    data = callback_query.data.split(':')
    game_code = data[1]
    player_id = callback_query.from_user.id

    # удаляем 3 сообщения
    for id_mess in ids_3_otmena[game_code]:
        bot.delete_message(player_id, id_mess)
    ids_3_otmena[game_code] = []

    # высылаем кнопку готово и добавляем её в массив
    markup = types.InlineKeyboardMarkup(row_width=1)
    callback_data_podtverdit = f"podtverdit:{game_code}"
    mozno_li_nazat_gotovo[game_code] = True
    podtverdit_choice = types.InlineKeyboardButton("Готово!", callback_data=callback_data_podtverdit)
    now_obnov[game_code] = False
    robocassa_first_time[game_code] = True
    markup.add(podtverdit_choice)
    message = bot.send_message(player_id, "Когда выберешь колоды, жми", reply_markup=markup)
    message_id = message.message_id
    ids_3_gotovo[game_code].append(message_id)  # добавили 3 элементом id сообщения "готово"


@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Successful payment')


#ситуации
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('sit_tarif:'))
def chose_tarif_sit(callback_query):
    with message_list_lock:
        global all_available_tarifs_sit
        global nazat_tarifs_sit
        data = callback_query.data.split(':')
        player_id = callback_query.from_user.id
        game_code = data[1]
        button = int(data[2])



        if button not in all_available_tarifs_sit[game_code]:
            #bot.send_message(player_id, "Этот тариф пока недоступен. Хорошая новость: его можно купить!")
            #робокасса
            robocassa(player_id, button, game_code)
        else:
            if button not in nazat_tarifs_sit[game_code]: #кнопка ненажата -> нажата = зеленый
                nazat_tarifs_sit[game_code].append(button)
            else: #кнопка была нажата, теперь нет -> белый
                nazat_tarifs_sit[game_code].remove(button)
            logos = []
            for number in range(5): #проходимся по всем кнопкам
                if number in nazat_tarifs_sit[game_code]: #должна быть зелёной
                    logos.append("🟢️ ")
                elif number in all_available_tarifs_sit[game_code]: #доступна, но не нажата (белый)
                    logos.append("⚪️ ")
                else: #замок
                    logos.append("💰")

            # выбор мемов
            demo_sit = f"sit_tarif:{game_code}:{0}"
            base_sit = f"sit_tarif:{game_code}:{1}"
            cccp_sit = f"sit_tarif:{game_code}:{2}"
            cats_sit = f"sit_tarif:{game_code}:{3}"
            neiro_sit = f"sit_tarif:{game_code}:{4}"
            markup = types.InlineKeyboardMarkup(row_width=2)
            demo = types.InlineKeyboardButton(f"{logos[0]}Демка (по 10 из всех сетов)", callback_data=demo_sit)
            base = types.InlineKeyboardButton(f"{logos[1]}База (100 шт.)", callback_data=base_sit)
            cccp = types.InlineKeyboardButton(f"{logos[2]}СССР (100 шт.)", callback_data=cccp_sit)
            cats = types.InlineKeyboardButton(f"{logos[3]}Котики (100 шт.)", callback_data=cats_sit)
            neiro = types.InlineKeyboardButton(f"{logos[4]}НЕЙРО (100 шт.)", callback_data=neiro_sit)
            markup.row(demo)
            markup.add(base, cccp, cats, neiro)
            bot.edit_message_text(chat_id=player_id, message_id=callback_query.message.message_id, text=f"И ещё потрудись выбрать карты ситуаций:",
                                  reply_markup=markup)



#выбор колоды мемов и ситуаций
def chose_deck_of_cards(player_id, game_code):
    global all_available_tarifs_memes
    global nazat_tarifs_memes

    global all_available_tarifs_sit
    global nazat_tarifs_sit
    # 0-id, 1-name, 2-tarif, 3-data

    #add(player_id, "sakuharo", "+", "10.08.2024 15:30:00")
    #add(player_id, "sakuharo", "Котики", "10.08.2021 15:30:00")
    # смотрим на подписки игрока
    user_subscriptions = get_user_subscriptions(player_id)
    '''for i in user_subscriptions:
        bot.send_message(player_id, str(i))'''
    nazat_tarifs_memes[game_code] = [0]
    nazat_tarifs_sit[game_code] = [0]

    #все доступные тарифы 0,1,2,3,4
    all_available_tarifs_memes[game_code] = [0]
    all_available_tarifs_sit[game_code] = [0]

    # выбор мемов
    demo_meme = f"meme_tarif:{game_code}:{0}"
    base_meme = f"meme_tarif:{game_code}:{1}"
    cccp_meme = f"meme_tarif:{game_code}:{2}"
    cats_meme = f"meme_tarif:{game_code}:{3}"
    neiro_meme = f"meme_tarif:{game_code}:{4}"
    markup = types.InlineKeyboardMarkup(row_width=2)
    demo = types.InlineKeyboardButton("🟢️ Демка (по 10 из всех сетов)", callback_data=demo_meme)
    # если подписок вообще нет
    if not user_subscriptions:
        base = types.InlineKeyboardButton("💰База (250 шт.)", callback_data=base_meme)
        cccp = types.InlineKeyboardButton("💰СССР (250 шт.)", callback_data=cccp_meme)
        cats = types.InlineKeyboardButton("💰Котики (250 шт.)", callback_data=cats_meme)
        neiro = types.InlineKeyboardButton("💰НЕЙРО (250 шт.)", callback_data=neiro_meme)
    # если есть подписка на что-то
    else:
        # Получить текущую дату и время
        current_datetime = datetime.datetime.now()

        tarifs_and_data = {} #тарифы - ключи, даты-values
        for raw in user_subscriptions:
            #добавляем тариф
            if raw[2] not in tarifs_and_data:
                tarifs_and_data[raw[2]] = [raw[3]]
            #если несколь дат, то добавляем и сортируем
            else:
                tarifs_and_data[raw[2]].append(raw[3])
                tarifs_and_data[raw[2]].sort()
        if "База" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["База"][-1], "%d.%m.%Y %H:%M:%S") > current_datetime:
            base = types.InlineKeyboardButton("⚪️ База (250 шт.)", callback_data=base_meme)
            all_available_tarifs_memes[game_code].append(1)
        else:
            base = types.InlineKeyboardButton("💰База (250 шт.)", callback_data=base_meme)
        if "СССР" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["СССР"][-1], "%d.%m.%Y %H:%M:%S") > current_datetime:
            cccp = types.InlineKeyboardButton("⚪️ СССР (250 шт.)", callback_data=cccp_meme)
            all_available_tarifs_memes[game_code].append(2)
        else:
            cccp = types.InlineKeyboardButton("💰СССР (250 шт.)", callback_data=cccp_meme)
        if "Котики" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["Котики"][-1], "%d.%m.%Y %H:%M:%S") > current_datetime:
            cats = types.InlineKeyboardButton("⚪️ Котики (250 шт.)", callback_data=cats_meme)
            all_available_tarifs_memes[game_code].append(3)
        else:
            cats = types.InlineKeyboardButton("💰Котики (250 шт.)", callback_data=cats_meme)
        if "НЕЙРО" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["НЕЙРО"][-1], "%d.%m.%Y %H:%M:%S") > current_datetime:
            neiro = types.InlineKeyboardButton("⚪ НЕЙРО (250 шт.)", callback_data=neiro_meme)
            all_available_tarifs_memes[game_code].append(4)
        else:
            neiro = types.InlineKeyboardButton("💰НЕЙРО (250 шт.)", callback_data=neiro_meme)
    markup.row(demo)
    markup.add(base, cccp, cats, neiro)
    message = bot.send_message(player_id, f"Приятель, тебе придётся выбрать набор мемов-картинок:", reply_markup=markup)



    # выбор ситуаций
    demo_sit = f"sit_tarif:{game_code}:{0}"
    base_sit = f"sit_tarif:{game_code}:{1}"
    cccp_sit = f"sit_tarif:{game_code}:{2}"
    cats_sit = f"sit_tarif:{game_code}:{3}"
    neiro_sit = f"sit_tarif:{game_code}:{4}"
    markup = types.InlineKeyboardMarkup(row_width=2)
    demo = types.InlineKeyboardButton("🟢️ Демка (по 10 из всех сетов)", callback_data=demo_sit)
    # если подписок вообще нет
    if not user_subscriptions:
        base = types.InlineKeyboardButton("💰База (100 шт.)", callback_data=base_sit)
        cccp = types.InlineKeyboardButton("💰СССР (100 шт.)", callback_data=cccp_sit)
        cats = types.InlineKeyboardButton("💰Котики (100 шт.)", callback_data=cats_sit)
        neiro = types.InlineKeyboardButton("💰НЕЙРО (100 шт.)", callback_data=neiro_sit)
    # если есть подписка на что-то
    else:
        # Получить текущую дату и время
        current_datetime = datetime.datetime.now()

        tarifs_and_data = {}  # тарифы - ключи, даты-values
        for raw in user_subscriptions:
            # добавляем тариф
            if raw[2] not in tarifs_and_data:
                tarifs_and_data[raw[2]] = [raw[3]]
            # если несколь дат, то добавляем и сортируем
            else:
                tarifs_and_data[raw[2]].append(raw[3])
                tarifs_and_data[raw[2]].sort()
        if "База" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["База"][-1],
                                                                    "%d.%m.%Y %H:%M:%S") > current_datetime:
            base = types.InlineKeyboardButton("⚪️ База (100 шт.)", callback_data=base_sit)
            all_available_tarifs_sit[game_code].append(1)
        else:
            base = types.InlineKeyboardButton("💰База (100 шт.)", callback_data=base_sit)
        if "СССР" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["СССР"][-1],
                                                                    "%d.%m.%Y %H:%M:%S") > current_datetime:
            cccp = types.InlineKeyboardButton("⚪️ СССР (100 шт.)", callback_data=cccp_sit)
            all_available_tarifs_sit[game_code].append(2)
        else:
            cccp = types.InlineKeyboardButton("💰СССР (100 шт.)", callback_data=cccp_sit)
        if "Котики" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["Котики"][-1],
                                                                      "%d.%m.%Y %H:%M:%S") > current_datetime:
            cats = types.InlineKeyboardButton("⚪️ Котики (100 шт.)", callback_data=cats_sit)
            all_available_tarifs_sit[game_code].append(3)
        else:
            cats = types.InlineKeyboardButton("💰Котики (100 шт.)", callback_data=cats_sit)
        if "НЕЙРО" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["НЕЙРО"][-1],
                                                                     "%d.%m.%Y %H:%M:%S") > current_datetime:
            neiro = types.InlineKeyboardButton("⚪ НЕЙРО (100 шт.)", callback_data=neiro_sit)
            all_available_tarifs_sit[game_code].append(4)
        else:
            neiro = types.InlineKeyboardButton("💰НЕЙРО (100 шт.)", callback_data=neiro_sit)
    markup.row(demo)
    markup.add(base, cccp, cats, neiro)
    message2 = bot.send_message(player_id, f"И ещё потрудись выбрать карты ситуаций:", reply_markup=markup)
    return (message.message_id, message2.message_id)




# новая игра
@bot.callback_query_handler(func=lambda message: message.data == 'new_game')
def new_game(message):
    player_id = message.message.chat.id
    #user_id = message.from_user.id
    pl_name = message.from_user.first_name
    game_code = generate_game_code()
    ids_3_gotovo[game_code] = []

    message_id = message.message.message_id
    bot.delete_message(player_id, message_id)


    # Сохраняем информацию об игре
    active_games[game_code] = {'creator': player_id, 'players': [player_id], 'usernames': [pl_name]}
    flag_vse_progolos[game_code] = False
    id_and_names[game_code] = {}
    id_and_names[game_code][player_id] = pl_name

    # выбор колоды мемов и ситуаций
    message_id_1,  message_id_2 = chose_deck_of_cards(player_id, game_code)
    ids_3_gotovo[game_code].append(message_id_1)
    ids_3_gotovo[game_code].append(message_id_2)

    markup = types.InlineKeyboardMarkup(row_width=1)
    callback_data_podtverdit = f"podtverdit:{game_code}"
    mozno_li_nazat_gotovo[game_code] = True
    podtverdit_choice = types.InlineKeyboardButton("Готово!", callback_data=callback_data_podtverdit)
    now_obnov[game_code] = False
    robocassa_first_time[game_code] = True
    markup.add(podtverdit_choice)
    message = bot.send_message(player_id, "Когда выберешь колоды, жми", reply_markup=markup)
    message_id = message.message_id
    ids_3_gotovo[game_code].append(message_id)  # добавили 3 элементом id сообщения "готово"


@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('podtverdit:'))
def podtverdit_choices(callback_query):
    data = callback_query.data.split(':')
    player_id = callback_query.from_user.id
    game_code = data[1]
    if mozno_li_nazat_gotovo[game_code]:
        mozno_li_nazat_gotovo[game_code] = False
        message_id_1 = ids_3_gotovo[game_code][0]
        message_id_2 = ids_3_gotovo[game_code][1]


        # удаляем прошлое сообщение
        message_id = callback_query.message.message_id
        bot.delete_message(player_id, message_id_1)
        bot.delete_message(player_id, message_id_2)
        bot.delete_message(player_id, message_id)

        # генерим все ссылки на все мемы. появляется deck_of_meme_cards, trash_memes
        generate_meme_links(game_code)
        generate_sit_links(game_code)

        # Отправляем ссылку создателю игры
        message_1 = bot.send_message(player_id, f"Вы создали новую игру! Поделитесь кодом со своими друзьями: {game_code}")
        message_id_1 = message_1.message_id

        creator_id = active_games[game_code]['creator']
        create_players_message(game_code, creator_id)
        message_id_2 = message_list_of_players[game_code][creator_id]


        markup = types.InlineKeyboardMarkup(row_width=2)
        callback_data_start = f"start:{game_code}:{message_id_1}"
        start_game_button = types.InlineKeyboardButton("Начать игру", callback_data=callback_data_start)
        callback_data_drop = f"drop:{game_code}:{message_id_1}:{message_id_2}"
        mozno_nazad_v_menu[game_code] = True
        drop_button = types.InlineKeyboardButton("Назад в меню", callback_data=callback_data_drop)
        markup.add(start_game_button, drop_button)
        bot.send_message(player_id, f'Когда все присоединятся, нажмите "Начать игру"', reply_markup=markup)

        optimization_hand_cards(game_code, player_id)


@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('drop:'))
def drop(callback_query):
    data = callback_query.data.split(':')
    player_id = callback_query.from_user.id
    game_code = data[1]
    message_id_1 = data[2]
    message_id_2 = data[3]
    if mozno_nazad_v_menu[game_code]:
        mozno_nazad_v_menu[game_code] = False
        #удаляем прошлое сообщение
        message_id = callback_query.message.message_id
        try:
            bot.delete_message(player_id, int(message_id_1))
        except:
            pass
        try:
            bot.delete_message(player_id, message_id)
        except:
            pass
        try:
            bot.delete_message(player_id, message_id_2)
        except:
            pass

        if game_code in active_games and player_id == active_games[game_code]['creator']:
            delete_stuff(game_code)
            del id_and_names[game_code]

            del all_available_tarifs_memes[game_code]
            del nazat_tarifs_memes[game_code]
            del all_available_tarifs_sit[game_code]
            del nazat_tarifs_sit[game_code]
            del deck_of_sit_cards[game_code]
            del trash_sit[game_code]
            del deck_of_meme_cards[game_code]
            del trash_memes[game_code]

        markup = types.InlineKeyboardMarkup(row_width=1)
        new_game_button = types.InlineKeyboardButton("Новая игра", callback_data="new_game")
        join_game_button = types.InlineKeyboardButton("Присоединиться к игре", callback_data="join_game")
        rules_button = types.InlineKeyboardButton("Правила игры", callback_data="rules")
        markup.add(new_game_button, join_game_button, rules_button)
        bot.send_message(player_id, text="А ну-ка, выбирай", reply_markup=markup)




@bot.callback_query_handler(func=lambda message: message.data == 'join_game')
def join_game(message):
    player_id = message.message.chat.id
    message_id = message.message.message_id
    bot.delete_message(player_id, message_id)

    game_code = -1
    callback_data_leave = f"menu:{game_code}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    back_button = types.InlineKeyboardButton("Назад в меню", callback_data=callback_data_leave)
    markup.add(back_button)
    bot.send_message(player_id, f"Введите код игры", reply_markup=markup)


# чтение текста (код игры)
@bot.message_handler(content_types=['text'])
def handle_game_code(message):
    # если это код
    if len(message.text) == 6 and message.text.isdigit():
        game_code = message.text
        chat_id = message.chat.id
        if game_code in active_games:
            pl_name = message.from_user.first_name
            join_existing_game(chat_id, pl_name, game_code)
        else:
            bot.send_message(chat_id, f"Игра с кодом {game_code} не найдена.")


def join_existing_game(player_id, pl_name, game_code):
    players = active_games[game_code]['players']
    game_started = active_games[game_code].get('game_started', False)  # Проверка флага game_started

    if game_started:
        bot.send_message(player_id, f"Игра уже началась. Новые игроки не могут присоединиться.")
    elif player_id in players:
        bot.send_message(player_id, f"Вы уже присоединены к этой игре.")
    else:
        bot.send_message(player_id, f"Вы присоединились к игре.")
        active_games[game_code]['players'].append(player_id)
        active_games[game_code]['usernames'].append(pl_name)
        id_and_names[game_code][player_id] = pl_name
        if 'creator' not in active_games[game_code]:
            creator_name = id_and_names[game_code][remember_players[game_code]['creator']]
            create_players_message(game_code, player_id)
            bot.send_message(player_id, text=f"Ждём, когда все зайдут и {creator_name} запустит игру")
        else:
            creator_name = id_and_names[game_code][active_games[game_code]['creator']]
            update_players_message(game_code, player_id, creator_name)
        optimization_hand_cards(game_code, player_id)


# начало игры
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('start:'))
def start_game(callback_query):
    data = callback_query.data.split(':')
    player_id = callback_query.from_user.id
    game_code = data[1]
    message_id_1 = data[2]
    if game_code in nazat_tarifs_memes and len(nazat_tarifs_memes[game_code]) == 0:
        bot.send_message(player_id, "Нужно выбрать хотябы 1 набор, чтобы начать игру.")
    else:
    #message_id_2 = data[3]


        #основное тело
        chat_id = callback_query.message.chat.id
        game_code = None
        for code, game in active_games.items():
            if game['creator'] == callback_query.from_user.id:
                game_code = code
                break
        if game_code in remember_players:
            del remember_players[game_code]
        if game_code:
            players = active_games[game_code]['players']
            if len(players) >= 1:  # Проверка количества игроков

                # удаляем прошлое сообщение
                message_id = callback_query.message.message_id
                bot.delete_message(player_id, int(message_id_1))
                bot.delete_message(player_id, message_id)
                active_games[game_code]['game_started'] = True

                send_message_to_players(game_code, "Игра началась!")
                rating[game_code] = {}
                for player in players: #добавляем всех в рейтинг
                    rating[game_code][player] = 0
                if len(players) < 4: #если мало игроков, то добавляем бота
                    rating[game_code]["bot"] = 0
                players_hand_cards(game_code)

            else:
                bot.send_message(chat_id, "Нужно хотя бы 2 игрока, чтобы начать игру.")

        else:
            bot.send_message(chat_id, "Вы не являетесь создателем игры, поэтому не можете её начать.")


####### показ ситуаций пользователю

# список ссылок на ситуации
def generate_sit_links(game_code):
    global deck_of_sit_cards
    global trash_sit
    global nazat_tarifs_sit
    nabor = nazat_tarifs_sit[game_code]
    '''for i in nabor:
        send_message_to_players(game_code, str(i))'''

    links = []
    url_1 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/s1/"
    url_2 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/s2/"
    url_3 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/s3/"
    url_4 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/s4/"
    est_demka = False
    if 0 in nabor:
        est_demka = True
        for i in range(1, 11):
            link1 = f"{url_1}N{str(i).zfill(5)}.jpg"
            link2 = f"{url_2}N{str(i).zfill(5)}.jpg"
            link3 = f"{url_3}N{str(i).zfill(5)}.jpg"
            link4 = f"{url_4}N{str(i).zfill(5)}.jpg"
            links.append(link1)
            links.append(link2)
            links.append(link3)
            links.append(link4)
    if 1 in nabor:
        if est_demka:
            for i in range(11, 101):
                link1 = f"{url_1}N{str(i).zfill(5)}.jpg"
                links.append(link1)
        else:
            for i in range(1, 101):
                link1 = f"{url_1}N{str(i).zfill(5)}.jpg"
                links.append(link1)
    if 2 in nabor:
        if est_demka:
            for i in range(11, 101):
                link2 = f"{url_2}N{str(i).zfill(5)}.jpg"
                links.append(link2)
        else:
            for i in range(1, 101):
                link2 = f"{url_2}N{str(i).zfill(5)}.jpg"
                links.append(link2)
    if 3 in nabor:
        if est_demka:
            for i in range(11, 101):
                link3 = f"{url_3}N{str(i).zfill(5)}.jpg"
                links.append(link3)
        else:
            for i in range(1, 101):
                link3 = f"{url_3}N{str(i).zfill(5)}.jpg"
                links.append(link3)
    if 4 in nabor:
        if est_demka:
            for i in range(11, 101):
                link4 = f"{url_4}N{str(i).zfill(5)}.jpg"
                links.append(link4)
        else:
            for i in range(1, 101):
                link4 = f"{url_4}N{str(i).zfill(5)}.jpg"
                links.append(link4)
    deck_of_sit_cards[game_code] = links  # колода карт sit в игре
    trash_sit[game_code] = []  # сброс

#список ссылок на действующие мемы
def generate_meme_links(game_code): #nabor-список наборов [0,1,2,3,4]
    global deck_of_meme_cards
    global trash_memes
    global nazat_tarifs_memes
    nabor = nazat_tarifs_memes[game_code]

    links = []
    url_1 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/m1/"
    url_2 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/m2/"
    url_3 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/m3/"
    url_4 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/m4/"
    est_demka = False
    if 0 in nabor:
        est_demka = True
        for i in range(1, 11):
            link1 = f"{url_1}N{str(i).zfill(5)}.jpg"
            link2 = f"{url_2}N{str(i).zfill(5)}.jpg"
            link3 = f"{url_3}N{str(i).zfill(5)}.jpg"
            link4 = f"{url_4}N{str(i).zfill(5)}.jpg"
            links.append(link1)
            links.append(link2)
            links.append(link3)
            links.append(link4)
    if 1 in nabor:
        if est_demka:
            for i in range(11, 251):
                link1 = f"{url_1}N{str(i).zfill(5)}.jpg"
                links.append(link1)
        else:
            for i in range(1, 251):
                link1 = f"{url_1}N{str(i).zfill(5)}.jpg"
                links.append(link1)
    if 2 in nabor:
        if est_demka:
            for i in range(11, 251):
                link2 = f"{url_2}N{str(i).zfill(5)}.jpg"
                links.append(link2)
        else:
            for i in range(1, 251):
                link2 = f"{url_2}N{str(i).zfill(5)}.jpg"
                links.append(link2)
    if 3 in nabor:
        if est_demka:
            for i in range(11, 251):
                link3 = f"{url_3}N{str(i).zfill(5)}.jpg"
                links.append(link3)
        else:
            for i in range(1, 251):
                link3 = f"{url_3}N{str(i).zfill(5)}.jpg"
                links.append(link3)
    if 4 in nabor:
        if est_demka:
            for i in range(11, 251):
                link4 = f"{url_4}N{str(i).zfill(5)}.jpg"
                links.append(link4)
        else:
            for i in range(1, 251):
                link4 = f"{url_4}N{str(i).zfill(5)}.jpg"
                links.append(link4)
    deck_of_meme_cards[game_code] = links  # колода карт мемов в игре
    trash_memes[game_code] = [] #сброс

#выбор ситуации
def random_choice_of_photo(game_code):
    global deck_of_sit_cards
    global trash_sit

    if len(deck_of_sit_cards[game_code]) == 0:
        send_message_to_players(game_code, "Ситуации закончились. Теперь вы будете видеть ситуации из колоды сброса. (Можно докупить наборы карт, чтобы играть было ещё веселей!")
        deck_of_sit_cards[game_code] = trash_sit
        trash_sit[game_code] = []

    random_photo_link = random.choice(deck_of_sit_cards[game_code])
    deck_of_sit_cards[game_code].remove(random_photo_link)
    trash_sit[game_code].append(random_photo_link)
    return random_photo_link

# отправить фото в игру
def send_photo_to_players(game_code, photo_url):
    players = active_games[game_code]['players']
    for player_id in players:
        bot.send_photo(player_id, photo_url)


def download_situation(link):
    image = Image.open(requests.get(link, stream=True).raw)

    sit_photo_io = io.BytesIO()  # скачиваем фотки большие
    image.save(sit_photo_io, format='JPEG')
    sit_photo_io.seek(0)

    return sit_photo_io


#отправка ситуаций
def send_situation(game_code):
    link = random_choice_of_photo(game_code)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        cards_on_table[game_code] = {}
        cards_on_table[game_code]['photos_on_table'] = []

        future = executor.submit(download_situation, link)
        situation_card = future.result()  # Get the result from the future object
        cards_on_table[game_code]['photos_on_table'].append(situation_card.getvalue())
        #chosen_photo = BytesIO(cards_on_table[game_code]['photos_on_table'][0]) - incorrect

    # запонимаени id situation чтобы удалить потом

    #send_photo_to_players
    players = active_games[game_code]['players']
    for player_id in players:
        sit = bot.send_photo(player_id, cards_on_table[game_code]['photos_on_table'][0])



### разыгровка руки


#обновления ссылок

def random_choice_of_link_meme(game_code):
    global deck_of_meme_cards
    global trash_memes
    #ссылки на все доступные мемы
    game_meme_choice = deck_of_meme_cards[game_code]
    if len(game_meme_choice) == 0:
        send_message_to_players(game_code, "Мемы закончились. Поэтому вы продолжите играть с мемами из колоды сброса. (Дополнительные картинки-мемы можно купить, чтобы игра была ещё интересней!)")
        deck_of_meme_cards[game_code] = trash_memes[game_code]
        trash_memes[game_code] = []
    else:
        random_meme_link = random.choice(game_meme_choice)
        deck_of_meme_cards[game_code].remove(random_meme_link)
        trash_memes[game_code].append(random_meme_link)
        return random_meme_link

# сделать ссылку на фото
'''def create_link_big_meme(number):
    base_url = f"https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/m4/"
    link = f"{base_url}N{str(number).zfill(5)}.jpg"
    return link'''
# chosen_photos[game_code]
'''def random_choice_of_number(game_code):
    game_meme_choice = chosen_memes[game_code]

    if len(game_meme_choice) == 0:
        send_message_to_players(game_code, "Мемы закончились")
        return None
    else:
        random_photo_number = random.choice(game_meme_choice)
        chosen_memes[game_code].remove(random_photo_number)
        #del chosen_memes[game_code][random_photo_number]
        return random_photo_number'''

#плашка 1/4
plashka_url_4 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/cursor275.jpg"
plashka_response_4 = requests.get(plashka_url_4)
#if plashka_response_4.status_code == 200:
plashka_4 = Image.open(BytesIO(plashka_response_4.content))

#плагшка 1/5
plashka_url_5 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/cursor128.jpg"
plashka_response_5 = requests.get(plashka_url_5)
plashka_5 = Image.open(BytesIO(plashka_response_5.content))

#корона
crown_url = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/crown.png"
crown_response = requests.get(crown_url)
crown = Image.open(BytesIO(crown_response.content))

#звезда
star_url = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/star.png"
star_response = requests.get(star_url)
star = Image.open(BytesIO(star_response.content))


#вставляем плашку
#position = (100, 200)
def insert_image_to_main(image, position, ad_param):
    main_image = Image.open(image)
    if ad_param == 5: #hand
        main_image.paste(plashka_5, position)
    elif ad_param == 4: #4 голосовалка
        main_image.paste(plashka_4, position)
    elif ad_param == "star":
        if main_image.mode != 'RGBA':
            main_image = main_image.convert('RGBA')
        main_image.paste(star, position, mask=star)
    else: #crown
        if main_image.mode != 'RGBA':
            main_image = main_image.convert('RGBA')

        main_image.paste(crown, position, mask=crown)


    new_image = BytesIO()
    main_image.save(new_image, format='PNG')
    new_image.seek(0)

    return new_image

def download_image(url):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    return image




# составляем колаж руки
def combine_small_pic(user_id, small_photos_links):
    # Загрузка маленьких изображений параллельно
    small_images_bylinks = OrderedDict()  # OrderedDict для сохранения порядка загруженных изображений

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(download_image, link): link for link in small_photos_links}
        for future in concurrent.futures.as_completed(futures):
            link = futures[future]
            result = future.result()
            small_images_bylinks[link] = result

    small_images = []
    for link in small_photos_links:
        small_images.append(small_images_bylinks[link])

    photos_per_row = 5
    lil_space_width = 640 // 5
    collage_height = 461 // 5 + 8
    collage_width = 640
    collage = Image.new('RGB', (collage_width, collage_height), (255, 255, 255))

    # Вставка каждой уменьшенной фотографии на холст
    for i, image in enumerate(small_images):
        if image.height > image.width: #вертикальная
            height = 461 // 5
            izmenil = 640 // height
            width = 461 // izmenil
            image.thumbnail((width, height))
            #image.thumbnail((image.height // 5, image.width // 5))
            x_offset = ((i % 5) * lil_space_width) + (lil_space_width - image.width) // 2
        else:  # горизонтальная
            image.thumbnail((640 // 5, 461 // 5))
            x_offset = (i % 5) * lil_space_width
        y_offset = 0
        # Вставка уменьшенной фотографии на холст
        collage.paste(image, (x_offset, y_offset))

    # Создаем объект BytesIO и сохраняем в него результирующее изображение
    image_buffer = BytesIO()
    collage.save(image_buffer, format='PNG')
    image_buffer.seek(0)

    # Возвращение объединенного изображения в виде объекта BytesIO
    return image_buffer





def top_plus_bottom(main_photo, bottom):
    # Ссылка на большое фото
    #main_photo_link = create_link_big_meme(main_photo_number)

    # Загрузка и объединение изображений
    #main_image = Image.open(BytesIO(requests.get(main_photo_link).content))
    main_image = Image.open(main_photo)
    bottom_image = Image.open(bottom)

    # Проверка размеров изображений и изменение размеров, если необходимо


    if main_image.height > main_image.width:
        new_width = round(main_image.width * (548 / main_image.height))
        main_image = main_image.resize((new_width, 548))
        whitespace_width = (bottom_image.width - main_image.width) // 2

        resized_bottom_image = bottom_image
        combined_width = bottom_image.width
        combined_height = main_image.height + bottom_image.height
        combined_image = Image.new('RGB', (combined_width, combined_height), (255, 255, 255))
        combined_image.paste(main_image, (whitespace_width, 0))

        #combined_image = Image.new('RGB', (bottom_image.width, main_image.height + bottom_image.height))
        #combined_image.paste(main_image, (0, 0))
    else:
        if main_image.width != bottom_image.width:
            resized_bottom_image = bottom_image.resize((main_image.width, bottom_image.height*main_image.width//bottom_image.width))
        else:
            resized_bottom_image = bottom_image
        # Создание нового изображения с объединенными фото
        combined_image = Image.new('RGB', (resized_bottom_image.width, main_image.height + resized_bottom_image.height))
        combined_image.paste(main_image, (0, 0))  # Вставка main_image сверху
    combined_image.paste(resized_bottom_image, (0, main_image.height))  # Вставка resized_bottom_image снизу

    # Отправка объединенного изображения
    combined_image_io = BytesIO()
    combined_image.save(combined_image_io, format='PNG')
    combined_image_io.seek(0)

    return combined_image_io


def left_plus_right(game_code, situation, meme):

    image1 = Image.open(situation)
    image2 = Image.open(meme)

    desired_height = 700

    max_width = image2.width
    max_height = image1.height

    if image2.height > image2.width: #вертикаль
        table_width = image1.width + 640

    else:
        # Размеры совместного изображения
        table_width = image1.width + image2.width
    table_height = max_height

    # Создаем белое изображение
    table_image = Image.new('RGB', (table_width, table_height), (255, 255, 255))

    if image2.height > image2.width: #вертикаль
        # Вычисляем координаты для размещения фотографий по центру
        x_offset_image1 = 0
        y_offset_image1 = 0
        x_offset_image2 = image1.width + (table_width - image1.width - image2.width) // 2

        #x_offset_image2 = x_offset_image1 + image1.width
        y_offset_image2 = (table_height - image2.height) // 2
    else:
        # Вычисляем координаты для размещения фотографий по центру
        x_offset_image1 = 0
        y_offset_image1 = 0
        x_offset_image2 = image1.width
        y_offset_image2 = (max_height - image2.height) // 2

    # Размещаем фотографии на белом фоне
    table_image.paste(image1, (x_offset_image1, y_offset_image1))
    table_image.paste(image2, (x_offset_image2, y_offset_image2))

    image_io = BytesIO()
    table_image.save(image_io, format='PNG')
    image_io.seek(0)

    return image_io


def all_cards_on_the_table(game_code, memes): #дается список фоток
    # for mem in memes:
    #     send_message_to_players(game_code, str(type(mem)))
    #     if (type(mem) == int):
    #         send_message_to_players(game_code, mem)

    images = [Image.open(BytesIO(mem)) for mem in memes]
    # количество карт в ряду
    if len(images) <= 8:
        photos_per_row = min(len(images), 4)
    elif len(images) <= 10:
        photos_per_row = 5
    else:
        photos_per_row = 6

    lil_space_width = 640 // photos_per_row
    max_height = 461
    kolvo_rows = math.ceil(len(images) / photos_per_row)
    if kolvo_rows == 1:
        collage_height = kolvo_rows * max_height//photos_per_row + 5
    else:
        collage_height = kolvo_rows * max_height // photos_per_row + 24
    collage_width = 640

    collage = Image.new('RGB', (collage_width, collage_height), (255, 255, 255))

    # Вставка каждой уменьшенной фотографии на холст
    prev_height = 0
    for i, image in enumerate(images):
        if image.height > image.width: #вертикальная
            image.thumbnail((image.height // photos_per_row, image.width // photos_per_row))
            x_offset = ((i % photos_per_row) * lil_space_width) + (lil_space_width - image.width) // 2
        else: # горизонтальная
            image.thumbnail((image.width//photos_per_row, image.height//photos_per_row))
            x_offset = (i % photos_per_row) * lil_space_width

        if i % photos_per_row == 0 and i != 0: #перешли на новую строку
            prev_height += max_height//photos_per_row + 12
        y_offset = prev_height
        # Вставка уменьшенной фотографии на холст
        collage.paste(image, (x_offset, y_offset))

    image_io = io.BytesIO()
    collage.save(image_io, format='PNG')
    image_io.seek(0)
    return image_io


voted_battle_cards = {} #карты, за которые проголосовали
# отправка голосования
def progolosoval(player_id, game_code, photos_per_row, kolvo_empty, message_idd, kolvo_buttons):
    global all_combined_images

    if not flag_vse_progolos[game_code]:
        if game_code in voted_players and player_id in voted_players[game_code]:
            bot.send_message(player_id, "Ты уже голосовал! Немного подожди:)")
        else:
            numb_za_kot_progolos = battle_cards[game_code][player_id]
            voted_battle_cards[game_code][player_id] = numb_za_kot_progolos
            if player_id == cards_on_table[game_code]['photos_on_table'][numb_za_kot_progolos][0]:
                bot.send_message(player_id, "Твой мем прекрасен, но проголосуй за другой 🤪")
            else:
                situation_card = cards_on_table[game_code]['photos_on_table'][0]
                numb_za_kot_progolos = battle_cards[game_code][player_id]
                x = -30
                y = -30
                whole_picture = add_mem_plashka(game_code, numb_za_kot_progolos - 1, (x, y))



                with message_list_lock:
                    znak = 0
                    if game_code not in voted_players:
                        voted_players[game_code] = [player_id]
                        znak = 1
                        #bot.send_message(player_id, "Ваш голос учтён первым. Посмотрим, что скажут другие игроки 🤔"
                        all_combined_images[game_code] = []
                    elif player_id not in voted_players[game_code]:
                        voted_players[game_code].append(player_id)
                        #bot.send_message(player_id, "Ваш голос учтён. Посмотрим, что скажут другие игроки 🤔")
                        znak = 1

                if znak == 1:
                    bot.send_message(player_id, "Ваш голос учтён. Посмотрим, что скажут другие игроки 🤔")
                    with message_list_lock:
                        # добавляем id сообщения
                        if game_code not in messages_ids:
                            messages_ids[game_code] = {}
                        messages_ids[game_code][player_id] = message_idd

                    # плашка
                    whole_picture_ = Image.open(whole_picture)
                    x = whole_picture_.width // 4 * (numb_za_kot_progolos - 1)
                    if kolvo_buttons == 4:
                        y = whole_picture_.height - 16
                    elif numb_za_kot_progolos <= 4:
                        y = 4 * whole_picture_.height // 5 - 28
                    else:
                        y = whole_picture_.height - 28
                        x = whole_picture_.width // 4 * (numb_za_kot_progolos - 4 - 1)

                    new_image = insert_image_to_main(whole_picture, (x, y), 4)

                    # if len(active_games[game_code]['players']) != len(voted_players[game_code]):
                    bot.edit_message_media(
                        chat_id=player_id,
                        message_id=message_idd,
                        media=types.InputMediaPhoto(new_image)
                    )

    with message_list_lock:
        if game_code in voted_players:
            flag_vse_progolos[game_code] = len(active_games[game_code]['players']) == len(voted_players[game_code])
        else:
            flag_vse_progolos[game_code] = False
    if flag_vse_progolos[game_code]:
        del voted_players[game_code]

        send_message_to_players(game_code, "Все игроки проголосовали! А вот и рейтинг мемолюбов:")

        progolosoval_prt_2(game_code, kolvo_buttons, photos_per_row, kolvo_empty)



def progolosoval_prt_2(game_code, kolvo_buttons, photos_per_row, kolvo_empty):
    # всем каpтинам присваиваем 0 голосов
    stop_waiting_golosov[game_code] = True
    for card in cards_on_table[game_code]['photos_on_table'][1:-1]:
        card.append(0)

    for numb_za in voted_battle_cards[game_code].values():  # получаем все номера картин, за которые проголосовали
        cards_on_table[game_code]['photos_on_table'][numb_za][2] += 1  # если не голос

    # кнопки с именами
    buttons = []
    zero = "zero"
    callback_zero = f"choose:{game_code}:{zero}:{photos_per_row}:{kolvo_empty}"

    answer = {}
    max_votes = 0
    num_winner = 0
    i = 0
    for result in cards_on_table[game_code]['photos_on_table'][1:-1]:
        i += 1
        pl_id = result[0]
        votes = result[2]
        if votes > max_votes:
            num_winner = i
            max_votes = votes
        if pl_id in id_and_names[game_code]:
            rating[game_code][pl_id] += votes
            answer[pl_id] = votes
            pl_name = id_and_names[game_code][pl_id]
            # button_text = f"{pl_name} (+{votes})"
            button_text = f"{pl_name}"
        else:
            rating[game_code]["bot"] += votes
            # button_text = f"bot (+{votes})"
            button_text = f"bot"
            if "bot" not in answer:
                answer["bot"] = votes
            else:
                answer["bot"] += votes
        button = types.InlineKeyboardButton(button_text, callback_data=callback_zero)
        buttons.append(button)

    # финальное фото
    x = -30
    y = -30
    whole_picture = add_mem_plashka(game_code, num_winner - 1, (x, y))
    whole_picture_ = Image.open(whole_picture)

    markup = types.InlineKeyboardMarkup(row_width=photos_per_row)
    markup.add(*buttons)

    # солнце на top
    top = whole_picture_
    x = top.width - 150
    y = 40
    new_top = insert_image_to_main(whole_picture, (x, y), "sun")

    # звезды
    x = 232
    x_initial = x
    y = 665
    com_star = new_top

    if kolvo_buttons == 4:
        y = 658
        for num in range(kolvo_buttons):
            kolvo_votes = cards_on_table[game_code]['photos_on_table'][num + 1][2]
            for vote in range(kolvo_votes):
                # for vote in range(3):
                com_star = insert_image_to_main(com_star, (x, y), "star")
                x -= 20
            x = x_initial + 275
            x_initial = x
    else:
        for num in range(kolvo_buttons):
            kolvo_votes = cards_on_table[game_code]['photos_on_table'][num + 1][2]
            if num <= 3:
                y = 658
            elif num == 4:
                x = 232
                x_initial = x
                y = 875
            else:
                y = 875
                # num = num - 4
            for vote in range(kolvo_votes):
                # for vote in range(3):
                com_star = insert_image_to_main(com_star, (x, y), "star")
                x -= 20
            x = x_initial + 275
            x_initial = x

    com = Image.open(com_star)
    new_width = 640
    new_height = int(new_width / whole_picture_.width * whole_picture_.height)
    resized_com_star = com.resize((new_width, new_height))

    # обновление у всех
    players = active_games[game_code]['players']
    for pl_id in players:
        combined_image_io = copy.deepcopy(resized_com_star)
        # with message_list_lock:
        messag_id = golosov_mes_ids[game_code][pl_id]
        #messag_id = int(messages_ids[game_code][pl_id])
        if messag_id is not None:
            # bot.send_photo(pl_id, combined_image_io)
            bot.edit_message_media(
                chat_id=pl_id,
                message_id=messag_id,
                media=types.InputMediaPhoto(combined_image_io),
                reply_markup=markup
            )

    # сортируем по убыванию и выводим общий рейтинг
    rating[game_code] = dict(sorted(rating[game_code].items(), key=lambda x: x[1], reverse=True))
    cur_rating = ""

    i = 1
    for pl_id in rating[game_code]:
        if pl_id in id_and_names[game_code]:
            pl_name = id_and_names[game_code][pl_id]
            if pl_id in answer:
                votes = answer[pl_id]
            else:
                votes = 0
        else:
            pl_name = "bot"
            votes = answer["bot"]
        if votes == 1:
            cur_rating += f"{i}. <b>{pl_name}</b> +{votes} голос, <b>итого {rating[game_code][pl_id]}</b>\n"
        elif votes == 2 or votes == 3 or votes == 4:
            cur_rating += f"{i}. <b>{pl_name}</b> +{votes} голоса, <b>итого {rating[game_code][pl_id]}</b>\n"
        else:
            cur_rating += f"{i}. <b>{pl_name}</b> +{votes} голосов, <b>итого {rating[game_code][pl_id]}</b>\n"

        i += 1
    for pl in players:
        bot.send_message(pl, cur_rating, parse_mode="HTML")

    # новый раунд
    players_hand_cards(game_code)

golosov_mes_ids = {} #словарь со всеми id стола для замены потом на результаты

# callback для table
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('choose:'))
def choose_callback_handler(callback_query):

    data = callback_query.data.split(':')
    player_id = callback_query.message.chat.id
    game_code = data[1]
    additional_parameter = data[2]
    photos_per_row = int(data[3])
    kolvo_empty = int(data[4])
    message_idd = callback_query.message.message_id


    if additional_parameter.isdigit():  # число
        button_number = int(additional_parameter) + 1  # тк 0 карта-ситуация
        #второй раз нажать на ту же кнопку
        mozno_li_nazat = True
        if battle_cards[game_code][player_id] == button_number:
            mozno_li_nazat = False
        else:
            battle_cards[game_code][player_id] = button_number # чел выбрал эту карту
        if mozno_li_nazat:
            # позиция - большой  мем memes[button_number]
            num_buttons = len(cards_on_table[game_code]['photos_on_table']) - 2

            # callback
            callback_data_list = [f"choose:{game_code}:{i}:{photos_per_row}:{kolvo_empty}" for i in range(num_buttons)]
            vote = "vote"
            zero = "zero"
            callback_vote_for_this = f"choose:{game_code}:{vote}:{photos_per_row}:{kolvo_empty}"
            callback_zero = f"choose:{game_code}:{zero}:{photos_per_row}:{kolvo_empty}"

            buttons = []
            numb_za_kot_progolos = battle_cards[game_code][player_id]
            for i, callback_data in enumerate(callback_data_list):
                cur = cards_on_table[game_code]['photos_on_table'][i+1][0]

                if cur == player_id:
                    if i+1 == numb_za_kot_progolos:
                        button_text = "твой👆"
                    else:
                        button_text = "твой"
                elif i+1 == numb_za_kot_progolos:
                    button_text = f"{i+1}👆"
                else:
                    button_text = str(i+1)

                #button_text = "твой мем" if cur == player_id else str(i+1)

                # Создаем кнопку и добавляем ее в список кнопок
                button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
                buttons.append(button)

            # добавляем пустышки
            for empty in range(kolvo_empty):
                buttons.append(types.InlineKeyboardButton(" ", callback_data=callback_zero))

            markup = types.InlineKeyboardMarkup(row_width=photos_per_row)
            send_meme_button = types.InlineKeyboardButton("Проголосовать за выбранный мем",
                                                          callback_data=callback_vote_for_this)

            markup.add(*buttons)
            markup.add(send_meme_button)

            # плашка

            blank_com = Image.open(io.BytesIO(blank_table[game_code]))
            x = blank_com.width // 4 * (button_number - 1)
            if len(buttons) == 4:
                y = blank_com.height - 16
            elif button_number <= 4:
                y = 4 * blank_com.height // 5 - 28
            else:
                y = blank_com.height - 28
                x = blank_com.width // 4 * (button_number - 4 - 1)

            whole_picture = add_mem_plashka(game_code, numb_za_kot_progolos-1, (x, y))
            whole_picture_ = Image.open(whole_picture)
            new_width = 640
            new_height = int(new_width / whole_picture_.width * whole_picture_.height)
            resized_whole_picture = whole_picture_.resize((new_width, new_height))

            bot.edit_message_media(
                chat_id=player_id,
                message_id=callback_query.message.message_id,
                media=types.InputMediaPhoto(resized_whole_picture),
                reply_markup=markup
            )

    # elif additional_parameter == 'zero': # Обработка запроса для пустых кнопок
        # send_message_to_players(game_code, "zer")

    elif additional_parameter == 'vote':
        num_buttons = len(cards_on_table[game_code]['photos_on_table']) - 2
        progolosoval(player_id, game_code, photos_per_row, kolvo_empty, message_idd, num_buttons)


def situation_plus_bar_blank(game_code):
    #cards_on_table[game_code]['photos_on_table']

    situation = Image.open(io.BytesIO(cards_on_table[game_code]['photos_on_table'][0]))
    new_width = 479
    new_height = 665
    resized_sit = situation.resize((new_width, new_height))
    bar = Image.open(io.BytesIO(cards_on_table[game_code]['photos_on_table'][-1]))

    # resize bottom
    resized_bar = bar.resize((1101, bar.height * 1101 // bar.width))

    table_height = 665 + resized_bar.height
    table_width = 1101

    # Создаем белое изображение
    table_image = Image.new('RGB', (table_width, table_height), (255, 255, 255))

    # Вычисляем координаты для размещения фотографий по центру
    x_offset_image1 = -3
    y_offset_image1 = 0
    x_offset_image2 = 0
    y_offset_image2 = 665

    # Размещаем фотографии на белом фоне
    table_image.paste(resized_sit, (x_offset_image1, y_offset_image1))
    table_image.paste(resized_bar, (x_offset_image2, y_offset_image2))


    image_io = BytesIO()
    table_image.save(image_io, format='PNG')
    image_io.seek(0)

    return image_io

def add_mem_plashka(game_code, number, position): #от 0
    blank = Image.open(io.BytesIO(blank_table[game_code]))
    mem = Image.open(io.BytesIO(cards_on_table[game_code]['photos_on_table'][number + 1][1]))


    blank.paste(plashka_4, position)

    table_width = 1101
    table_height = blank.height

    if mem.height > mem.width:  # вертикаль
        new_width = 479
        new_height = 665
        resized_mem = mem.resize((new_width, new_height))
        # Вычисляем координаты для размещения фотографий по центру
        x_offset_image2 = 476 + (table_width - 479 - resized_mem.width) // 2
        y_offset_image2 = 0
    else:
        new_width = 680
        new_height = 490
        resized_mem = mem.resize((new_width, new_height))
        # Вычисляем координаты для размещения фотографий по центру
        x_offset_image2 = 430
        y_offset_image2 = (640 - resized_mem.height) // 2

    # Размещаем фотографии на белом фоне
    blank.paste(resized_mem, (x_offset_image2, y_offset_image2))


    image_io = BytesIO()
    blank.save(image_io, format='PNG')
    image_io.seek(0)


    return image_io


stop_waiting_meme_chose = {}
stop_waiting_golosov = {}

#разыгровка карт
def table(player_id, game_code):
    battle_cards[game_code] = {}
    voted_battle_cards[game_code] = {}
    stop_waiting_meme_chose[game_code] = True
    stop_waiting_golosov[game_code] = False

    players = active_games[game_code]['players']
    active_players = players_order[game_code]

    #добавляем рандомные фотки
    if len(active_players) < 4:
        if players_hand[game_code]['round'] == 1:
            send_message_to_players(game_code,
                                    "У вас меньше 4 игроков, поэтому с вами играет бот! Попробуйте его обыграть ахах 😈")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            features = {}
            big_images_bynumb = OrderedDict()
            cards_links = []
            #for i in range (8 - len(players)):
            for i in range(4 - len(active_players)):
                card_link = random_choice_of_link_meme(game_code)
                cards_links.append(card_link)

                future = executor.submit(download_big_photo, card_link)
                features[future] = card_link
            # Дождитесь завершения всех загрузок больших фотографий
            for future in concurrent.futures.as_completed(features):
                card_number = features[future]
                result = future.result()
                big_images_bynumb[card_number] = result

            for number in cards_links:
                cards_on_table[game_code]['photos_on_table'].append(['bot', big_images_bynumb[number].getvalue()])

    # перемешиваю карты
    rest_of_list = cards_on_table[game_code]['photos_on_table'][1:].copy()
    random.shuffle(rest_of_list)
    cards_on_table[game_code]['photos_on_table'][1:] = rest_of_list

    situation_card = cards_on_table[game_code]['photos_on_table'][0]
    #перемешиваем все мемы. на 0 месте остаётся ситуация


    # переделываем склейку, делаем blank ситуация + бар
    '''# верхняя часть стола, первоначальная позциия
    top_pic = left_plus_right(game_code, BytesIO(situation_card),
                              BytesIO(cards_on_table[game_code]['photos_on_table'][1][1]))
'''
    memes = []
    for mem in cards_on_table[game_code]['photos_on_table'][1:]:  # берем все кроме 0, тк 0 - ситуация
        memes.append(mem[1])
        # работает

    low_pic = all_cards_on_the_table(game_code, memes)

    # добавляем бар ко всем картам (ситуация, карты, бар)
    cards_on_table[game_code]['photos_on_table'].append(low_pic.getvalue())

    #генерим склейку
    blank = situation_plus_bar_blank (game_code)

    blank_table[game_code] = blank.getvalue()


    # добавляем 0 позицию (плашку и мем)
    x = 0
    com_blank = Image.open(blank)
    if len(cards_on_table[game_code]['photos_on_table']) - 2 == 4:
        y = com_blank.height - 16
    else:
        y = 4 * com_blank.height // 5 - 28
    whole_picture = add_mem_plashka(game_code, 0, (x, y))
    whole_picture_ = Image.open(whole_picture)

    new_width = 640
    new_height = int(new_width / whole_picture_.width * whole_picture_.height)
    resized_whole_picture = whole_picture_.resize((new_width, new_height))

    num_buttons = len(memes)
    # количество кнопочек в ряду
    photos_per_row = 4

    # количество пустышек
    kolvo_rows = math.ceil(num_buttons / photos_per_row)
    vsego_mest = kolvo_rows * photos_per_row
    kolvo_empty = vsego_mest - num_buttons

    # callback
    callback_data_list = [f"choose:{game_code}:{i}:{photos_per_row}:{kolvo_empty}" for i in range(num_buttons)]
    vote = "vote"
    zero = "zero"
    callback_vote_for_this = f"choose:{game_code}:{vote}:{photos_per_row}:{kolvo_empty}"
    callback_zero = f"choose:{game_code}:{zero}:{photos_per_row}:{kolvo_empty}"

    golosov_mes_ids[game_code] = {}
    for cur_player in players:  # потом возможно надо будет создать список игроков, которые отправили мем в игру (то есть не все)
        buttons = []
        # если игрок вкинул мем
        if cur_player in active_players:
            battle_cards[game_code][cur_player] = 1
            numb_za_kot_progolos = battle_cards[game_code][cur_player]
            for i, callback_data in enumerate(callback_data_list):
                cur = cards_on_table[game_code]['photos_on_table'][i + 1][0]
                if cur == cur_player:
                    if i+1 == numb_za_kot_progolos:
                        button_text = "твой👆"
                    else:
                        button_text = "твой"
                elif  i+1 == numb_za_kot_progolos:
                    button_text = f"{i+1}👆"
                else:
                    button_text = str(i+1)
                # Создаем кнопку и добавляем ее в список кнопок
                button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
                buttons.append(button)
        # если игрок не успел вкинуть мем
        else:
            battle_cards[game_code][cur_player] = 1
            numb_za_kot_progolos = battle_cards[game_code][cur_player]
            for i, callback_data in enumerate(callback_data_list):
                cur = cards_on_table[game_code]['photos_on_table'][i + 1][0]
                if i + 1 == numb_za_kot_progolos:
                    button_text = f"{i + 1}👆"
                else:
                    button_text = str(i + 1)
                # Создаем кнопку и добавляем ее в список кнопок
                button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
                buttons.append(button)

        # добавляем пустышки
        for empty in range (kolvo_empty):
                buttons.append(types.InlineKeyboardButton(" ", callback_data=callback_zero))

        markup = types.InlineKeyboardMarkup(row_width=photos_per_row)
        send_meme_button = types.InlineKeyboardButton("Проголосовать за выбранный мем", callback_data=callback_vote_for_this)
        markup.add(*buttons)
        markup.add(send_meme_button)

        picture = copy.deepcopy(resized_whole_picture)

        all_combined_images[game_code].append(picture)

        message = bot.send_photo(chat_id=cur_player, photo=picture, reply_markup=markup)
        golosov_mes_ids[game_code][cur_player] = message.message_id

        # Устанавливаем таймер на удаление сообщения через 5 секунд
        if cur_player == players[-1]:  # последний игрок
            #time.sleep(10)
            wait_thread = threading.Thread(target=wait_and_check_golosov(game_code))
            wait_thread.start()
            wait_thread.join()
            if (game_code not in voted_players or len(voted_players[game_code]) == 0) and not stop_waiting_golosov[game_code]:
                bot.send_message(player_id, "Никто не проголосовал")
            # проголосовали не все
            elif not stop_waiting_golosov[game_code] and len(active_games[game_code]['players']) != len(voted_players[game_code]):
                del voted_players[game_code]
                kolvo_buttons = len(cards_on_table[game_code]['photos_on_table']) - 2
                progolosoval_prt_2(game_code, kolvo_buttons, photos_per_row, kolvo_empty)


# Функция для удаления отредактированного сообщения


# Обработчик callback-запроса
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('combine:'))
def combine_callback_handler(callback_query):
    data = callback_query.data.split(':')
    player_id = callback_query.message.chat.id
    game_code = data[1]
    additional_parameter = data[2]

    if additional_parameter == "send_meme_button": # игрок хочет отправить мем в игру
        if game_code not in flag_pl_otpravil:
            flag_pl_otpravil[game_code] = []
        if player_id in flag_pl_otpravil[game_code]:
            bot.send_message(player_id, "Ты уже отправил свой мем! Немного подожди:)")
        else:
            flag_pl_otpravil[game_code].append(player_id)

            # запоминаем id чтобы потом удалить
            sit = bot.send_message(player_id, "Вы отправили этот мем в игру. Дождёмся других игроков")

            chosen_mem_number = cards_on_table[game_code][player_id]
            chosen_photo = BytesIO(photo_bar_players[game_code][player_id][chosen_mem_number])

            if game_code not in kolvo_players_that_send_mem:
                kolvo_players_that_send_mem[game_code] = 1
                players_order[game_code] = []
            else:
                kolvo_players_that_send_mem[game_code] += 1

            bot.edit_message_media(chat_id=player_id, message_id=callback_query.message.message_id, media=types.InputMediaPhoto(chosen_photo))

            # 1 - удалить из руки
            #send_message_to_players(game_code, str(len(players_hand[game_code][player_id])))

            del players_hand[game_code][player_id][chosen_mem_number] #хранили 5 номеров карт, теперь 4
            del photo_bar_players[game_code][player_id][chosen_mem_number] #хранили bytes 5 мемов и бар, теперь храним 4 фотки мемов
            photo_bar_players[game_code][player_id].pop()

            # 2 - отправить на стол потом добавить что добавляется список из pl_id and bytesIO
            #cards_on_table[game_code]['photos_on_table'].append(chosen_photo.getvalue())
            #cards_on_table[game_code]['photos_on_table'].append(chosen_photo.getvalue())
            cards_on_table[game_code]['photos_on_table'].append([player_id, chosen_photo.getvalue()])
            players_order[game_code].append(player_id) #отсортированный список игроков

            if len(active_games[game_code]['players']) == kolvo_players_that_send_mem[game_code]:
                flag_pl_otpravil[game_code] = []
                kolvo_players_that_send_mem[game_code] = 0
                send_message_to_players(game_code, "Все игроки отправили мемы. Время выбирать самый смешной!")


                # удаляем сообщения из чатов


                table(player_id, game_code)



    else: #игрок пока выбирает мем
        bar = BytesIO(photo_bar_players[game_code][player_id][5]) #bar

        big_photo = BytesIO()
        button_1 = "1"
        button_2 = "2"
        button_3 = "3"
        button_4 = "4"
        button_5 = "5"

        # изменилось ли фото
        mozno_li_obnovlat = True

        if additional_parameter == "first_meme":
            big_photo = BytesIO(photo_bar_players[game_code][player_id][0])
            if cards_on_table[game_code][player_id] == 0:
                mozno_li_obnovlat = False
            else:
                cards_on_table[game_code][player_id] = 0
            button_1 = "1👆"
        elif additional_parameter == "second_meme":
            big_photo = BytesIO(photo_bar_players[game_code][player_id][1])
            if cards_on_table[game_code][player_id] == 1:
                mozno_li_obnovlat = False
            else:
                cards_on_table[game_code][player_id] = 1
            button_2 = "2👆"
        elif additional_parameter == "third_meme":
            big_photo = BytesIO(photo_bar_players[game_code][player_id][2])
            if cards_on_table[game_code][player_id] == 2:
                mozno_li_obnovlat = False
            else:
                cards_on_table[game_code][player_id] = 2
            button_3 = "3👆"
        elif additional_parameter == "fourth_meme":
            big_photo = BytesIO(photo_bar_players[game_code][player_id][3])
            if cards_on_table[game_code][player_id] == 3:
                mozno_li_obnovlat = False
            else:
                cards_on_table[game_code][player_id] = 3
            button_4 = "4👆"
        elif additional_parameter == "fifth_meme":
            big_photo = BytesIO(photo_bar_players[game_code][player_id][4])
            if cards_on_table[game_code][player_id] == 4:
                mozno_li_obnovlat = False
            else:
                cards_on_table[game_code][player_id] = 4
            button_5 = "5👆"

        if mozno_li_obnovlat == True:
            combined_image_io = top_plus_bottom(big_photo, bar)

            #плашка
            main_image = Image.open(big_photo)
            x = cards_on_table[game_code][player_id] * 128
            if (main_image.width < main_image.height): #вертикальная
                y = 640 - 2
            else:
                y = main_image.height + 461 // 5 - 2

            new_image = insert_image_to_main(combined_image_io, (x, y), 5)

            additional_parameter_1 = "first_meme"
            additional_parameter_2 = "second_meme"
            additional_parameter_3 = "third_meme"
            additional_parameter_4 = "fourth_meme"
            additional_parameter_5 = "fifth_meme"
            additional_parameter_6 = "send_meme_button"
            callback_data_1 = f"combine:{game_code}:{additional_parameter_1}"
            callback_data_2 = f"combine:{game_code}:{additional_parameter_2}"
            callback_data_3 = f"combine:{game_code}:{additional_parameter_3}"
            callback_data_4 = f"combine:{game_code}:{additional_parameter_4}"
            callback_data_5 = f"combine:{game_code}:{additional_parameter_5}"
            callback_send_meme = f"combine:{game_code}:{additional_parameter_6}"

            # кнопочки
            markup = types.InlineKeyboardMarkup(row_width=5)
            first_meme = types.InlineKeyboardButton(button_1, callback_data=callback_data_1)
            ''', number=hand_cards[1],  BytesIO=bottom_image_path'''
            second_meme = types.InlineKeyboardButton(button_2, callback_data=callback_data_2)
            third_meme = types.InlineKeyboardButton(button_3, callback_data=callback_data_3)
            fourth_meme = types.InlineKeyboardButton(button_4, callback_data=callback_data_4)
            fifth_meme = types.InlineKeyboardButton(button_5, callback_data=callback_data_5)
            send_meme_button = types.InlineKeyboardButton("Отправить выбранный мем", callback_data=callback_send_meme)
            markup.add(first_meme, second_meme, third_meme, fourth_meme, fifth_meme)
            markup.add(send_meme_button)

            bot.edit_message_media(
                chat_id=player_id,
                message_id=callback_query.message.message_id,
                media=types.InputMediaPhoto(new_image),
                reply_markup=markup
            )




#карты на руках
# players_hand[game_code][player_id]



def download_big_photo(big_photo_link):
    try:
        image = Image.open(requests.get(big_photo_link, stream=True).raw)
    except Exception as e:
        # Обработка ошибки
        print(f"Нельзя загрузить большое фото")

    big_photo_io = io.BytesIO()  # скачиваем фотки большие
    image.save(big_photo_io, format='PNG')
    big_photo_io.seek(0)

    return big_photo_io

def optimization_hand_cards(game_code, player_id):
    if game_code not in all_combined_images:
        all_combined_images[game_code] = []
    if game_code not in players_hand:
        players_hand[game_code] = {}

    '''#генерим все ссылки на все мемы. появляется deck_of_meme_cards, trash_memes
    generate_meme_links(game_code)'''

    #all_meme_links = [i for i in range(1, 251)]  # all numbers of memes
    '''if game_code not in chosen_memes:
        chosen_memes[game_code] = all_meme_links'''

    players_hand[game_code][player_id] = []
    if game_code not in photo_bar_players:
        photo_bar_players[game_code] = {}
    photo_bar_players[game_code][player_id] = []

    features = {}
    big_images_bynumb = OrderedDict()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for number in range(5):
            card_link = random_choice_of_link_meme(game_code)
            #card_number = 4
            players_hand[game_code][player_id].append(card_link)  # добавили номер

            try:
                future = executor.submit(download_big_photo, card_link)
                features[future] = card_link
            except Exception as e:
                print(f"Ошибка при загрузке изображения: {e}")
                send_message_to_players(game_code, "ошибка")

        # Дождитесь завершения всех загрузок больших фотографий
        for future in concurrent.futures.as_completed(features):
            try:
                card_number = features[future]
                result = future.result()
                big_images_bynumb[card_number] = result
            except Exception as e:
                # Обработка ошибок при обработке результатов future
                print(f"Ошибка при обработке результатов: {e}")
                send_message_to_players(game_code, f"Ошибка при обработке результатов: {e}")

        if game_code in players_hand:
            for number in players_hand[game_code][player_id]:
                if game_code in photo_bar_players:
                    photo_bar_players[game_code][player_id].append(big_images_bynumb[number].getvalue())


    # первоначальный расклад (видна 0 карта)
    if game_code in photo_bar_players:
        hand_cards = players_hand[game_code][player_id]
        small_photos_numbers = hand_cards[0:]

        bottom_images = combine_small_pic(player_id, small_photos_numbers)  # bar
    # send_photo_to_players(game_code, bottom_images)
    if game_code in photo_bar_players:
        photo_bar_players[game_code][player_id].append(bottom_images.getvalue())  # добавили в бар сам ба
        initial_main_photo = BytesIO(photo_bar_players[game_code][player_id][0])  # распаковка фото в BytesIO

        combined_image_io = top_plus_bottom(initial_main_photo, bottom_images)

        main_image = Image.open(initial_main_photo)
        x = 0
        if (main_image.width < main_image.height):  # вертикальная
            y = 640 - 2
        else:
            y = main_image.height + 461 // 5 - 2
        new_image = insert_image_to_main(combined_image_io, (x, y), 5)

    if game_code in all_combined_images:
        all_combined_images[game_code].append(new_image)



def optimization_update_hands (player_id, game_code):
    # global all_combined_images
    # у всех игроков пополняются руки до 5 карт

    # для теста
    features = {}
    big_images_bynumb = OrderedDict()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        card_link = random_choice_of_link_meme(game_code)
        # send_message_to_players(game_code, str(len(chosen_memes[game_code])))
        players_hand[game_code][player_id].append(card_link)  # добавили номер

        future = executor.submit(download_big_photo, card_link)
        features[future] = card_link

        # Дождитесь завершения всех загрузок больших фотографий
        for future in concurrent.futures.as_completed(features):
            card_number = features[future]
            result = future.result()
            big_images_bynumb[card_number] = result
        photo_bar_players[game_code][player_id].append(
            big_images_bynumb[players_hand[game_code][player_id][-1]].getvalue())

    # первоначальный расклад (видна 0 карта)
    hand_cards = players_hand[game_code][player_id]
    small_photos_numbers = hand_cards[0:]

    bottom_images = combine_small_pic(player_id, small_photos_numbers)  # bar
    # send_photo_to_players(game_code, bottom_images)

    photo_bar_players[game_code][player_id].append(bottom_images.getvalue())  # добавили в бар сам ба
    initial_main_photo = BytesIO(photo_bar_players[game_code][player_id][0])  # распаковка фото в BytesIO

    combined_image_io = top_plus_bottom(initial_main_photo, bottom_images)

    main_image = Image.open(initial_main_photo)
    x = 0
    y = main_image.height + 461 // 5 - 2
    new_image = insert_image_to_main(combined_image_io, (x, y), 5)

    all_combined_images[game_code].append(new_image)

def delete_stuff(game_code):
    del active_games[game_code]
    del flag_vse_progolos[game_code]
    if game_code in rating:
        del rating[game_code]
    '''if game_code in chosen_photos:
        del chosen_photos[game_code]'''
    if game_code in cards_on_table:
        del cards_on_table[game_code]
    # del voted_players[game_code]
    if game_code in battle_cards:
        del battle_cards[game_code]
    del all_combined_images[game_code]
    if game_code in messages_ids:
        del messages_ids[game_code]
    if game_code in blank_table:
        del blank_table[game_code]
    del players_hand[game_code]
    if game_code in flag_pl_otpravil:
        del flag_pl_otpravil[game_code]
    if game_code in kolvo_players_that_send_mem:
        del kolvo_players_that_send_mem[game_code]
    if game_code in players_order:
        del players_order[game_code]
    if game_code in mozno_li_nazat_gotovo:
        del mozno_li_nazat_gotovo[game_code]
    if game_code in now_obnov:
        del now_obnov[game_code]
    if game_code in robocassa_first_time:
        del robocassa_first_time[game_code]
    if game_code in ids_3_gotovo:
        del ids_3_gotovo[game_code]
    if game_code in mozno_nazad_v_menu:
        del mozno_nazad_v_menu[game_code]
    '''if game_code in chosen_memes:
        del chosen_memes[game_code]'''

    del photo_bar_players[game_code]
    del message_list_of_players[game_code]


#запонимнаем список игроков с прошлого раунда
#remember_players = {}

#сыграть ещё раз
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('repeat:'))
def repeat(callback_query):
    data = callback_query.data.split(':')
    player_id = callback_query.from_user.id
    pl_name = callback_query.from_user.first_name
    game_code = data[1]
    # удаляем прошлое сообщение
    message_id = callback_query.message.message_id
    bot.delete_message(player_id, message_id)
    #первый раз нажали
    if game_code not in remember_players:
        remember_players[game_code] = copy.copy(active_games[game_code])
        id_and_names[game_code][remember_players[game_code]['creator']] = id_and_names[game_code][active_games[game_code]['creator']]

        #стираем всю информацию
        delete_stuff(game_code)

        active_games[game_code] = {}
        active_games[game_code]['players'] = []
        active_games[game_code]['usernames'] = []

    if game_code not in id_and_names:
        id_and_names[game_code] = {}

    if player_id not in active_games[game_code]['players']:
        if player_id == remember_players[game_code]['creator']:
            active_games[game_code]['players'].append(player_id)
            active_games[game_code]['usernames'].append(pl_name)
            active_games[game_code]['creator'] = player_id
            # Сохраняем информацию об игре
            flag_vse_progolos[game_code] = False
            id_and_names[game_code][player_id] = pl_name

            # Отправляем ссылку создателю игры
            message_1 = bot.send_message(player_id, f"Продолжаем игру с кодом: {game_code}")
            message_id_1 = message_1.message_id

            if len(active_games[game_code]['players']) > 1:
                update_players_message(game_code, player_id, pl_name)
            else:
                create_players_message(game_code, player_id)

            markup = types.InlineKeyboardMarkup(row_width=2)
            callback_data_start = f"start:{game_code}:{message_id_1}"

            start_game_button = types.InlineKeyboardButton("Начать игру", callback_data=callback_data_start)
            callback_data_drop = f"drop:{game_code}:{message_id_1}:{0}"
            mozno_nazad_v_menu[game_code] = True
            # назад
            drop_button = types.InlineKeyboardButton("Назад в меню", callback_data=callback_data_drop)
            markup.add(start_game_button, drop_button)
            bot.send_message(player_id, f'Когда все присоединятся, нажмите "Начать игру"', reply_markup=markup)

            optimization_hand_cards(game_code, player_id)
        else:
            #добавляем игрока, если криэйтор есть
            if 'creator' in active_games[game_code]:
                join_existing_game(player_id, str(pl_name), game_code)
            else:

                join_existing_game(player_id, str(pl_name), game_code)

timer_hands = {}
hands_mes_id = {} #лежат
import time
from telegram import Update
from telegram.ext import Updater, CallbackContext, CallbackQueryHandler


def wait_and_check_meme_chose(game_code):
    global stop_waiting_meme_chose
    print("Waiting for 10 seconds...")
    for _ in range(10):
        if stop_waiting_meme_chose[game_code]:
            print("Waiting was interrupted.")
            return
        time.sleep(1)
    print("Waiting finished.")

def wait_and_check_golosov(game_code):
    global stop_waiting_golosov
    print("Waiting for 10 seconds...")
    for _ in range(10):
        if stop_waiting_golosov[game_code]:
            print("Waiting was interrupted.")
            return
        time.sleep(1)
    print("Waiting finished.")
def players_hand_cards(game_code):
    global all_combined_images
    global hands_mes_id
    global stop_waiting_meme_chose
    stop_waiting_meme_chose[game_code] = False
    if game_code not in players_hand:
        players_hand[game_code] = {}

    players = active_games[game_code]['players']

    # если не набран максимум очков
    first_key, first_value = next(iter(rating[game_code].items()))

    # first_value - максимум голосов для окончания
    # окончание игры
    if first_value >= 1:
        if first_key in id_and_names[game_code]:
            pl_name = id_and_names[game_code][first_key]
        else:
            pl_name = "bot"
        for player_id in players:
            bot.send_message(player_id, f"Игра окончена, Победитель <b>{pl_name}</b>!🎉", parse_mode="HTML")
        # предложение сыграть ещё
        markup = types.InlineKeyboardMarkup(row_width=2)
        callback_data_repeat = f"repeat:{game_code}"
        callback_data_leave = f"menu:{game_code}"
        repeat_the_game = types.InlineKeyboardButton("Сыграть ещё", callback_data=callback_data_repeat)
        leave_the_game = types.InlineKeyboardButton("Выйти из игры", callback_data=callback_data_leave)
        markup.add(repeat_the_game, leave_the_game)
        for player_id in players:
            bot.send_message(player_id, text="Ещё партеечку?😏", reply_markup=markup)

    else:
        if players_hand.get(game_code, {}).get('round'):  # новый раунд
            # генерация рук и down time
            for player_id in players:
                optimization_update_hands(player_id, game_code)

            flag_vse_progolos[game_code] = False
            players_hand[game_code]['round'] += 1  # счётчик раундов
            for pl in players:
                bot.send_message(pl, f"<b>{players_hand[game_code]['round']} раунд</b>", parse_mode="HTML")
            #send_message_to_players(game_code, f"{players_hand[game_code]['round']} раунд")
            send_situation(game_code)

            #send_message_to_players(game_code, "Выберите свой мем:")
            # запоминаем id чтобы потом удалить
            players = active_games[game_code]['players']
            for player_id in players:
                sit = bot.send_message(player_id, "Выберите свой мем:")


            # в бар надо добавить элемент мем и бар(мини фотки)
        else:  # 1 раунд
            for pl in players:
                bot.send_message(pl, f"<b>1 раунд</b>", parse_mode="HTML")
            #send_message_to_players(game_code, "1 раунд")
            send_situation(game_code)
            #send_message_to_players(game_code, "Выберите свой мем:")
            players = active_games[game_code]['players']
            for player_id in players:
                sit = bot.send_message(player_id, "Выберите свой мем:")
            players_hand[game_code]['round'] = 1


        flag = 0
        for player_id in players:
            combined_image_io = all_combined_images[game_code][flag]
            flag += 1
            additional_parameter_1 = "first_meme"
            additional_parameter_2 = "second_meme"
            additional_parameter_3 = "third_meme"
            additional_parameter_4 = "fourth_meme"
            additional_parameter_5 = "fifth_meme"
            additional_parameter_6 = "send_meme_button"
            callback_data_1 = f"combine:{game_code}:{additional_parameter_1}"
            callback_data_2 = f"combine:{game_code}:{additional_parameter_2}"
            callback_data_3 = f"combine:{game_code}:{additional_parameter_3}"
            callback_data_4 = f"combine:{game_code}:{additional_parameter_4}"
            callback_data_5 = f"combine:{game_code}:{additional_parameter_5}"
            callback_send_meme = f"combine:{game_code}:{additional_parameter_6}"

            # cards_on_table[game_code] = {'photos_on_table': [], 'player_ids': []}
            # у всех пока выбрана 0 карта
            cards_on_table[game_code][player_id] = 0

            # кнопочки
            markup = types.InlineKeyboardMarkup(row_width=5)
            first_meme = types.InlineKeyboardButton("1👆", callback_data=callback_data_1)
            ''', number=hand_cards[1],  BytesIO=bottom_image_path'''
            second_meme = types.InlineKeyboardButton("2", callback_data=callback_data_2)
            third_meme = types.InlineKeyboardButton("3", callback_data=callback_data_3)
            fourth_meme = types.InlineKeyboardButton("4", callback_data=callback_data_4)
            fifth_meme = types.InlineKeyboardButton("5", callback_data=callback_data_5)
            send_meme_button = types.InlineKeyboardButton("Отправить выбранный мем", callback_data=callback_send_meme)
            markup.add(first_meme, second_meme, third_meme, fourth_meme, fifth_meme)
            markup.add(send_meme_button)

            message = bot.send_photo(player_id, combined_image_io, reply_markup=markup)
            if game_code not in hands_mes_id:
                hands_mes_id[game_code] = {}
            hands_mes_id[game_code][player_id] = message.message_id


            # Устанавливаем таймер на удаление сообщения через 5 секунд
            if player_id == players[-1]: #последний игрок
                #time.sleep(10)
                wait_thread = threading.Thread(target=wait_and_check_meme_chose(game_code))
                wait_thread.start()
                wait_thread.join()
                # если никто не выбрал мем
                if game_code not in flag_pl_otpravil and not stop_waiting_meme_chose[game_code]:
                    bot.delete_message(player_id, message.message_id)
                    bot.send_message(player_id, "Никто не выбрал мем, поэтому игра завершилась")
                    # перевести на главное меню и дропнуть игру
                    if game_code in active_games and player_id == active_games[game_code]['creator']:
                        delete_stuff(game_code)
                        del id_and_names[game_code]

                        del all_available_tarifs_memes[game_code]
                        del nazat_tarifs_memes[game_code]
                        del all_available_tarifs_sit[game_code]
                        del nazat_tarifs_sit[game_code]
                        del deck_of_sit_cards[game_code]
                        del trash_sit[game_code]
                        del deck_of_meme_cards[game_code]
                        del trash_memes[game_code]

                    markup = types.InlineKeyboardMarkup(row_width=1)
                    new_game_button = types.InlineKeyboardButton("Новая игра", callback_data="new_game")
                    join_game_button = types.InlineKeyboardButton("Присоединиться к игре", callback_data="join_game")
                    rules_button = types.InlineKeyboardButton("Правила игры", callback_data="rules")
                    markup.add(new_game_button, join_game_button, rules_button)
                    bot.send_message(player_id, text="А ну-ка, выбирай", reply_markup=markup)

                elif len(active_games[game_code]['players']) != kolvo_players_that_send_mem[game_code] and not stop_waiting_meme_chose[game_code]:
                    flag_pl_otpravil[game_code] = []
                    kolvo_players_that_send_mem[game_code] = 0
                    send_message_to_players(game_code,
                                            "Среди нас халявщики, которые не успели отправить мем. Голосуем за самых быстрых!")
                    for pl in players:
                        # если игрок не вкинул карту в иру
                        if pl not in players_order[game_code]:
                            # удаляем его руку с кнопками
                            bot.delete_message(chat_id = pl, message_id=hands_mes_id[game_code][pl])
                            bot.send_message(pl, "Ты не успел вкинуть свой мем в игру:(")

                    table(player_id, game_code)

            '''
            timer = threading.Timer(10, delete_edited_message,
                                    args=[player_id, update.callback_query.message.message_id])
            timer.start()
            # Сохраняем таймер в словаре
            timer_hands[player_id] = timer'''


#надо как-то сделать юот бесконечным, а то ун умирает через какое-то время, если его не использовать
bot.polling(none_stop=True, timeout = 31536000)













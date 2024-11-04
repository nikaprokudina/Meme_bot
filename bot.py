# Timer 2 рабочие
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
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



# import decimal
# import hashlib
# from urllib import parse
from collections import OrderedDict
# import datetime
import copy
# import files
# import database
# import payment

bot = telebot.TeleBot("6227889329:AAHP40wbfEJ0ZWgMCb7tqGBT9DoDtLWfOKY")
# bot = telebot.TeleBot("6478379933:AAG_OaYSRm0vZDIT565vT4aON5v6_oyFtmU") #guy

# Словарь для хранения активных игр
active_games = {}
cards_on_table = {}
battle_cards = {}  # голоса за карты
kolvo_players_that_send_mem = {}
voted_players = {}
players_order = {}
id_and_names = {}  # по id можно расшифровать имя игрока

photo_bar_players = {}

# Словарь для хранения сообщения списка игроков
message_list_of_players = {}
usernames = {}
rating = {}  # действующий рейтинг игроков (если игроков мало, то среди них есть бот
flag_vse_progolos = {}
flag_pl_otpravil = {}
messages_ids = {}
all_combined_images = {}
blank_table = {}  # пустой стол голсования
chosen_photos = {}
# chosen_memes = {}
players_hand = {}

# все доступные тарифы meme 0,1,2,3,4
all_available_tarifs_memes = {}
nazat_tarifs_memes = {}
kolvo_naz_green_buttons = {}
kolvo_naz_green_sit = {}
all_available_tarifs_sit = {}
nazat_tarifs_sit = {}

deck_of_sit_cards = {}
trash_sit = {}

deck_of_meme_cards = {}  # колода карт мемов в игре
trash_memes = {}  # сброс мемов

# запонимнаем список игроков с прошлого раунда
remember_players = {}

mozno_li_nazat_gotovo = {}
# для оплаты (+ добавить в удаление)
# mozno_obnovlat = {}

# ids_chose_lots_all = {}  # хранение всех id сообщений с выбором лотов, которые нужно будет удалить после нажатия на кнопку обновить
# now_obnov = {}  # содержится в ids_3_otmena отмена или обновть

ids_3_otmena = {}
# choose_the_duration_of_subscription_first_time = {}  # bool нажата ли робокасса или нет
# оплата
# pay_button_first_time = {} # bool нажата ли кнопка оплаты или нет

ids_3_gotovo = {}  # словарь, где хранятся 3 id сообщений с кнопками (выбор мемов и ситуаций) + кнопка готово
mozno_nazad_v_menu = {}

# Создаем блокировку для синхронизации доступа к словарю message_list_of_players
message_list_lock = threading.Lock()

mozno_play_again = {}
mozno_start_the_game = {}

halavshik = {}

#оплата
# flag_double_oplata = {}
# flag_double_cancel_payment = {}

# Устанавливаем команды
try:
    commands = [
        types.BotCommand("start", "Открыть главное меню"),
        # types.BotCommand("000000", "code")
    ]

    bot.set_my_commands(commands)
except Exception as e:
    logging.error(f"Ошибка при установке команд бота: {e}")


# @bot.message_handler(commands=['000000'])
# def handle_game_code(message):
#     # если это код
#     game_code = '000000'
#     chat_id = message.chat.id
#     if game_code in active_games:
#         pl_name = message.from_user.first_name
#         join_existing_game(chat_id, pl_name, game_code)
#


def send_message_to_players(game_code, message):
    try:
        players = active_games[game_code]['players']
        for player_id in players:
            bot.send_message(player_id, message)
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения игрокам в игре {game_code}: {e}")


def create_players_message(game_code, creator_id):
    try:
        players = active_games[game_code]['players']
        users = active_games[game_code]['usernames']
        name = id_and_names[game_code][creator_id]
        message = "Игроки:\n" + "\n".join(users)

        mes = bot.send_message(creator_id, message)
        message_id = mes.message_id
        with message_list_lock:
            message_list_of_players[game_code] = {}
            message_list_of_players[game_code][creator_id] = message_id
    except Exception as e:
        logging.error(f"Ошибка при создании сообщения для игроков в игре с кодом {game_code}: {e}")


def update_players_message(game_code, new_player_id, creator_name):
    try:
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
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения для игроков в игре с кодом {game_code}: {e}")


def generate_game_code():
    try:
        code = ''.join(random.choices(string.digits, k=6))
        return code
        # return '000000'
    except Exception as e:
        logging.error(f"Ошибка при генерации кода игры: {e}")
        return None

# старт: присоединиться к игре или создать новую
@bot.message_handler(commands=['start'])
def start(message):
    # дропаем прошлую игру
    player_id = message.chat.id
    try:
        # print(str(len(all_players_and_their_codes)))
        if player_id in all_players_and_their_codes and all_players_and_their_codes[player_id] in active_games:
            last_game_code = all_players_and_their_codes[player_id]
            pl_name = id_and_names[last_game_code][player_id]
            #     если криейтор, то дропаем игру у всех
            if player_id == active_games[last_game_code]['creator']:
                for pl_id in active_games[last_game_code]['players']:
                    if pl_id == player_id:
                        bot.send_message(pl_id, "Вы завершили активную игру.")
                    else:
                        bot.send_message(pl_id, f"Ведущий {pl_name} завершил игру.")
                a_nu_ka_main_menu_all(last_game_code)
                delete_stuff_for_next_round(last_game_code)
                delete_stuff_for_repeat(last_game_code)
                delete_rest_stuff(last_game_code)
            else:


                for pl_id in active_games[last_game_code]['players']:
                    if pl_id == player_id:
                        bot.send_message(pl_id, "Отключаем вас от прошлой активной игры.")
                        a_nu_ka_main_menu(player_id)
                    else:
                        bot.send_message(pl_id, f"Игрок {pl_name} покинул игру.")

                # удаляем чела из игры
                active_games[last_game_code]['players'].remove(player_id)
                del all_players_and_their_codes[player_id]
        else:
            try:
                markup = types.InlineKeyboardMarkup(row_width=1)
                new_game_button = types.InlineKeyboardButton("Новая игра", callback_data="new_game")
                join_game_button = types.InlineKeyboardButton("Присоединиться к игре", callback_data="join_game")
                rules_button = types.InlineKeyboardButton("Правила игры", callback_data="rules")
                markup.add(new_game_button, join_game_button, rules_button)
                bot.send_message(message.chat.id, text="Добро пожаловать! Я мемобот:)", reply_markup=markup)
            except Exception as e:
                logging.error(f"Ошибка при выполнении команды /start: {e}")
                bot.send_message(message.chat.id, text="Произошла ошибка, попробуйте позже.")

    except Exception as e:
        logging.error(f"Ошибка при отключении при старте в all_players_and_their_codes: {e}")

    # try:
    #     markup = types.InlineKeyboardMarkup(row_width=1)
    #     new_game_button = types.InlineKeyboardButton("Новая игра", callback_data="new_game")
    #     join_game_button = types.InlineKeyboardButton("Присоединиться к игре", callback_data="join_game")
    #     rules_button = types.InlineKeyboardButton("Правила игры", callback_data="rules")
    #     markup.add(new_game_button, join_game_button, rules_button)
    #     bot.send_message(message.chat.id, text="Добро пожаловать! Я мемобот:)", reply_markup=markup)
    # except Exception as e:
    #     logging.error(f"Ошибка при выполнении команды /start: {e}")
    #     bot.send_message(message.chat.id, text="Произошла ошибка, попробуйте позже.")


# выход в главное меню и удаление игры из активных, если ушёл криэйтор
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('menu:'))
def main_menu(callback_query):
    try:
        data = callback_query.data.split(':')
        player_id = callback_query.from_user.id
        game_code = data[1]
        # удаляем прошлое сообщение
        message_id = callback_query.message.message_id
        bot.delete_message(player_id, message_id)

        if game_code in active_games and player_id == active_games[game_code]['creator']:
            delete_stuff_for_next_round(game_code)
            delete_stuff_for_repeat(game_code)
            delete_rest_stuff(game_code)
            # del kolvo_naz_green_buttons[game_code]
            # del kolvo_naz_green_sit[game_code]
        a_nu_ka_main_menu(player_id)
    except:
        pass
            # logging.error(f"Ошибка в обработчике главного меню: {e}")

# правила игры
@bot.callback_query_handler(func=lambda message: message.data == 'rules')
def rules(message):
    try:
        message_id = message.message.message_id
        player_id = message.message.chat.id
        bot.delete_message(player_id, message_id)

        game_code = -1
        callback_data_leave = f"menu:{game_code}"
        markup = types.InlineKeyboardMarkup(row_width=1)
        back_button = types.InlineKeyboardButton("Назад в меню", callback_data=callback_data_leave)
        markup.add(back_button)
        bot.send_message(player_id, f"<b>💥 КАК ИГРАТЬ? 💥</b> \n\n🔹 Раздай <b>всем по 5 карт мемов.</b> \n"
                                    f"🔹 Положи колоды мемов и ситуаций в центре стола.\n"
                                    f"🔹 Стань судьёй на первый раунд!", parse_mode="HTML")

        bot.send_message(player_id, "<b>🎰 РАУНД ИГРЫ 🎰</b> \n\n"
                                    "<code>1.</code> <b>Судья читает карту ситуации.</b> \n"
                                    "<code>2.</code> <b>Все</b> (кроме судьи) <b>как можно быстрее</b> из карт в руке <b>выкладывают лучший мем</b> в центр стола лицом вниз! \n"
                                    "<code>3.</code> <b>Судья открывает мемы</b> по-очереди, начиная с верхней карты. Верхняя (сыгранная позже) - открывается рядом с колодой, следующие - под ней (карта, сыгранная первой, окажется дальше всех от колоды).\n"
                                    "<code>4.</code> <b>Cудья выбирает лучший мем!</b> \n"
                                    "<code>5.</code> <b>Победитель</b> (чей это был мем) <b>забирает эту карту и все, что выше</b> (сыгранные позже) и кладет перед собой - это его победная стопка карт! \n"
                                    "<code>6.</code> Все пополняют руку до 6 карт. \n\n"
                                    "<i>Следующий - новый судья на новый раунд.</i>\n"
                                    "<i>Закончилась колода / привезли пиццу? Считайте карты в победных стопках. У кого больше - тот мемолог!</i>",
                         parse_mode="HTML")


    except Exception as e:
        pass
        # logging.error(f"Ошибка в обработчике правил игры: {e}")


@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('meme_tarif:'))
def chose_tarif_meme(callback_query):
    try:
        with message_list_lock:
            global all_available_tarifs_memes
            global nazat_tarifs_memes
            global kolvo_naz_green_buttons
            data = callback_query.data.split(':')
            player_id = callback_query.from_user.id
            game_code = data[1]
            button = int(data[2])


            # включить когда будет оплата
            # if button not in all_available_tarifs_memes[game_code]: # нажали на кнопку с замком (хотят купить)
            #     choose_the_duration_of_subscription(player_id, button, game_code)

            # else:
            if button not in nazat_tarifs_memes[game_code]:  # кнопка ненажата -> нажата = зеленый
                nazat_tarifs_memes[game_code].append(button)
                kolvo_naz_green_buttons[game_code] += 1
            else:  # кнопка была нажата, теперь нет -> белый
                nazat_tarifs_memes[game_code].remove(button)
                kolvo_naz_green_buttons[game_code] -= 1
            logos = []
            for number in range(5):  # проходимся по всем кнопкам
                if number in nazat_tarifs_memes[game_code]:  # должна быть зелёной
                    logos.append("🟢️ ")
                # удалить потом когда подключат оплату
                else:
                    logos.append("⚪ ")
                # elif number in all_available_tarifs_memes[game_code]:  # доступна, но не нажата (белый)
                #     logos.append("⚪️ ")
                # else:  # замок
                #     logos.append("💰")

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

            bot.edit_message_text(chat_id=player_id, message_id=callback_query.message.message_id,
                                  text="Приятель, тебе придётся выбрать набор мемов-картинок:",
                                  reply_markup=markup)
    except Exception as e:
        logging.error(f"Ошибка в обработчике выбора тарифа мемов: {e}")

# # БЛОК ОПЛАТЫ
# # из документации
# def calculate_signature(*args) -> str:
#     return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()
#
#
# flag_mes_oplat_id = {}
#
# # STARS
#
# all_names_of_tarifs = ['Демка', 'МЕМЫ: Весело и в точку!', 'МЕМЫ 2: СССР и 90-е', 'МЕМЫ 3: Котики и пр. нелюди',
#                        'МЕМЫ НЕЙРО']
#
#
#
# @bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('oplata:'))
# def oplata(callback_query):
#     data = callback_query.data.split(':')
#     game_code = data[5]
#     global all_names_of_tarifs
#     chat_id = callback_query.from_user.id
#     days_text = data[1]
#     days_number = data[2]  # 1, 30, 365
#     price = int(data[3])
#     button = int(data[4])
#
#
#
#     if not flag_double_oplata[game_code]:
#         flag_double_oplata[game_code] = True
#         try:
#             bot.delete_message(chat_id, ids_3_otmena[game_code][2])  # вернуться к выбору карт
#         except:
#             pass
#
#         if game_code in flag_mes_oplat_id:
#             try:
#                 bot.delete_message(chat_id, flag_mes_oplat_id[game_code])  # прошлая invoice
#             except:
#                 pass
#
#         ids_3_otmena[game_code].pop(2)  # попаем вернуться к выбору
#
#         if button != 1000:
#             name_of_cards = all_names_of_tarifs[int(button)]
#             prices = [types.LabeledPrice(label=f'{name_of_cards} на 1 {days_text}', amount=price)]
#             descrip_text = f'💸 Приобрести "{name_of_cards}" на 1 {days_text} 💸'
#             title_text = f'Набор {name_of_cards}'
#         else:
#             prices = [types.LabeledPrice(label=f'Все наборы на 1 {days_text}', amount=price)]
#             descrip_text = f'💸 Приобрести ВСЕ наборы на 1 {days_text} 💸'
#             title_text = 'ВСЕ наборы'
#
#         try:
#             bot.delete_message(chat_id, ids_3_otmena[game_code][3])
#         except:
#             pass
#         try:
#             bot.delete_message(chat_id, ids_3_otmena[game_code][2])
#         except:
#             pass
#         try:
#             ids_3_otmena[game_code].pop(2)
#             ids_3_otmena[game_code].pop(2)
#         except:
#             pass
#
#         call_data = f'{chat_id} {callback_query.from_user.username} {button} {days_number}'
#
#         invoice_message = bot.send_invoice(
#             chat_id,
#             title=title_text,
#             description=descrip_text,
#             invoice_payload=call_data,  # что передаём
#             provider_token='',
#             currency='XTR',  # telegram strs
#             prices=prices,
#             start_parameter='test',
#         )
#
#         # Отправляем сообщение с кнопкой "Отмена" и сохраняем его message_id
#         markup = types.InlineKeyboardMarkup()
#         flag_double_cancel_payment[game_code] = False
#         cancel_button = types.InlineKeyboardButton(text="Отмена", callback_data=f"cancel_payment:{game_code}")
#         markup.add(cancel_button)
#         cancel_message = bot.send_message(chat_id, "Вы можете отменить оплату, нажав кнопку ниже:", reply_markup=markup)
#
#
#         ids_3_otmena[game_code].extend([cancel_message.message_id, invoice_message.message_id])
#         flag_double_oplata[game_code] = False
#
#         # pay_button_first_time[game_code] = True
#
#     # Обработчик для кнопки "Отмена"
#     @bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('cancel_payment:'))
#     def cancel_payment(callback_query):
#         data = callback_query.data.split(':')
#         game_code = data[1]
#         chat_id = callback_query.from_user.id
#
#         if not flag_double_cancel_payment[game_code]:
#             flag_double_cancel_payment[game_code] = True
#             try:
#                 bot.delete_message(chat_id, ids_3_otmena[game_code][-1])  # Удаляем инвойс
#             except Exception as e:
#                 pass
#
#             try:
#                 bot.delete_message(chat_id, ids_3_otmena[game_code][-2])  # Удаляем сообщение об отмене
#             except Exception as e:
#                 pass
#             try:
#                 bot.delete_message(chat_id, ids_3_otmena[game_code][0])  # Удаляем сообщение 1
#             except Exception as e:
#                 pass
#             try:
#                 bot.delete_message(chat_id, ids_3_otmena[game_code][1])  # Удаляем сообщение 2
#             except Exception as e:
#                 pass
#             ids_3_otmena[game_code] = []
#
#             markup = types.InlineKeyboardMarkup(row_width=1)
#             callback_data_podtverdit = f"podtverdit:{game_code}"
#             mozno_li_nazat_gotovo[game_code] = True
#             podtverdit_choice = types.InlineKeyboardButton("Готово!", callback_data=callback_data_podtverdit)
#             now_obnov[game_code] = False
#             choose_the_duration_of_subscription_first_time[game_code] = True
#             markup.add(podtverdit_choice)
#             message = bot.send_message(chat_id, "Когда выберешь колоды, жми", reply_markup=markup)
#             message_id = message.message_id
#             ids_3_gotovo[game_code].append(message_id)  # добавили 3 элементом id сообщения "готово"
#
#             # ids_3_otmena[game_code] = []
#             flag_double_cancel_payment[game_code] = False
#
#
# @bot.pre_checkout_query_handler(func=lambda query: True)
# def checkout(pre_checkout_query):
#     bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
#
# @bot.message_handler(content_types=['successful_payment'])
# def got_payment(message):
#     # payment_info = message.successful_payment.to_python()
#     # game_code = payment_info['invoice_payload'].split(':')[1]
#     bot.send_message(message.chat.id, 'Оплата прошла успешно! Спасибо за покупку.')
#     # chat_id = message.chat.id
#
#     successful_payment_info_all = message.successful_payment
#     useful_info_payment = (successful_payment_info_all.invoice_payload).split()
#     player_id = int(useful_info_payment[0])
#     player_nick = useful_info_payment[1]
#     button = int(useful_info_payment[2])
#     days = int(useful_info_payment[3])
#     mess = bot.send_message(message.chat.id, 'Оплата прошла успешно!')
#
#     # Получить текущую дату и время
#     current_datetime = datetime.datetime.now()
#     # Прибавить нужный тариф
#     if days == 1:
#         expiration = current_datetime + datetime.timedelta(days=1)
#     elif days == 30:  # Прибавить месяц
#         expiration = current_datetime.replace(month=current_datetime.month + 1)
#     else:  # Прибавить год
#         expiration = current_datetime.replace(year=current_datetime.year + 1)
#     # Преобразовать новые даты и время в текстовый формат (строку)
#     one_month_later_text = expiration.strftime("%d.%m.%Y %H:%M:%S")
#
#     all_names_in_table = ['Демка', 'База', 'СССР', 'Котики', 'НЕЙРО']
#     if button != 1000:
#         text = all_names_in_table[button]
#         database.add_subscription(player_id, player_nick, text, one_month_later_text)
#     else:
#         for text in all_names_in_table[1:]:
#             database.add_subscription(player_id, player_nick, text, one_month_later_text)
#
#
#
# # (менюшки с выбором лотов)
# def choose_the_duration_of_subscription(user_id, button, game_code):
#     global ids_3_otmena
#
#     # удаляем кнопку готово
#     if choose_the_duration_of_subscription_first_time[game_code]:
#         gotovo_id = ids_3_gotovo[game_code][2]
#         ids_3_gotovo[game_code].pop()
#         bot.delete_message(user_id, gotovo_id)
#
#     keyboard_1 = telebot.types.InlineKeyboardMarkup()
#     flag_double_oplata[game_code] = False
#     callback_oplata_100 = f"oplata:день:{1}:{100}:{button}:{game_code}"
#     callback_oplata_300 = f"oplata:месяц:{30}:{300}:{button}:{game_code}"
#     callback_oplata_900 = f"oplata:год:{365}:{900}:{button}:{game_code}"
#
#     pay_button_day = types.InlineKeyboardButton(text=f"день: 100 ₽.", callback_data=callback_oplata_100)
#     pay_button_month = telebot.types.InlineKeyboardButton(text=f"мес: 300 ₽.", callback_data=callback_oplata_300)
#     pay_button_year = telebot.types.InlineKeyboardButton(text=f"год: 900 ₽.", callback_data=callback_oplata_900)
#
#     keyboard_1.add(pay_button_day, pay_button_month, pay_button_year)
#     if button == 1:
#         emoji = "🎯"
#     elif button == 2:
#         emoji = "🕺"
#     elif button == 3:
#         emoji = "😻"
#     else:
#         emoji = "⚡️"
#     if not choose_the_duration_of_subscription_first_time[game_code]:
#         try:
#             message_1 = bot.edit_message_text(chat_id=user_id, message_id=ids_3_otmena[game_code][0],
#                                               text=f"Купить <b>доступ к сету «{all_names_of_tarifs[button]}{emoji}»</b> (250 мемов + 100 ситуаций) на период:",
#                                               reply_markup=keyboard_1, parse_mode="HTML")
#             message_1_id = ids_3_otmena[game_code][0]
#         except:
#             message_1_id = ids_3_otmena[game_code][0]
#     else:
#         message_1 = bot.send_message(user_id,
#                                      text=f"Купить <b>доступ к сету «{all_names_of_tarifs[button]}{emoji}»</b> (250 мемов + 100 ситуаций) на период:",
#                                      reply_markup=keyboard_1, parse_mode="HTML")
#         message_1_id = message_1.message_id
#
#     # 1000 - button на все тарифы
#     callback_oplata_600_all = f"oplata:день:{1}:{600}:{1000}:{game_code}"
#     callback_oplata_1800_all = f"oplata:месяц:{30}:{1800}:{1000}:{game_code}"
#     callback_oplata_5400_all = f"oplata:год:{365}:{5400}:{1000}:{game_code}"
#
#     pay_button_day = types.InlineKeyboardButton(text=f"день: 600 ₽.", callback_data=callback_oplata_600_all)
#     pay_button_month = telebot.types.InlineKeyboardButton(text=f"мес: 1800 ₽.", callback_data=callback_oplata_1800_all)
#     pay_button_year = telebot.types.InlineKeyboardButton(text=f"год: 5400 ₽.", callback_data=callback_oplata_5400_all)
#
#     keyboard_2 = telebot.types.InlineKeyboardMarkup()
#     keyboard_2.add(pay_button_day, pay_button_month, pay_button_year)
#     if not choose_the_duration_of_subscription_first_time[game_code]:
#         message_2_id = ids_3_otmena[game_code][1]
#     else:
#         message_2 = bot.send_message(user_id,
#                                      text="Купить <b>полный доступ</b> ко всем существующим и будущим сетам на период:",
#                                      reply_markup=keyboard_2, parse_mode="HTML")
#         message_2_id = message_2.message_id
#
#     call_data = f"otmena_pokupki:{game_code}"
#     # call_data = f"pay_mem:{game_code}"
#     markup = types.InlineKeyboardMarkup(row_width=1)
#     mozno_obnovlat[game_code] = True
#     chestno = types.InlineKeyboardButton(text="Вернуться к выбору карт для игры", callback_data=call_data)
#     markup.row(chestno)
#
#     if not choose_the_duration_of_subscription_first_time[game_code]:
#         message_3_id = ids_3_otmena[game_code][2]
#     else:
#         choose_the_duration_of_subscription_first_time[game_code] = False
#         message_3 = bot.send_message(chat_id=user_id, text="Чтобы вернуться к выбору сетов, нажми на кнопку",
#                                      reply_markup=markup)
#         message_3_id = message_3.message_id
#
#     ids_3_otmena[game_code] = [message_1_id, message_2_id, message_3_id]



from datetime import datetime, timedelta

from telebot import types

#
# @bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('otmena_pokupki:'))
# def payment(callback_query):
#     global mozno_li_nazat_gotovo
#     global now_obnov
#     data = callback_query.data.split(':')
#     game_code = data[1]
#     player_id = callback_query.from_user.id
#
#     # удаляем 3 сообщения
#     for id_mess in ids_3_otmena[game_code]:
#         bot.delete_message(player_id, id_mess)
#     ids_3_otmena[game_code] = []
#
#     # высылаем кнопку готово и добавляем её в массив
#     markup = types.InlineKeyboardMarkup(row_width=1)
#     callback_data_podtverdit = f"podtverdit:{game_code}"
#     mozno_li_nazat_gotovo[game_code] = True
#     podtverdit_choice = types.InlineKeyboardButton("Готово!", callback_data=callback_data_podtverdit)
#     now_obnov[game_code] = False
#     choose_the_duration_of_subscription_first_time[game_code] = True
#     markup.add(podtverdit_choice)
#     message = bot.send_message(player_id, "Когда выберешь колоды, жми", reply_markup=markup)
#     message_id = message.message_id
#     ids_3_gotovo[game_code].append(message_id)  # добавили 3 элементом id сообщения "готово"
#
#
# # СИТУАЦИИ
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('sit_tarif:'))
def chose_tarif_sit(callback_query):
    with message_list_lock:
        global all_available_tarifs_sit
        global nazat_tarifs_sit
        global kolvo_naz_green_sit
        try:
            data = callback_query.data.split(':')
            player_id = callback_query.from_user.id
            game_code = data[1]
            button = int(data[2])

            # if button not in all_available_tarifs_sit[game_code]:
            #     choose_the_duration_of_subscription(player_id, button, game_code)
            # else:
            if button not in nazat_tarifs_sit[game_code]:  # кнопка ненажата -> нажата = зеленый
                nazat_tarifs_sit[game_code].append(button)
                kolvo_naz_green_sit[game_code] += 1
            else:  # кнопка была нажата, теперь нет -> белый
                nazat_tarifs_sit[game_code].remove(button)
                kolvo_naz_green_sit[game_code] -= 1
            logos = []
            for number in range(5):  # проходимся по всем кнопкам
                if number in nazat_tarifs_sit[game_code]:  # должна быть зелёной
                    logos.append("🟢️ ")
                # удалить потом когда подключат оплату
                else:
                    logos.append("⚪ ")
                # elif number in all_available_tarifs_sit[game_code]:  # доступна, но не нажата (белый)
                #     logos.append("⚪️ ")
                # else:  # замок
                #     logos.append("💰")

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
            bot.edit_message_text(chat_id=player_id, message_id=callback_query.message.message_id,
                                  text=f"И ещё потрудись выбрать карты ситуаций:",
                                  reply_markup=markup)
        except Exception as e:
            logging.error(f"Ошибка при обновлении сообщения выбора ситуаций для игры {game_code}: {e}")


# выбор колоды мемов и ситуаций
def chose_deck_of_cards(player_id, game_code):
    try:
        global all_available_tarifs_memes
        global nazat_tarifs_memes
        global kolvo_naz_green_buttons
        global kolvo_naz_green_sit
        global all_available_tarifs_sit
        global nazat_tarifs_sit
        # 0-id, 1-name, 2-tarif, 3-data

        # add(player_id, "sakuharo", "Котики", "10.08.2021 15:30:00")

        # смотрим на подписки игрока
        # user_subscriptions = database.get_user_subscriptions(player_id)

        nazat_tarifs_memes[game_code] = [0]
        nazat_tarifs_sit[game_code] = [0]

        # все доступные тарифы 0,1,2,3,4
        all_available_tarifs_memes[game_code] = [0]
        all_available_tarifs_sit[game_code] = [0]

        if game_code not in kolvo_naz_green_buttons:
            kolvo_naz_green_buttons[game_code] = 1
        if game_code not in kolvo_naz_green_sit:
            kolvo_naz_green_sit[game_code] = 1

        # выбор мемов
        demo_meme = f"meme_tarif:{game_code}:{0}"
        base_meme = f"meme_tarif:{game_code}:{1}"
        cccp_meme = f"meme_tarif:{game_code}:{2}"
        cats_meme = f"meme_tarif:{game_code}:{3}"
        neiro_meme = f"meme_tarif:{game_code}:{4}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        demo = types.InlineKeyboardButton("🟢️ Демка (по 10 из всех сетов)", callback_data=demo_meme)
        # без оплаты всё доступно
        base = types.InlineKeyboardButton("⚪️ База (250 шт.)", callback_data=base_meme)
        cccp = types.InlineKeyboardButton("⚪️ СССР (250 шт.)", callback_data=cccp_meme)
        cats = types.InlineKeyboardButton("⚪️ Котики (250 шт.)", callback_data=cats_meme)
        neiro = types.InlineKeyboardButton("⚪ НЕЙРО (250 шт.)", callback_data=neiro_meme)

        # если подписок вообще нет
        # if not user_subscriptions:
        #     base = types.InlineKeyboardButton("💰База (250 шт.)", callback_data=base_meme)
        #     cccp = types.InlineKeyboardButton("💰СССР (250 шт.)", callback_data=cccp_meme)
        #     cats = types.InlineKeyboardButton("💰Котики (250 шт.)", callback_data=cats_meme)
        #     neiro = types.InlineKeyboardButton("💰НЕЙРО (250 шт.)", callback_data=neiro_meme)
        # # если есть подписка на что-то
        # else:
        #     # Получить текущую дату и время
        #     current_datetime = datetime.datetime.now()
        #
        #     tarifs_and_data = {}  # тарифы - ключи, даты-values
        #     print(tarifs_and_data)
        #     for raw in user_subscriptions:
        #         # добавляем тариф
        #         if raw['tarif'] not in tarifs_and_data:
        #             tarifs_and_data[raw['tarif']] = [raw['expiration_date']]
        #         # если несколь дат, то добавляем и сортируем
        #         else:
        #             tarifs_and_data[raw['tarif']].append(raw['expiration_date'])
        #             tarifs_and_data[raw['tarif']].sort()
        #     if "База" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["База"][-1],
        #                                                                 "%d.%m.%Y %H:%M:%S") > current_datetime:
        #         base = types.InlineKeyboardButton("⚪️ База (250 шт.)", callback_data=base_meme)
        #         all_available_tarifs_memes[game_code].append(1)
        #     else:
        #         base = types.InlineKeyboardButton("💰База (250 шт.)", callback_data=base_meme)
        #     if "СССР" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["СССР"][-1],
        #                                                                 "%d.%m.%Y %H:%M:%S") > current_datetime:
        #         cccp = types.InlineKeyboardButton("⚪️ СССР (250 шт.)", callback_data=cccp_meme)
        #         all_available_tarifs_memes[game_code].append(2)
        #     else:
        #         cccp = types.InlineKeyboardButton("💰СССР (250 шт.)", callback_data=cccp_meme)
        #     if "Котики" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["Котики"][-1],
        #                                                                   "%d.%m.%Y %H:%M:%S") > current_datetime:
        #         cats = types.InlineKeyboardButton("⚪️ Котики (250 шт.)", callback_data=cats_meme)
        #         all_available_tarifs_memes[game_code].append(3)
        #     else:
        #         cats = types.InlineKeyboardButton("💰Котики (250 шт.)", callback_data=cats_meme)
        #     if "НЕЙРО" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["НЕЙРО"][-1],
        #                                                                  "%d.%m.%Y %H:%M:%S") > current_datetime:
        #         neiro = types.InlineKeyboardButton("⚪ НЕЙРО (250 шт.)", callback_data=neiro_meme)
        #         all_available_tarifs_memes[game_code].append(4)
        #     else:
        #         neiro = types.InlineKeyboardButton("💰НЕЙРО (250 шт.)", callback_data=neiro_meme)
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

        # всё доступно ничего не платим
        base = types.InlineKeyboardButton("⚪️ База (100 шт.)", callback_data=base_sit)
        cccp = types.InlineKeyboardButton("⚪️ СССР (100 шт.)", callback_data=cccp_sit)
        cats = types.InlineKeyboardButton("⚪️ Котики (100 шт.)", callback_data=cats_sit)
        neiro = types.InlineKeyboardButton("⚪ НЕЙРО (100 шт.)", callback_data=neiro_sit)

        # # если подписок вообще нет
        # if not user_subscriptions:
        #     base = types.InlineKeyboardButton("💰База (100 шт.)", callback_data=base_sit)
        #     cccp = types.InlineKeyboardButton("💰СССР (100 шт.)", callback_data=cccp_sit)
        #     cats = types.InlineKeyboardButton("💰Котики (100 шт.)", callback_data=cats_sit)
        #     neiro = types.InlineKeyboardButton("💰НЕЙРО (100 шт.)", callback_data=neiro_sit)
        # # если есть подписка на что-то
        # else:
        #     # Получить текущую дату и время
        #     current_datetime = datetime.datetime.now()
        #
        #     tarifs_and_data = {}  # тарифы - ключи, даты-values
        #     for raw in user_subscriptions:
        #         # добавляем тариф
        #         if raw['tarif'] not in tarifs_and_data:
        #             tarifs_and_data[raw['tarif']] = [raw['expiration_date']]
        #         # если несколь дат, то добавляем и сортируем
        #         else:
        #             tarifs_and_data[raw['tarif']].append(raw['expiration_date'])
        #             tarifs_and_data[raw['tarif']].sort()
        #     if "База" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["База"][-1],
        #                                                                 "%d.%m.%Y %H:%M:%S") > current_datetime:
        #         base = types.InlineKeyboardButton("⚪️ База (100 шт.)", callback_data=base_sit)
        #         all_available_tarifs_sit[game_code].append(1)
        #     else:
        #         base = types.InlineKeyboardButton("💰База (100 шт.)", callback_data=base_sit)
        #     if "СССР" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["СССР"][-1],
        #                                                                 "%d.%m.%Y %H:%M:%S") > current_datetime:
        #         cccp = types.InlineKeyboardButton("⚪️ СССР (100 шт.)", callback_data=cccp_sit)
        #         all_available_tarifs_sit[game_code].append(2)
        #     else:
        #         cccp = types.InlineKeyboardButton("💰СССР (100 шт.)", callback_data=cccp_sit)
        #     if "Котики" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["Котики"][-1],
        #                                                                   "%d.%m.%Y %H:%M:%S") > current_datetime:
        #         cats = types.InlineKeyboardButton("⚪️ Котики (100 шт.)", callback_data=cats_sit)
        #         all_available_tarifs_sit[game_code].append(3)
        #     else:
        #         cats = types.InlineKeyboardButton("💰Котики (100 шт.)", callback_data=cats_sit)
        #     if "НЕЙРО" in tarifs_and_data and datetime.datetime.strptime(tarifs_and_data["НЕЙРО"][-1],
        #                                                                  "%d.%m.%Y %H:%M:%S") > current_datetime:
        #         neiro = types.InlineKeyboardButton("⚪ НЕЙРО (100 шт.)", callback_data=neiro_sit)
        #         all_available_tarifs_sit[game_code].append(4)
        #     else:
        #         neiro = types.InlineKeyboardButton("💰НЕЙРО (100 шт.)", callback_data=neiro_sit)
        markup.row(demo)
        markup.add(base, cccp, cats, neiro)
        message2 = bot.send_message(player_id, f"И ещё потрудись выбрать карты ситуаций:", reply_markup=markup)
        return (message.message_id, message2.message_id)
    except Exception as e:
        logging.error(f"Ошибка при выборе колоды мемов и ситуаций: {e}")

# список всех пользователей и коды их игр на данный момент
all_players_and_their_codes = {}

# новая игра
@bot.callback_query_handler(func=lambda message: message.data == 'new_game')
def new_game(message):
    try:
        player_id = message.message.chat.id
        # user_id = message.from_user.id
        pl_name = message.from_user.first_name
        game_code = generate_game_code()
        ids_3_gotovo[game_code] = []
        # перед этим попробовать удалить из all_players_and_their_codes если есть и отключить игру
        all_players_and_their_codes[player_id] = game_code

        # try:
        #     if player_id in all_players_and_their_codes and all_players_and_their_codes[player_id] in active_games:
        #         last_game_code = all_players_and_their_codes[player_id]
        #         #     если криейтор, то дропаем игру у всех
        #         if player_id == active_games[last_game_code]['creator']:
        #             for pl_id in active_games[last_game_code]['players']:
        #                 if pl_id != player_id:
        #                     bot.send_message(pl_id, "Вы завершили активную игру.")
        #                 else:
        #                     bot.send_message(pl_id, f"Ведущий {pl_name} завершил игру.")
        #             a_nu_ka_main_menu_all(last_game_code)
        #             delete_stuff_for_repeat(last_game_code)
        #             delete_rest_stuff(last_game_code)
        #         else:
        #             bot.send_message(player_id, f"Отключаем вас от прошлой активной игры.")
        # except Exception as e:
        #     logging.error(f"Ошибка при отключении при старте в all_players_and_their_codes: {e}")

    except Exception as e:
        logging.error(f"Ошибка при создании новой игры: {e}")

    try:
        message_id = message.message.message_id
        bot.delete_message(player_id, message_id)
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения с кнопкой создания новой игры")

    # Сохраняем информацию об игре
    try:
        active_games[game_code] = {'creator': player_id, 'players': [player_id], 'usernames': [pl_name]}
        flag_vse_progolos[game_code] = False
        id_and_names[game_code] = {}
        id_and_names[game_code][player_id] = pl_name
    except Exception as e:
        logging.error(f"Ошибка при сохранении информации об игре: {e}")

    # выбор колоды мемов и ситуаций
    try:
        message_id_1, message_id_2 = chose_deck_of_cards(player_id, game_code)
        ids_3_gotovo[game_code].append(message_id_1)
        ids_3_gotovo[game_code].append(message_id_2)
    except Exception as e:
        logging.error(f"Ошибка при выборе колоды для игры {game_code}: {e}")

    try:
        markup = types.InlineKeyboardMarkup(row_width=1)
        callback_data_podtverdit = f"podtverdit:{game_code}"
        mozno_li_nazat_gotovo[game_code] = True
        podtverdit_choice = types.InlineKeyboardButton("Готово!", callback_data=callback_data_podtverdit)
        # now_obnov[game_code] = False
        # choose_the_duration_of_subscription_first_time[game_code] = True
        markup.add(podtverdit_choice)
        message = bot.send_message(player_id, "Когда выберешь колоды, жми", reply_markup=markup)
        message_id = message.message_id
        ids_3_gotovo[game_code].append(message_id)  # добавили 3 элементом id сообщения "готово"
    except Exception as e:
        logging.error(f"Ошибка при создании кнопок подтверждения для игры {game_code}: {e}")


@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('podtverdit:'))
def podtverdit_choices(callback_query):
    try:
        global kolvo_naz_green_buttons
        global kolvo_naz_green_sit
        global ids_3_gotovo
        data = callback_query.data.split(':')
        player_id = callback_query.from_user.id
        game_code = data[1]
    except Exception as e:
        logging.error(f"Ошибка при разборе данных callback в podtverdit: {e}")
        return

    try:
        if mozno_li_nazat_gotovo[game_code] and kolvo_naz_green_buttons[game_code] > 0 and kolvo_naz_green_sit[game_code] > 0:
            mozno_li_nazat_gotovo[game_code] = False
            message_id_1 = ids_3_gotovo[game_code][0]
            message_id_2 = ids_3_gotovo[game_code][1]

            # удаляем прошлое сообщение
            try:
                message_id = callback_query.message.message_id
                bot.delete_message(player_id, message_id_1)
                bot.delete_message(player_id, message_id_2)
                bot.delete_message(player_id, message_id)
                if len(ids_3_gotovo[game_code]) == 4:
                    bot.delete_message(player_id, ids_3_gotovo[game_code][3])
                    ids_3_gotovo[game_code].pop()
            except Exception as e:
                logging.error(f"Ошибка при удалении сообщения с кнопкой подтверждения: {e}")

            # генерим все ссылки на все мемы. появляется deck_of_meme_cards, trash_memes
            generate_meme_links(game_code)
            generate_sit_links(game_code)

            # Отправляем ссылку создателю игры
            message_1 = bot.send_message(player_id,
                                         f"Вы создали новую игру! Поделитесь кодом со своими друзьями: {game_code}")
            message_id_1 = message_1.message_id

            creator_id = active_games[game_code]['creator']
            create_players_message(game_code, creator_id)
            message_id_2 = message_list_of_players[game_code][creator_id]

            markup = types.InlineKeyboardMarkup(row_width=2)
            callback_data_start = f"start:{game_code}:{message_id_1}"
            mozno_start_the_game[game_code] = True
            start_game_button = types.InlineKeyboardButton("Начать игру", callback_data=callback_data_start)
            callback_data_drop = f"drop:{game_code}:{message_id_1}:{message_id_2}"
            mozno_nazad_v_menu[game_code] = True
            drop_button = types.InlineKeyboardButton("Назад в меню", callback_data=callback_data_drop)
            markup.add(start_game_button, drop_button)
            bot.send_message(player_id, f'Когда все присоединятся, нажмите "Начать игру"', reply_markup=markup)

            optimization_hand_cards(game_code, player_id)
        elif kolvo_naz_green_buttons[game_code] == 0 or kolvo_naz_green_sit[game_code] == 0 and len(ids_3_gotovo[game_code])!= 4:
                message = bot.send_message(player_id, "Нужно выбрать хотябы по одному набору мемов и ситуаций")
                message_id = message.message_id
                ids_3_gotovo[game_code].append(message_id)

    except Exception as e:
        logging.error(f"Ошибка при подтверждении выбора колод: {e}")




@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('drop:'))
def drop(callback_query):
    try:
        data = callback_query.data.split(':')
        player_id = callback_query.from_user.id
        game_code = data[1]
        message_id_1 = data[2]
        message_id_2 = data[3]

        if mozno_nazad_v_menu[game_code]:
            mozno_nazad_v_menu[game_code] = False
            # удаляем прошлое сообщение
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

            for pl_id in active_games[game_code]['players']:
                if pl_id == player_id:
                    bot.send_message(pl_id, "Вы завершили игру.")
                else:
                    bot.send_message(pl_id, f"Ведущий {callback_query.from_user.first_name} завершил игру.")

            a_nu_ka_main_menu_all(game_code)

            try:
                delete_stuff_for_next_round(game_code)
                delete_stuff_for_repeat(game_code)
                delete_rest_stuff(game_code)
            except Exception as e:
                logging.error(f"Ошибка при удалении данных игры в drop {game_code}: {e}")
    except Exception as e:
        logging.error(f"Ошибка при удалении игры: {e}")


@bot.callback_query_handler(func=lambda message: message.data == 'join_game')
def join_game(message):
    try:
        player_id = message.message.chat.id
        message_id = message.message.message_id
        bot.delete_message(player_id, message_id)

        game_code = -1
        callback_data_leave = f"menu:{game_code}"
        markup = types.InlineKeyboardMarkup(row_width=1)
        back_button = types.InlineKeyboardButton("Назад в меню", callback_data=callback_data_leave)
        markup.add(back_button)
        bot.send_message(player_id, f"Введите код игры", reply_markup=markup)
    except:
        pass
        # logging.error(f"Ошибка при создании сообщения ввода кода игры для пользователя: {e}")


# чтение текста (код игры)
@bot.message_handler(content_types=['text'])
def handle_game_code(message):
    # если это код
    try:
        if len(message.text) == 6 and message.text.isdigit():
            game_code = message.text
            chat_id = message.chat.id
            if game_code in active_games:
                pl_name = message.from_user.first_name
                join_existing_game(chat_id, pl_name, game_code)
            else:
                bot.send_message(chat_id, f"Игра с кодом {game_code} не найдена.")
    except Exception as e:
        logging.error(f"Ошибка при обработке кода игры: {e}")

def a_nu_ka_main_menu(player_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    new_game_button = types.InlineKeyboardButton("Новая игра", callback_data="new_game")
    join_game_button = types.InlineKeyboardButton("Присоединиться к игре", callback_data="join_game")
    rules_button = types.InlineKeyboardButton("Правила игры", callback_data="rules")
    markup.add(new_game_button, join_game_button, rules_button)
    bot.send_message(player_id, text="А ну-ка, выбирай!", reply_markup=markup)

def a_nu_ka_main_menu_all(game_code):
        markup = types.InlineKeyboardMarkup(row_width=1)
        new_game_button = types.InlineKeyboardButton("Новая игра", callback_data="new_game")
        join_game_button = types.InlineKeyboardButton("Присоединиться к игре",
                                                      callback_data="join_game")
        rules_button = types.InlineKeyboardButton("Правила игры", callback_data="rules")
        markup.add(new_game_button, join_game_button, rules_button)

        players = active_games[game_code]['players']
        for pl in players:
            bot.send_message(pl, text="А ну-ка, выбирай!", reply_markup=markup)


def join_existing_game(player_id, pl_name, game_code):
    try:
        players = active_games[game_code]['players']
        game_started = active_games[game_code].get('game_started', False)  # Проверка флага game_started

        if game_started:
            bot.send_message(player_id, f"Игра уже началась. Новые игроки не могут присоединиться.")
            a_nu_ka_main_menu(player_id)

        elif player_id in players:
            bot.send_message(player_id, f"Вы уже присоединены к этой игре.")
        else:
            # перед этим удалить
            all_players_and_their_codes[player_id] = game_code

            # try:
            #     if player_id in all_players_and_their_codes and game_code in active_games:
            #         all_players_and_their_codes[player_id] = game_code
            #     #     если криейтор, то дропаем игру у всех
            #         if player_id == active_games[game_code]['creator']:
            #             for pl_id in active_games[game_code]['players']:
            #                 if pl_id != player_id:
            #                     bot.send_message(pl_id, "Вы завершили активную игру.")
            #                 else:
            #                     bot.send_message(pl_id, f"Ведущий {pl_name} завершил игру.")
            #             a_nu_ka_main_menu_all(game_code)
            #             delete_stuff_for_repeat(game_code)
            #             delete_rest_stuff(game_code)
            #         else:
            #             bot.send_message(player_id, f"Отключаем вас от прошлой активной игры.")
            # except Exception as e:
            #     logging.error(f"Ошибка при отключении во время присоединения в all_players_and_their_codes: {e}")

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
    except Exception as e:
        logging.error(f"Ошибка при присоединении к игре: {e}")

import traceback
# начало игры
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('start:'))
def start_game(callback_query):
    try:
        data = callback_query.data.split(':')
        player_id = callback_query.from_user.id
        game_code = data[1]
        message_id_1 = data[2]
        if mozno_start_the_game[game_code]:
            mozno_start_the_game[game_code] = False
            if game_code in nazat_tarifs_memes and len(nazat_tarifs_memes[game_code]) == 0:
                bot.send_message(player_id, "Нужно выбрать хотябы 1 набор, чтобы начать игру.")
            else:
                # message_id_2 = data[3]
                # основное тело
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
                        try:
                            message_id = callback_query.message.message_id
                            bot.delete_message(player_id, int(message_id_1))
                            bot.delete_message(player_id, message_id)
                            active_games[game_code]['game_started'] = True
                        except Exception as e:
                            logging.error(f"Ошибка при удалении сообщения с кнопкой начала игры: {e}")

                        send_message_to_players(game_code, "Игра началась!")
                        send_message_to_players(game_code, "Впереди вас ждёт 5 раундов!")
                        rating[game_code] = {}
                        for player in players:  # добавляем всех в рейтинг
                            rating[game_code][player] = 0
                        if len(players) < 4:  # если мало игроков, то добавляем бота
                            rating[game_code]["bot"] = 0
                        players_hand_cards(game_code)

                    else:
                        bot.send_message(chat_id, "Нужно хотя бы 2 игрока, чтобы начать игру.")
                else:
                    bot.send_message(chat_id, "Вы не являетесь создателем игры, поэтому не можете её начать.")
            mozno_play_again[game_code] = {}
    except Exception as e:
        logging.error(f"Ошибка при начале игры: {e}\n{traceback.format_exc()}")


####### показ ситуаций пользователю

# список ссылок на ситуации
def generate_sit_links(game_code):
    try:
        global deck_of_sit_cards
        global trash_sit
        global nazat_tarifs_sit
        nabor = nazat_tarifs_sit[game_code]

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
    except Exception as e:
        logging.error(f"Ошибка при генерации ссылок на ситуации: {e}")


# список ссылок на действующие мемы
def generate_meme_links(game_code):  # nabor-список наборов [0,1,2,3,4]
    try:
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
        trash_memes[game_code] = []  # сброс
    except Exception as e:
        logging.error(f"Ошибка при генерации ссылок на мемы: {e}")


# выбор ситуации
def random_choice_of_photo(game_code):
    global deck_of_sit_cards
    global trash_sit

    try:
        if len(deck_of_sit_cards[game_code]) == 0:
            # send_message_to_players(game_code,
            #                         "Ситуации закончились. Теперь вы будете видеть ситуации из колоды сброса. (Можно докупить наборы карт, чтобы играть было ещё веселей!")
            send_message_to_players(game_code,
                                    "Ситуации закончились. Теперь вы будете видеть ситуации из колоды сброса. (В главном меню можно выбрать больше наборов, чтобы играть было веселее!")

            deck_of_sit_cards[game_code] = trash_sit
            trash_sit[game_code] = []

        random_photo_link = random.choice(deck_of_sit_cards[game_code])
        deck_of_sit_cards[game_code].remove(random_photo_link)
        trash_sit[game_code].append(random_photo_link)
        return random_photo_link
    except Exception as e:
        logging.error(f"Ошибка при выборе ситуации: {e}")


# отправить фото в игру
def send_photo_to_players(game_code, photo_url):
    try:
        if game_code in active_games:
            players = active_games[game_code]['players']
            for player_id in players:
                bot.send_photo(player_id, photo_url)
    except Exception as e:
        logging.error(f"Ошибка при отправке фото игрокам: {e}")


def download_situation(link):
    try:
        image = Image.open(requests.get(link, stream=True).raw)
        sit_photo_io = io.BytesIO()  # скачиваем фотки большие
        image.save(sit_photo_io, format='JPEG')
        sit_photo_io.seek(0)
        return sit_photo_io
    except Exception as e:
        logging.error(f"Ошибка при скачивании ситуации: {e}")


# отправка ситуаций
def send_situation(game_code):
    try:
        link = random_choice_of_photo(game_code)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            cards_on_table[game_code] = {}
            cards_on_table[game_code]['photos_on_table'] = []

            future = executor.submit(download_situation, link)
            situation_card = future.result()  # Get the result from the future object
            cards_on_table[game_code]['photos_on_table'].append(situation_card.getvalue())
            # chosen_photo = BytesIO(cards_on_table[game_code]['photos_on_table'][0]) - incorrect

        # запонимаени id situation чтобы удалить потом

        # send_photo_to_players
        players = active_games[game_code]['players']
        for player_id in players:
            sit = bot.send_photo(player_id, cards_on_table[game_code]['photos_on_table'][0])
    except Exception as e:
        try:
            link = random_choice_of_photo(game_code)
            logging.error(f"Ошибка при отправке ситуации, ссылка: {link}: {e}")
        except Exception as e:
            logging.error(f"Ошибка при отправке ситуации: {e}")



### разыгровка руки


# обновления ссылок

def random_choice_of_link_meme(game_code):
    global deck_of_meme_cards
    global trash_memes
    # ссылки на все доступные мемы
    try:
        game_meme_choice = deck_of_meme_cards[game_code]
        if len(game_meme_choice) == 0:
            send_message_to_players(game_code,
                                    "Мемы закончились. Поэтому вы продолжите играть с мемами из колоды сброса. (Дополнительные картинки-мемы можно купить, чтобы игра была ещё интересней!)")
            deck_of_meme_cards[game_code] = trash_memes[game_code]
            trash_memes[game_code] = []
        else:
            random_meme_link = random.choice(game_meme_choice)
            deck_of_meme_cards[game_code].remove(random_meme_link)
            trash_memes[game_code].append(random_meme_link)
            return random_meme_link
    except Exception as e:
        logging.error(f"Ошибка при обновлении ссылок: {e}")


# плашка 1/4
try:
    plashka_url_4 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/cursor275.jpg"
    plashka_response_4 = requests.get(plashka_url_4)
    # if plashka_response_4.status_code == 200:
    plashka_4 = Image.open(BytesIO(plashka_response_4.content))
except Exception as e:
    logging.error(f"Ошибка при загрузке плашки 1/4: {e}")
    plashka_4 = None

# плагшка 1/5
try:
    plashka_url_5 = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/cursor128.jpg"
    plashka_response_5 = requests.get(plashka_url_5)
    plashka_5 = Image.open(BytesIO(plashka_response_5.content))
except Exception as e:
    logging.error(f"Ошибка при загрузке плашки 1/5: {e}")
    plashka_5 = None

# корона
try:
    # crown_url = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/crown.png"
    crown_url = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/tBkC/sZCCxzX7J"
    crown_response = requests.get(crown_url)
    crown = Image.open(BytesIO(crown_response.content))



except Exception as e:
    logging.error(f"Ошибка при загрузке короны: {e}")
    crown = None





# звезда
try:
    # star_url = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/Fu4g/MPnSu7KQs/star.png"
    star_url = "https://thumb.cloud.mail.ru/weblink/thumb/xw1/WUCf/QBR5RRtMY"
    star_response = requests.get(star_url)
    star = Image.open(BytesIO(star_response.content))
except Exception as e:
    logging.error(f"Ошибка при загрузке звезды: {e}")
    star = None

# вставляем плашку
# position = (100, 200)
def insert_image_to_main(image, position, ad_param):
    try:
        main_image = Image.open(image)
    except Exception as e:
        logging.error(f"Ошибка при открытии главного изображения: {e}")
        return None
    try:
        if ad_param == 5:  # hand
            main_image.paste(plashka_5, position)
        elif ad_param == 4:  # 4 голосовалка
            main_image.paste(plashka_4, position)
        elif ad_param == "star":
            if main_image.mode != 'RGBA':
                main_image = main_image.convert('RGBA')
            main_image.paste(star, position, mask=star)
        else:  # crown

            if main_image.mode != 'RGBA':
                main_image = main_image.convert('RGBA')

            main_image.paste(crown, position, mask=crown)
    except Exception as e:
        logging.error(f"Ошибка при вставке изображения на основное изображение: {e}")
        return None

    try:
        new_image = BytesIO()
        main_image.save(new_image, format='PNG')
        new_image.seek(0)
        return new_image
    except Exception as e:
        logging.error(f"Ошибка при сохранении нового изображения: {e}")
        return None


def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки HTTP
        image = Image.open(BytesIO(response.content))
        return image
    except Exception as e:
        logging.error(f"Ошибка при загрузке изображения с URL {url}: {e}")
        return None


# составляем колаж руки
def combine_small_pic(user_id, small_photos_links):
    # Загрузка маленьких изображений параллельно
    small_images_bylinks = OrderedDict()  # OrderedDict для сохранения порядка загруженных изображений

    try:
        # Загрузка маленьких изображений параллельно
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(download_image, link): link for link in small_photos_links}
            for future in concurrent.futures.as_completed(futures):
                link = futures[future]
                # print(link)
                result = future.result()
                if result:
                    small_images_bylinks[link] = result
                else:
                    logging.error(f"Изображение по ссылке {link} не было загружено.")
    except Exception as e:
        logging.error(f"Ошибка при загрузке маленьких изображений: {e}")
        return None

    try:
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
            if image.height > image.width:  # вертикальная
                height = 461 // 5
                izmenil = 640 // height
                width = 461 // izmenil
                image.thumbnail((width, height))
                # image.thumbnail((image.height // 5, image.width // 5))
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
    except Exception as e:
        logging.error(f"Ошибка при создании коллажа изображений для пользователя {user_id}: {e}")
        return None


def top_plus_bottom(main_photo, bottom):
    try:
        main_image = Image.open(main_photo)
        bottom_image = Image.open(bottom)
    except Exception as e:
        logging.error(f"Ошибка при загрузке изображений {main_photo, bottom}: {e}")
        return None

    # Проверка размеров изображений и изменение размеров, если необходимо
    try:
        if main_image.height > main_image.width:
            new_width = round(main_image.width * (548 / main_image.height))
            main_image = main_image.resize((new_width, 548))
            whitespace_width = (bottom_image.width - main_image.width) // 2

            resized_bottom_image = bottom_image
            combined_width = bottom_image.width
            combined_height = main_image.height + bottom_image.height
            combined_image = Image.new('RGB', (combined_width, combined_height), (255, 255, 255))
            combined_image.paste(main_image, (whitespace_width, 0))

            # combined_image = Image.new('RGB', (bottom_image.width, main_image.height + bottom_image.height))
            # combined_image.paste(main_image, (0, 0))
        else:
            if main_image.width != bottom_image.width:
                resized_bottom_image = bottom_image.resize(
                    (main_image.width, bottom_image.height * main_image.width // bottom_image.width))
            else:
                resized_bottom_image = bottom_image
            # Создание нового изображения с объединенными фото
            combined_image = Image.new('RGB', (resized_bottom_image.width, main_image.height + resized_bottom_image.height))
            combined_image.paste(main_image, (0, 0))  # Вставка main_image сверху
        combined_image.paste(resized_bottom_image, (0, main_image.height))  # Вставка resized_bottom_image снизу
    except Exception as e:
        logging.error(f"Ошибка при объединении изображений: {e}")
        return None

    # Отправка объединенного изображения
    try:
        combined_image_io = BytesIO()
        combined_image.save(combined_image_io, format='PNG')
        combined_image_io.seek(0)

        return combined_image_io
    except Exception as e:
            logging.error(f"Ошибка при сохранении объединенного изображения: {e}")
            return None



def left_plus_right(game_code, situation, meme):
    try:
        image1 = Image.open(situation)
        image2 = Image.open(meme)
    except Exception as e:
        logging.error(f"Ошибка при загрузке изображений left {situation} right {meme}: {e}")
        return None

    # Проверка размеров изображений и изменение размеров, если необходимо
    try:
        desired_height = 700
        max_width = image2.width
        max_height = image1.height

        if image2.height > image2.width:  # вертикаль
            table_width = image1.width + 640

        else:
            # Размеры совместного изображения
            table_width = image1.width + image2.width
        table_height = max_height

        # Создаем белое изображение
        table_image = Image.new('RGB', (table_width, table_height), (255, 255, 255))

        if image2.height > image2.width:  # вертикаль
            # Вычисляем координаты для размещения фотографий по центру
            x_offset_image1 = 0
            y_offset_image1 = 0
            x_offset_image2 = image1.width + (table_width - image1.width - image2.width) // 2

            # x_offset_image2 = x_offset_image1 + image1.width
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
    except Exception as e:
        logging.error(f"Ошибка при объединении изображений для игры {game_code}: {e}")
        return None

    try:
        image_io = BytesIO()
        table_image.save(image_io, format='PNG')
        image_io.seek(0)

        return image_io
    except Exception as e:
        logging.error(f"Ошибка при сохранении изображения: {e}")
        return None


def all_cards_on_the_table(game_code, memes):  # дается список фоток
    # for mem in memes:
    #     send_message_to_players(game_code, str(type(mem)))
    #     if (type(mem) == int):
    #         send_message_to_players(game_code, mem)

    try:
        images = [Image.open(BytesIO(mem)) for mem in memes]
    except Exception as e:
        logging.error(f"Ошибка при открытии изображений all_cards_on_the_table: {e}")
        return None
    try:
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
            collage_height = kolvo_rows * max_height // photos_per_row + 5
        else:
            collage_height = kolvo_rows * max_height // photos_per_row + 24
        collage_width = 640

        collage = Image.new('RGB', (collage_width, collage_height), (255, 255, 255))

        # Вставка каждой уменьшенной фотографии на холст
        prev_height = 0
        for i, image in enumerate(images):
            if image.height > image.width:  # вертикальная
                image.thumbnail((image.height // photos_per_row, image.width // photos_per_row))
                x_offset = ((i % photos_per_row) * lil_space_width) + (lil_space_width - image.width) // 2
            else:  # горизонтальная
                image.thumbnail((image.width // photos_per_row, image.height // photos_per_row))
                x_offset = (i % photos_per_row) * lil_space_width

            if i % photos_per_row == 0 and i != 0:  # перешли на новую строку
                prev_height += max_height // photos_per_row + 12
            y_offset = prev_height
            # Вставка уменьшенной фотографии на холст
            collage.paste(image, (x_offset, y_offset))
    except Exception as e:
        logging.error(f"Ошибка при создании коллажа для игры all_cards_on_the_table: {e}")
        return None

    try:
        image_io = io.BytesIO()
        collage.save(image_io, format='PNG')
        image_io.seek(0)
        return image_io
    except Exception as e:
        logging.error(f"Ошибка при сохранении коллажа для игры all_cards_on_the_table: {e}")
        return None


voted_battle_cards = {}  # карты, за которые проголосовали
# can_vote = {}
# отправка голосования
def progolosoval(player_id, game_code, photos_per_row, kolvo_empty, message_idd, kolvo_buttons):
    global all_combined_images
    global flag_vse_progolos


    try:
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
                            all_combined_images[game_code] = []
                        elif player_id not in voted_players[game_code]:
                            voted_players[game_code].append(player_id)
                            znak = 1

                    if znak == 1:
                        if game_code not in message_ids_timer_send_votes_after_sending:
                            message_ids_timer_send_votes_after_sending[game_code] = {}

                        try:
                            bot.edit_message_text(chat_id=player_id,
                                                  message_id=message_ids_timer_send_votes[game_code][player_id],
                                                  text=f"Все игроки отправили мемы. Выбери лучший!", parse_mode="HTML")
                        except:
                            pass

                        players = active_games[game_code]['players']
                        for pl in players:
                            try:
                                bot.edit_message_text(chat_id=pl,
                                                      message_id=message_ids_timer_send_memes_after_sending[game_code][
                                                          pl], text="Ты отправил этот мем.")
                                # rr
                                # bot.delete_message(chat_id=pl,
                                #                   message_id=message_ids_timer_send_memes_after_sending[game_code][pl])
                            except:
                                pass


                        message = bot.send_message(player_id, "Твой голос учтён! Ждём других…")
                        message_ids_timer_send_votes_after_sending[game_code][player_id] = message.message_id

                        with message_list_lock:
                            # добавляем id сообщения
                            if game_code not in messages_ids:
                                messages_ids[game_code] = {}
                            messages_ids[game_code][player_id] = message_idd

                        # плашка
                        try:
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
                        except Exception as e:
                            logging.error(f"Ошибка при обновлении изображения после голосования: {e}: {traceback.format_exc()}")

        # with message_list_lock:
        try:
            if game_code in voted_players:
                flag_vse_progolos[game_code] = len(active_games[game_code]['players']) == len(
                    voted_players[game_code])
            else:
                flag_vse_progolos[game_code] = False
        except Exception as e:
            logging.error(f"Ошибка при проверке всех голосов для игры {game_code}: {e}")

        players = active_games[game_code]['players']
        if flag_vse_progolos[game_code]:
            try:
                # can_vote[game_code] = False
                del voted_players[game_code]

                try:  # удаляем таймер
                    bot.edit_message_text(chat_id=player_id,
                                          message_id=message_ids_timer_send_votes_after_sending[game_code][
                                              player_id],
                                          text=f"Твой голос учтён!", parse_mode="HTML")
                except:
                    pass

                send_message_to_players(game_code, "Все игроки проголосовали! А вот и рейтинг мемолюбов:")

                # удалить таймер
                try:
                    for pl_id in players:
                        bot.delete_message(pl_id, message_ids_timer_send_votes_after_sending[game_code][pl_id])
                        # message = bot.send_message(pl_id,
                        #                            "Среди нас халявщики, которые не успели отправить мем. Голосуем за самых быстрых!")
                        # message_ids_timer_send_votes[game_code][pl_id] = message.message_id
                except:
                    pass

                progolosoval_prt_2(game_code, kolvo_buttons, photos_per_row, kolvo_empty)
            except Exception as e:
                logging.error(f"Ошибка при завершении голосования для игры {game_code}: {e}")

    except Exception as e:
        logging.error(f"Ошибка в процессе голосования для игры {game_code}: {e}: {traceback.format_exc()}")





def progolosoval_prt_2(game_code, kolvo_buttons, photos_per_row, kolvo_empty):
    # всем каpтинам присваиваем 0 голосов
    try:
        stop_waiting_golosov[game_code] = True
        for card in cards_on_table[game_code]['photos_on_table'][1:-1]:
            card.append(0)

        for numb_za in voted_battle_cards[game_code].values():  # получаем все номера картин, за которые проголосовали
            cards_on_table[game_code]['photos_on_table'][numb_za][2] += 1  # если не голос
    except Exception as e:
        logging.error(f"Ошибка при подсчете голосов для игры {game_code}: {e}")
        return

    try:
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
    except Exception as e:
        logging.error(f"Ошибка при создании кнопок голосования для игры {game_code}: {e}")
        return

    # финальное фото
    try:
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
        # x = 232
        x = 220
        x_initial = x
        # y = 675 #new
        # y = 665 #old
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
                    # x = 232
                    x = 220
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
    except Exception as e:
        logging.error(f"Ошибка при создании финального изображения для игры {game_code}: {e}")
        return

    # обновление у всех
    try:
        players = active_games[game_code]['players']
        for pl_id in players:
            combined_image_io = copy.deepcopy(resized_com_star)
            # with message_list_lock:
            messag_id = golosov_mes_ids[game_code][pl_id]
            # messag_id = int(messages_ids[game_code][pl_id])
            if messag_id is not None:
                # bot.send_photo(pl_id, combined_image_io)
                bot.edit_message_media(
                    chat_id=pl_id,
                    message_id=messag_id,
                    media=types.InputMediaPhoto(combined_image_io),
                    reply_markup=markup
                )
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщений с результатами голосования для игры {game_code}: {e}")
        return

    # сортируем по убыванию и выводим общий рейтинг
    try:
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
    except Exception as e:
        logging.error(f"Ошибка при отправке рейтинга игрокам для игры {game_code}: {e}")
        return

    # if game_code in flag_pl_otpravil:
    #     del flag_pl_otpravil[game_code]

    # новый раунд
    # try:
    #     delete_stuff_for_next_round(game_code)
    # except Exception as e:
    #     logging.error(f"Ошибка при подготовке к новому раунду для игры {game_code}: {e}")


    try:
        # time.sleep(3)
        players_hand_cards(game_code)
    except Exception as e:
        logging.error(f"Ошибка при старте нового раунда для игры {game_code}: {e}\n{traceback.format_exc()}")


golosov_mes_ids = {}  # словарь со всеми id стола для замены потом на результаты


# callback для table
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('choose:'))
def choose_callback_handler(callback_query):
    try:
        data = callback_query.data.split(':')
        player_id = callback_query.message.chat.id
        game_code = data[1]
        additional_parameter = data[2]
        photos_per_row = int(data[3])
        kolvo_empty = int(data[4])
        message_idd = callback_query.message.message_id
    except Exception as e:
        logging.error(f"Ошибка при обработке данных в choose_callback_handler для игры {game_code}: {e}")
        return
    try:
        if additional_parameter.isdigit():  # число
            button_number = int(additional_parameter) + 1  # тк 0 карта-ситуация
            # второй раз нажать на ту же кнопку
            mozno_li_nazat = True
            if battle_cards[game_code][player_id] == button_number:
                mozno_li_nazat = False
            else:
                battle_cards[game_code][player_id] = button_number  # чел выбрал эту карту
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
                    cur = cards_on_table[game_code]['photos_on_table'][i + 1][0]

                    if cur == player_id:
                        if i + 1 == numb_za_kot_progolos:
                            button_text = "твой👆"
                        else:
                            button_text = "твой"
                    elif i + 1 == numb_za_kot_progolos:
                        button_text = f"{i + 1}👆"
                    else:
                        button_text = str(i + 1)

                    # button_text = "твой мем" if cur == player_id else str(i+1)

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
                try:
                    blank_com = Image.open(io.BytesIO(blank_table[game_code]))
                    x = blank_com.width // 4 * (button_number - 1)
                    if len(buttons) == 4:
                        y = blank_com.height - 16
                    elif button_number <= 4:
                        y = 4 * blank_com.height // 5 - 28
                    else:
                        y = blank_com.height - 28
                        x = blank_com.width // 4 * (button_number - 4 - 1)

                    whole_picture = add_mem_plashka(game_code, numb_za_kot_progolos - 1, (x, y))
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
                except Exception as e:
                    logging.error(
                        f"Ошибка при обновлении изображения в choose_callback_handler для игры {game_code}: {e}")
        # elif additional_parameter == 'zero': # Обработка запроса для пустых кнопок
        # send_message_to_players(game_code, "zer")

        elif additional_parameter == 'vote':
            # print('here')
            try:
                num_buttons = len(cards_on_table[game_code]['photos_on_table']) - 2
                progolosoval(player_id, game_code, photos_per_row, kolvo_empty, message_idd, num_buttons)
            except Exception as e:
                logging.error(f"Ошибка при голосовании в choose_callback_handler для игры {e}: {traceback}")
    except Exception as e:
        logging.error(f"Ошибка в обработчике choose_callback_handler: {e}")


def situation_plus_bar_blank(game_code):
    # cards_on_table[game_code]['photos_on_table']
    try:
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
    except Exception as e:
        logging.error(f"Ошибка при создании изображения situation_plus_bar_blank для игры {game_code}: {e}")
        return None


def add_mem_plashka(game_code, number, position):  # от 0
    try:
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
    except Exception as e:
        logging.error(f"Ошибка при создании мем-изображения add_mem_plashka для игры {game_code}: {e}")
        return None


stop_waiting_meme_chose = {}
stop_waiting_golosov = {}


# разыгровка карт
def table(player_id, game_code):
    try:
        battle_cards[game_code] = {}
        voted_battle_cards[game_code] = {}
        stop_waiting_meme_chose[game_code] = True
        stop_waiting_golosov[game_code] = False

        players = active_games[game_code]['players']
        active_players = players_order[game_code]

        # добавляем рандомные фотки
        #bot.send_message(player_id, f"кол-во игроков {len(active_players)}")
        if len(active_players) < 4:
            if players_hand[game_code]['round'] == 1:
                send_message_to_players(game_code,
                                        "У вас меньше 4 игроков, поэтому с вами играет бот! Попробуйте его обыграть ахах 😈")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                features = {}
                big_images_bynumb = OrderedDict()
                cards_links = []
                # for i in range (8 - len(players)):
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
        try:
            rest_of_list = cards_on_table[game_code]['photos_on_table'][1:].copy()
            random.shuffle(rest_of_list)
            cards_on_table[game_code]['photos_on_table'][1:] = rest_of_list
        except Exception as e:
            logging.error(f"Ошибка при перемешивании карт в table для игры {game_code}: {e}")

        situation_card = cards_on_table[game_code]['photos_on_table'][0]
        # перемешиваем все мемы. на 0 месте остаётся ситуация

        # переделываем склейку, делаем blank ситуация + бар
        '''# верхняя часть стола, первоначальная позциия
        top_pic = left_plus_right(game_code, BytesIO(situation_card),
                                  BytesIO(cards_on_table[game_code]['photos_on_table'][1][1]))
    '''
        memes = []
        try:
            for mem in cards_on_table[game_code]['photos_on_table'][1:]:  # берем все кроме 0, тк 0 - ситуация
                memes.append(mem[1])
                # работает

            low_pic = all_cards_on_the_table(game_code, memes)

            # добавляем бар ко всем картам (ситуация, карты, бар)
            cards_on_table[game_code]['photos_on_table'].append(low_pic.getvalue())

            # генерим склейку
            blank = situation_plus_bar_blank(game_code)

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
        except Exception as e:
            logging.error(f"Ошибка при подготовке изображения и плашки в table для игры {game_code}: {e}")

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
                        if i + 1 == numb_za_kot_progolos:
                            button_text = "твой👆"
                        else:
                            button_text = "твой"
                    elif i + 1 == numb_za_kot_progolos:
                        button_text = f"{i + 1}👆"
                    else:
                        button_text = str(i + 1)
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
            for empty in range(kolvo_empty):
                buttons.append(types.InlineKeyboardButton(" ", callback_data=callback_zero))

            markup = types.InlineKeyboardMarkup(row_width=photos_per_row)
            send_meme_button = types.InlineKeyboardButton("Проголосовать за выбранный мем",
                                                          callback_data=callback_vote_for_this)
            markup.add(*buttons)
            markup.add(send_meme_button)

            try:
                picture = copy.deepcopy(resized_whole_picture)
                all_combined_images[game_code].append(picture)
                # print(f"lenn all_combined_images[game_code]: {len(all_combined_images[game_code])}")
                message = bot.send_photo(chat_id=cur_player, photo=picture, reply_markup=markup)
                golosov_mes_ids[game_code][cur_player] = message.message_id
            except Exception as e:
                logging.error(f"Ошибка при отправке изображения игроку {cur_player} в table для игры {game_code}: {e}")

            # Устанавливаем таймер на удаление сообщения через 5 секунд
            if cur_player == players[-1]:  # последний игрок
                # time.sleep(10)
                try:
                    wait_thread = threading.Thread(target=wait_and_check_golosov(game_code))
                    # wait_thread.start()
                    # wait_thread.join()
                    if (game_code not in voted_players or len(voted_players[game_code]) == 0) and not stop_waiting_golosov[
                        game_code]:
                        for pl in players:

                            # send_message_to_players(game_code, "Все игроки проголосовали! А вот и рейтинг мемолюбов:")
                            #
                            # # удалить таймер
                            # try:
                            #     for pl_id in players:
                            #         bot.delete_message(pl_id,
                            #                            message_ids_timer_send_votes_after_sending[game_code][pl_id])
                            #         # message = bot.send_message(pl_id,
                            #         #                            "Среди нас халявщики, которые не успели отправить мем. Голосуем за самых быстрых!")
                            #         # message_ids_timer_send_votes[game_code][pl_id] = message.message_id
                            # except:
                            #     pass
                            try: #удаляем сообщение с таймером
                                bot.delete_message(pl, message_ids_timer_send_votes[game_code][pl])
                            except:
                                pass

                            try:

                                bot.edit_message_text(chat_id=player_id,
                                                      message_id=
                                                      message_ids_timer_send_votes_after_sending[game_code][
                                                          player_id],
                                                      text=f"Твой голос учтён!", parse_mode="HTML")
                            except:
                                pass

                        send_message_to_players(game_code, "Все уснули и никто не проголосовал, завершаем игру, но можно начать новую!")
                        # перевести на главное меню и дропнуть игру
                        a_nu_ka_main_menu_all(game_code)
                        try:
                            delete_stuff_for_repeat(game_code)
                            delete_rest_stuff(game_code)
                        except Exception as e:
                            logging.error(f"Ошибка при завершении игры, когда не голосовали {game_code}: {e}")


                    # проголосовали не все
                    elif not stop_waiting_golosov[game_code] and len(active_games[game_code]['players']) != len(
                            voted_players[game_code]):

                        # сообщение
                        for player_id in active_games[game_code]['players']:
                            if player_id not in voted_players[game_code]:
                                try:
                                    bot.send_message(player_id, "Ты не успел проголосовать :(")
                                except:
                                    pass

                            try:
                                bot.edit_message_text(chat_id=player_id,
                                                      message_id=message_ids_timer_send_votes[game_code][player_id],
                                                      text=f"Среди нас халявщики, которые не успели отправить мем. Голосуем за самых быстрых! ",
                                                      parse_mode="HTML")
                            except:
                                pass

                            # if player_id not in voted_players[game_code]:
                            #     players = active_games[game_code]['players']
                            #     for pl in players:
                            #         try:
                            #             bot.edit_message_text(chat_id=pl,
                            #                                   message_id=
                            #                                   message_ids_timer_send_memes_after_sending[game_code][
                            #                                       pl], text="Ты отправил этот мем.")
                            #         except Exception as e:
                            #             logging.error(
                            #                 f"Ошибка при удалении сообщения в Ваш мем отправлен. для игры {game_code}: {e}")

                                # bot.send_message(player_id, "Ты не успел проголосовать :(")



                            else: # вкинул
                                try:

                                    bot.edit_message_text(chat_id=player_id,
                                                          message_id=
                                                          message_ids_timer_send_votes_after_sending[game_code][
                                                              player_id],
                                                          text=f"Твой голос учтён!", parse_mode="HTML")
                                except:
                                    pass



                        del voted_players[game_code]

                        kolvo_buttons = len(cards_on_table[game_code]['photos_on_table']) - 2

                        flag_pl_otpravil[game_code] = []
                        kolvo_players_that_send_mem[game_code] = 0
                        if game_code in message_ids_timer_send_memes_after_sending:
                            del message_ids_timer_send_memes_after_sending[game_code]
                        if game_code in message_ids_timer_send_memes:
                            del message_ids_timer_send_memes[game_code]
                        if game_code in message_ids_timer_send_votes:
                            del message_ids_timer_send_votes[game_code]
                        if game_code in message_ids_timer_send_votes_after_sending:
                            del message_ids_timer_send_votes_after_sending[game_code]

                        progolosoval_prt_2(game_code, kolvo_buttons, photos_per_row, kolvo_empty)
                except Exception as e:
                    logging.error(f"Ошибка в процессе ожидания голосов в table для игры {game_code}: {e}:{traceback.format_exc()}")
        # перенесла далеко, чтобы было только 1 нажатие на мем карту (Все игроки отправили мемы)
        flag_pl_otpravil[game_code] = []
        if game_code in message_ids_timer_send_memes_after_sending:
            del message_ids_timer_send_memes_after_sending[game_code]
        if game_code in message_ids_timer_send_memes:
            del message_ids_timer_send_memes[game_code]
        if game_code in message_ids_timer_send_votes:
            del message_ids_timer_send_votes[game_code]
        if game_code in message_ids_timer_send_votes_after_sending:
            del message_ids_timer_send_votes_after_sending[game_code]
        # print("очистили flag_pl_otpravil")
        kolvo_players_that_send_mem[game_code] = 0
    except Exception as e:
        logging.error(f"Ошибка в table: {e}")

# Функция для удаления отредактированного сообщения
nothing_to_send_back_for_mem = {}

# Обработчик callback-запроса
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('combine:'))
def combine_callback_handler(callback_query):
    try:
        data = callback_query.data.split(':')
        player_id = callback_query.message.chat.id
        game_code = data[1]
        additional_parameter = data[2]

        bar = BytesIO(photo_bar_players[game_code][player_id][5])  # bar
        big_photo = BytesIO()
        button_1 = "1"
        button_2 = "2"
        button_3 = "3"
        button_4 = "4"
        button_5 = "5"

        if additional_parameter == "send_meme_button":  # игрок хочет отправить мем в игру
            if game_code not in flag_pl_otpravil and nothing_to_send_back_for_mem[game_code]:
                flag_pl_otpravil[game_code] = []
            if player_id in flag_pl_otpravil[game_code] and nothing_to_send_back_for_mem[game_code]:
                bot.send_message(player_id, "Ты уже отправил свой мем! Немного подожди:)")
            elif nothing_to_send_back_for_mem[game_code]:
                flag_pl_otpravil[game_code].append(player_id)

                try:  # удаляем таймер
                    bot.delete_message(player_id, message_ids_timer_send_memes[game_code][player_id])
                except Exception as e:
                    logging.error(
                        f"Ошибка при удалении сообщения в combine_callback_handler для игры {game_code}: {e}")

                # присылаем новый таймер

                if game_code not in message_ids_timer_send_memes_after_sending:
                    message_ids_timer_send_memes_after_sending[game_code] = {}

                message = bot.send_message(player_id, "Ты отправил этот мем. Ждём других…")
                message_ids_timer_send_memes_after_sending[game_code][player_id] = message.message_id


                chosen_mem_number = cards_on_table[game_code][player_id]
                chosen_photo = BytesIO(photo_bar_players[game_code][player_id][chosen_mem_number])

                if game_code not in kolvo_players_that_send_mem or (
                        game_code in kolvo_players_that_send_mem and kolvo_players_that_send_mem[game_code] == 0):
                    kolvo_players_that_send_mem[game_code] = 1
                    players_order[game_code] = []
                else:
                    kolvo_players_that_send_mem[game_code] += 1

                bot.edit_message_media(chat_id=player_id, message_id=callback_query.message.message_id,
                                       media=types.InputMediaPhoto(chosen_photo))

                # Удаление мема из руки
                del players_hand[game_code][player_id][chosen_mem_number]
                del photo_bar_players[game_code][player_id][chosen_mem_number]
                photo_bar_players[game_code][player_id].pop()

                # Отправляем мем на стол
                cards_on_table[game_code]['photos_on_table'].append([player_id, chosen_photo.getvalue()])
                players_order[game_code].append(player_id)

                players = active_games[game_code]['players']
                if len(active_games[game_code]['players']) == kolvo_players_that_send_mem[game_code]:
                    nothing_to_send_back_for_mem[game_code] = False
                    try:  # удаляем таймер
                        bot.edit_message_text(chat_id=player_id,
                                              message_id=message_ids_timer_send_memes_after_sending[game_code][
                                                  player_id],
                                              text=f"Ты отправил этот мем", parse_mode="HTML")
                        # bot.delete_message(player_id, message_ids_timer_send_memes_after_sending[game_code][player_id])
                    except:
                        pass
                    if game_code not in message_ids_timer_send_votes:
                        message_ids_timer_send_votes[game_code] = {}
                    for player_id in players:
                        message = bot.send_message(player_id, "Все игроки отправили мемы. Выбери лучший!")
                        message_ids_timer_send_votes[game_code][player_id] = message.message_id
                    table(player_id, game_code)

        else:  # игрок пока выбирает мем
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

            if mozno_li_obnovlat:
                combined_image_io = top_plus_bottom(big_photo, bar)

                # Корректировка позиции плашки
                main_image = Image.open(big_photo)
                card_index = cards_on_table[game_code][player_id]


                x = card_index * (640// 5)

                if main_image.width < main_image.height:
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

                markup = types.InlineKeyboardMarkup(row_width=5)
                first_meme = types.InlineKeyboardButton(button_1, callback_data=callback_data_1)
                second_meme = types.InlineKeyboardButton(button_2, callback_data=callback_data_2)
                third_meme = types.InlineKeyboardButton(button_3, callback_data=callback_data_3)
                fourth_meme = types.InlineKeyboardButton(button_4, callback_data=callback_data_4)
                fifth_meme = types.InlineKeyboardButton(button_5, callback_data=callback_data_5)
                send_meme_button = types.InlineKeyboardButton("Отправить выбранный мем",
                                                              callback_data=callback_send_meme)
                markup.add(first_meme, second_meme, third_meme, fourth_meme, fifth_meme)
                markup.add(send_meme_button)

                bot.edit_message_media(
                    chat_id=player_id,
                    message_id=callback_query.message.message_id,
                    media=types.InputMediaPhoto(new_image),
                    reply_markup=markup
                )
    except Exception as e:
        logging.error(f"Ошибка при выборе мема в combine_callback_handler для игры {game_code}: {e}")


# карты на руках
# players_hand[game_code][player_id]


def download_big_photo(big_photo_link):
    try:
        image = Image.open(requests.get(big_photo_link, stream=True).raw)
        big_photo_io = io.BytesIO()  # скачиваем фотки большие
        image.save(big_photo_io, format='PNG')
        big_photo_io.seek(0)
        return big_photo_io
    except Exception as e:
        logging.error(f"Ошибка при загрузке большого фото: {e}")
        return None


def optimization_hand_cards(game_code, player_id):
    if game_code not in all_combined_images:
        all_combined_images[game_code] = []
    if game_code not in players_hand:
        players_hand[game_code] = {}

    '''#генерим все ссылки на все мемы. появляется deck_of_meme_cards, trash_memes
    generate_meme_links(game_code)'''

    # all_meme_links = [i for i in range(1, 251)]  # all numbers of memes
    '''if game_code not in chosen_memes:
        chosen_memes[game_code] = all_meme_links'''
    try:
        players_hand[game_code][player_id] = []
        if game_code not in photo_bar_players:
            photo_bar_players[game_code] = {}
        photo_bar_players[game_code][player_id] = []

        features = {}
        big_images_bynumb = OrderedDict()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for number in range(5):
                card_link = random_choice_of_link_meme(game_code)
                # card_number = 4
                players_hand[game_code][player_id].append(card_link)  # добавили номер

                try:
                    future = executor.submit(download_big_photo, card_link)
                    features[future] = card_link
                except Exception as e:
                    logging.error(f"Ошибка при загрузке изображения в optimization_hand_cards для игры {game_code}: {e}")

            # Дождитесь завершения всех загрузок больших фотографий
            for future in concurrent.futures.as_completed(features):
                try:
                    card_number = features[future]
                    result = future.result()
                    big_images_bynumb[card_number] = result
                except Exception as e:
                    logging.error(
                        f"Ошибка при обработке результатов загрузки изображений в optimization_hand_cards для игры {game_code}: {e}")

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

            # проверка на склейку 0
            # try:
            #     bot.send_message(player_id, "Твои карты на руках!")
            #     bot.send_photo(chat_id=player_id, photo=combined_image_io)
            # except Exception as e:
            #     logging.error(f"Ошибка при отправке изображения игроку в optimization_hand_cards для игры {game_code}: {e}")

            main_image = Image.open(initial_main_photo)
            x = 0
            if (main_image.width < main_image.height):  # вертикальная
                y = 640 - 2
            else:
                y = main_image.height + 461 // 5 - 2
            new_image = insert_image_to_main(combined_image_io, (x, y), 5)

        if game_code in all_combined_images:
            all_combined_images[game_code].append(new_image)
            # print(f"len 4 all_combined_images[game_code]: {len(all_combined_images[game_code])}")
        # else:
        #     all_combined_images[game_code] = [new_image]

    except Exception as e:
        logging.error(f"Ошибка в функции optimization_hand_cards для игры {game_code}: {e}")


def optimization_update_hands(player_id, game_code):
    global all_combined_images
    # у всех игроков пополняются руки до 5 карт

    # для теста
    try:
        features = {}
        big_images_bynumb = OrderedDict()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            try:
                card_link = random_choice_of_link_meme(game_code)
                # send_message_to_players(game_code, str(len(chosen_memes[game_code])))
                players_hand[game_code][player_id].append(card_link)  # добавили номер

                future = executor.submit(download_big_photo, card_link)
                features[future] = card_link
            except Exception as e:
                logging.error(f"Ошибка при добавлении карточки в optimization_update_hands для игры {game_code}: {e}")
                return

            # Дождитесь завершения всех загрузок больших фотографий
            try:
                for future in concurrent.futures.as_completed(features):
                    card_number = features[future]
                    result = future.result()
                    big_images_bynumb[card_number] = result
                photo_bar_players[game_code][player_id].append(
                    big_images_bynumb[players_hand[game_code][player_id][-1]].getvalue())
            except Exception as e:
                logging.error(
                    f"Ошибка при обработке результатов загрузки фото в optimization_update_hands для игры {game_code}: {e}")
                return
        try:
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

            # # проверка на склейку 1
            # try:
            #     # bot.send_message(player_id, "Ты получил новую карту!")
            #     # bot.send_photo(chat_id=player_id, photo=new_image)
            # except Exception as e:
            #     logging.error(f"Ошибка при отправке изображения игроку в optimization_update_hands для игры {game_code}: {e}")

            all_combined_images[game_code].append(new_image)
            # print(f"len 3 all_combined_images[game_code]: {len(all_combined_images[game_code])}")
        except Exception as e:
            logging.error(f"Ошибка при обновлении рук игроков в optimization_update_hands для игры {game_code}: {e}")
    except Exception as e:
        logging.error(f"Ошибка в функции optimization_update_hands для игры {game_code}: {e}")

def delete_stuff_for_next_round(game_code):
    if game_code in message_ids_timer_send_memes:
        del message_ids_timer_send_memes[game_code]

    if game_code in message_ids_timer_send_memes_after_sending:
        del message_ids_timer_send_memes_after_sending[game_code]

    if game_code in message_ids_timer_send_votes:
        del message_ids_timer_send_votes[game_code]

    if game_code in message_ids_timer_send_votes_after_sending:
        del message_ids_timer_send_votes_after_sending[game_code]

    if game_code in chosen_photos:
        del chosen_photos[game_code]

    if game_code in voted_players:
        del voted_players[game_code]

    if game_code in battle_cards:
        del battle_cards[game_code]

    if game_code in all_combined_images:
        del all_combined_images[game_code]

    if game_code in messages_ids:
        del messages_ids[game_code]

    if game_code in blank_table:
        del blank_table[game_code]

    if game_code in flag_pl_otpravil:
        del flag_pl_otpravil[game_code]

    if game_code in kolvo_players_that_send_mem:
        del kolvo_players_that_send_mem[game_code]

    if game_code in players_order:
        del players_order[game_code]

    if game_code in mozno_li_nazat_gotovo:
        del mozno_li_nazat_gotovo[game_code]

    if game_code in stop_waiting_meme_chose:
        del stop_waiting_meme_chose[game_code]

    if game_code in stop_waiting_golosov:
        del stop_waiting_golosov[game_code]

    if game_code in timer_hands:
        del timer_hands[game_code]

    if game_code in hands_mes_id:
        del hands_mes_id[game_code]

    if game_code in halavshik:
        del halavshik[game_code]


def delete_stuff_for_repeat(game_code):
    if game_code in active_games:
        for pl in active_games[game_code]['players']:
            try:
                del all_players_and_their_codes[pl]
            except Exception as e:
                logging.error(f"Ошибка при удалении игрока из all_players_and_their_codes: {e}")

        del active_games[game_code]

    if game_code in rating:
        del rating[game_code]


    if game_code in cards_on_table:
        del cards_on_table[game_code]


    if game_code in players_hand:
        del players_hand[game_code]



    # try:
    #     del now_obnov[game_code]
    # except KeyError as e:
    #     logging.error(f"Ошибка при удалении из now_obnov: {e}\n{traceback.format_exc()}")

    # try:
    #     del choose_the_duration_of_subscription_first_time[game_code]
    # except KeyError as e:
    #     logging.error(
    #         f"Ошибка при удалении из choose_the_duration_of_subscription_first_time: {e}\n{traceback.format_exc()}")


    if game_code in ids_3_gotovo:
        del ids_3_gotovo[game_code]

    if game_code in mozno_nazad_v_menu:
        del mozno_nazad_v_menu[game_code]
    # try:
    #     del flag_double_oplata[game_code]
    # except KeyError as e:
    #     logging.error(f"Ошибка при удалении из flag_double_oplata: {e}\n{traceback.format_exc()}")

    if game_code in photo_bar_players:
        del photo_bar_players[game_code]

    if game_code in message_list_of_players:
        del message_list_of_players[game_code]

    if game_code in ids_3_otmena:
        del ids_3_otmena[game_code]

    if game_code in voted_battle_cards:
        del voted_battle_cards[game_code]

    if game_code in golosov_mes_ids:
        del golosov_mes_ids[game_code]



    #     check
    if game_code in mozno_start_the_game:
        del mozno_start_the_game[game_code]

    if game_code in nothing_to_send_back_for_mem:
        del nothing_to_send_back_for_mem[game_code]

def delete_rest_stuff(game_code):

    if game_code in flag_vse_progolos:
        del flag_vse_progolos[game_code]
    try:
        if game_code in id_and_names:
            del id_and_names[game_code]
        if game_code in all_available_tarifs_memes:
            del all_available_tarifs_memes[game_code]
        if game_code in nazat_tarifs_memes:
            del nazat_tarifs_memes[game_code]
        if game_code in all_available_tarifs_sit:
            del all_available_tarifs_sit[game_code]
        if game_code in nazat_tarifs_sit:
            del nazat_tarifs_sit[game_code]
        if game_code in deck_of_sit_cards:
            del deck_of_sit_cards[game_code]
        if game_code in trash_sit:
            del trash_sit[game_code]
        if game_code in deck_of_meme_cards:
            del deck_of_meme_cards[game_code]
        if game_code in trash_memes:
            del trash_memes[game_code]

        if game_code in kolvo_naz_green_buttons:
            del kolvo_naz_green_buttons[game_code]

        if game_code in kolvo_naz_green_sit:
            del kolvo_naz_green_sit[game_code]

        if game_code in usernames:
            del usernames[game_code]

        if game_code in remember_players:
            del remember_players[game_code]

        if game_code in mozno_play_again:
            del mozno_play_again[game_code]


    except Exception as e:
        logging.error(f"Ошибка при удалении оставшихся данных для игры {game_code}: {e}")




# запонимнаем список игроков с прошлого раунда


# сыграть ещё раз
@bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('repeat:'))
def repeat(callback_query):
    global mozno_play_again
    data = callback_query.data.split(':')
    player_id = callback_query.from_user.id
    pl_name = callback_query.from_user.first_name
    game_code = data[1]

    try:
        # print(f"{len(mozno_play_again[game_code])}")
        # print(f"{mozno_play_again[game_code][player_id]}")
        if mozno_play_again[game_code][player_id]:
            mozno_play_again[game_code][player_id] = False

            # удаляем прошлое сообщение
            try:
                message_id = callback_query.message.message_id
                bot.delete_message(player_id, message_id)
            except Exception as e:
                logging.error(f"Ошибка при удалении сообщения в repeat для игры {game_code}: {e}")

            # проверка не началась ли ещё игра
            game_started = active_games[game_code].get('game_started', False)  # Проверка флага game_started
            if game_started:
                bot.send_message(player_id, f"Игра уже началась. Новые игроки не могут присоединиться.")
                a_nu_ka_main_menu(player_id)
            else: # игра не началась
                if game_code not in remember_players: # ещё не создавалсь, то есть запускает криэйтор
                    try:
                        remember_players[game_code] = copy.copy(active_games[game_code])

                        # стираем всю информацию
                        delete_stuff_for_next_round(game_code)
                        delete_stuff_for_repeat(game_code)

                        # Создаем новое состояние игры с текущим игроком как криэйтором
                        active_games[game_code] = {
                            'players': [player_id],
                            'usernames': [pl_name],
                            'creator': player_id,
                            'game_started': False  # Флаг для отслеживания статуса игры
                        }

                        if game_code not in id_and_names:
                            id_and_names[game_code] = {}
                        id_and_names[game_code][player_id] = pl_name

                        # Уведомляем игрока, что он стал криэйтором
                        message_1 = bot.send_message(player_id, f"Вы стали ведущим новой игры с кодом: {game_code}. Можете сообщить его другим игрокам или подождать, пока они нажмут на кнопку 'Сыграть ещё'")
                        message_id_1 = message_1.message_id

                        create_players_message(game_code, player_id)

                        markup = types.InlineKeyboardMarkup(row_width=2)
                        callback_data_start = f"start:{game_code}:{message_id_1}"

                        mozno_start_the_game[game_code] = True
                        start_game_button = types.InlineKeyboardButton("Начать игру", callback_data=callback_data_start)
                        callback_data_drop = f"drop:{game_code}:{message_id_1}:{0}"
                        mozno_nazad_v_menu[game_code] = True
                        drop_button = types.InlineKeyboardButton("Назад в меню", callback_data=callback_data_drop)
                        markup.add(start_game_button, drop_button)
                        bot.send_message(player_id, f'Когда все присоединятся, нажмите "Начать игру"', reply_markup=markup)

                        optimization_hand_cards(game_code, player_id)
                    except Exception as e:
                        logging.error(f"Ошибка при подготовке к повтору игры {game_code}: {e}")
                        return
                else:
                    try:
                        join_existing_game(player_id, str(pl_name), game_code)
                    except Exception as e:
                        logging.error(f"Ошибка при присоединении игрока к игре {game_code}: {e}")
    except Exception as e:
        logging.error(f"Ошибка в функции repeat для игры : {e}: {traceback.format_exc()}")

timer_hands = {}
hands_mes_id = {}  # лежат
import time
from telegram import Update
from telegram.ext import Updater, CallbackContext, CallbackQueryHandler


message_ids_timer_send_memes = {}
message_ids_timer_send_memes_after_sending = {}
message_ids_timer_send_votes = {}
message_ids_timer_send_votes_after_sending = {}
def wait_and_check_meme_chose(game_code):
    try:
        global stop_waiting_meme_chose
        global message_ids_timer_send_memes

        players = active_games[game_code]['players']

        for seconds_left in range(5, 0, -1):

            if stop_waiting_meme_chose[game_code]: # print("Waiting was interrupted.")
                return
            last_digit = seconds_left % 10
            if last_digit == 1:
                updated_message = f"Выбери свой мем! Осталось <b>{seconds_left}</b> секунда"
                updated_message_for_all = f"Ты отправил этот мем. Ждём других… <b>{seconds_left}</b> секунда"
            elif last_digit == 2 or last_digit == 3 or last_digit == 4:
                updated_message = f"Выбери свой мем! Осталось <b>{seconds_left}</b> секунды"
                updated_message_for_all = f"Ты отправил этот мем. Ждём других… <b>{seconds_left}</b> секунды"
            else:
                updated_message = f"Выбери свой мем! Осталось <b>{seconds_left}</b> секунд"
                updated_message_for_all = f"Ты отправил этот мем. Ждём других… <b>{seconds_left}</b> секунд"
            try:
                if len(active_games[game_code]['players']) == kolvo_players_that_send_mem[game_code]:
                    updated_message_for_all = f"Ты отправил этот мем"
            except:
                pass

            for player_id in players:
                try:
                    # личный таймер
                    # flag_pl_otpravil:{'520907': []}
                    # print(f"flag_pl_otpravil:{flag_pl_otpravil}")
                    if game_code in flag_pl_otpravil and player_id in flag_pl_otpravil[game_code]:
                        # print(f"player_id: {player_id} A: {message_ids_timer_send_memes_after_sending}")
                        bot.edit_message_text(chat_id=player_id, message_id=message_ids_timer_send_memes_after_sending[game_code][player_id], text=updated_message_for_all, parse_mode="HTML")
                    else:
                        # print(f"player_id: {player_id} B: {message_ids_timer_send_memes}")
                        bot.edit_message_text(chat_id=player_id, message_id=message_ids_timer_send_memes[game_code][player_id], text=updated_message, parse_mode="HTML")
                    # общий таймер
                except:
                    pass


            time.sleep(1)
    except:
        pass


def wait_and_check_golosov(game_code):
    try:
        global stop_waiting_golosov
        global message_ids_timer_send_votes

        players = active_games[game_code]['players']

        for seconds_left in range(8, 0, -1):
            if stop_waiting_golosov[game_code]:
                return
            last_digit = seconds_left % 10

            if last_digit == 1:
                updated_message = f"Все игроки отправили мемы. Выбери лучший! <b>{seconds_left}</b> секунда"
                updated_message_halavshik = f"Среди нас халявщики, которые не успели отправить мем. Голосуем за самых быстрых! <b>{seconds_left}</b> секунда"
                updated_message_for_all = f"Твой голос учтён! Ждём других… <b>{seconds_left}</b> секунда"
            elif last_digit == 2 or last_digit == 3 or last_digit == 4:
                updated_message = f"Все игроки отправили мемы. Выбери лучший! <b>{seconds_left}</b> секунды"
                updated_message_halavshik = f"Среди нас халявщики, которые не успели отправить мем. Голосуем за самых быстрых! <b>{seconds_left}</b> секунды"
                updated_message_for_all = f"Твой голос учтён! Ждём других… <b>{seconds_left}</b> секунды"
            else:
                updated_message = f"Все игроки отправили мемы. Выбери лучший! <b>{seconds_left}</b> секунд"
                updated_message_halavshik = f"Среди нас халявщики, которые не успели отправить мем. Голосуем за самых быстрых! <b>{seconds_left}</b> секунд"
                updated_message_for_all = f"Твой голос учтён! Ждём других… <b>{seconds_left}</b> секунд"


            for player_id in players:
                try:
                    # халявщики
                    if halavshik[game_code]:
                        bot.edit_message_text(chat_id=player_id, message_id=message_ids_timer_send_votes[game_code][player_id], text=updated_message_halavshik, parse_mode="HTML")
                    elif game_code in voted_players and len(active_games[game_code]['players']) == len(voted_players[game_code]):
                        bot.edit_message_text(chat_id=player_id,
                                              message_id=message_ids_timer_send_votes_after_sending[game_code][player_id],
                                              text=f"Твой голос учтён!", parse_mode="HTML")
                    # общий таймер, когда уже отправил голос
                    elif game_code in voted_players and player_id in voted_players[game_code]:
                        bot.edit_message_text(chat_id=player_id, message_id=message_ids_timer_send_votes_after_sending[game_code][player_id], text=updated_message_for_all, parse_mode="HTML")
                    else: # личный таймер
                        bot.edit_message_text(chat_id=player_id, message_id=message_ids_timer_send_votes[game_code][player_id], text=updated_message, parse_mode="HTML")

                except:
                    pass
            time.sleep(1)

    except:
        pass


def players_hand_cards(game_code):
    global all_combined_images
    global hands_mes_id
    global stop_waiting_meme_chose
    global mozno_play_again


    stop_waiting_meme_chose[game_code] = False
    if game_code not in players_hand:
        players_hand[game_code] = {}

    players = active_games[game_code]['players']

    # если не набран максимум очков
    # first_key, first_value = next(iter(rating[game_code].items()))

    # окончание игры
    # количество раундов с 2 на 5 поменять
    if game_code in players_hand and 'round' in players_hand[game_code] and players_hand[game_code]['round'] >= 5:
        # удаляем данные о таймерах
        flag_pl_otpravil[game_code] = []
        if game_code in message_ids_timer_send_memes_after_sending:
            del message_ids_timer_send_memes_after_sending[game_code]
        if game_code in message_ids_timer_send_memes:
            del message_ids_timer_send_memes[game_code]
        if game_code in message_ids_timer_send_votes:
            del message_ids_timer_send_votes[game_code]
        if game_code in message_ids_timer_send_votes_after_sending:
            del message_ids_timer_send_votes_after_sending[game_code]

        try:
            max_score = max(rating[game_code].values())  # находим максимальное количество очков
            winners = [pl_id for pl_id, score in rating[game_code].items() if
                       score == max_score]  # список всех победителей

            # Формируем строку с именами победителей
            if len(winners) > 1:
                winner_names = ', '.join(
                    [id_and_names[game_code][pl_id] if pl_id in id_and_names[game_code] else "bot" for pl_id in
                     winners])
                winner_message = f"Игра окончена. Победители: <b>{winner_names}</b>! 🎉"
            else:
                winner_name = id_and_names[game_code][winners[0]] if winners[0] in id_and_names[game_code] else "bot"
                winner_message = f"Игра окончена, Победитель: <b>{winner_name}</b>! 🎉"

            #
            # if first_key in id_and_names[game_code]:
            #     pl_name = id_and_names[game_code][first_key]
            # else:
            #     pl_name = "bot"
            # делаем игру неактивной
            active_games[game_code]['game_started'] = False

            for player_id in players:
                bot.send_message(player_id, winner_message, parse_mode="HTML")


            # предложение сыграть ещё

            markup = types.InlineKeyboardMarkup(row_width=2)
            callback_data_repeat = f"repeat:{game_code}"
            callback_data_leave = f"menu:{game_code}"
            repeat_the_game = types.InlineKeyboardButton("Сыграть ещё", callback_data=callback_data_repeat)
            leave_the_game = types.InlineKeyboardButton("Выйти из игры", callback_data=callback_data_leave)
            markup.add(repeat_the_game, leave_the_game)
            mozno_play_again[game_code] = {}
            for player_id in players:
                mozno_play_again[game_code][player_id] = True
                bot.send_message(player_id, text="Ещё партеечку? 😏", reply_markup=markup)
        except Exception as e:
            logging.error(f"Ошибка при завершении игры {game_code}: {e}: {traceback.format_exc()}")

    else:
        if players_hand.get(game_code, {}).get('round'):  # новый раунд
            # генерация рук и down time
            for player_id in players:
                try:
                    optimization_update_hands(player_id, game_code)
                except Exception as e:
                    logging.error(f"Ошибка при обновлении рук игрока {player_id} для игры {game_code}: {e}")



            flag_vse_progolos[game_code] = False
            players_hand[game_code]['round'] += 1  # счётчик раундов
            for pl in players:
                bot.send_message(pl, f"<b>Раунд {players_hand[game_code]['round']} из 5</b>", parse_mode="HTML")
            # time.sleep(2)
            # send_message_to_players(game_code, f"{players_hand[game_code]['round']} раунд")
            send_situation(game_code)

            # запоминаем id чтобы потом удалить
            players = active_games[game_code]['players']
            # отправляем сообщение выбери свой мем

            # таймер
            if game_code not in message_ids_timer_send_memes:
                message_ids_timer_send_memes[game_code] = {}
            for player_id in players:
                message = bot.send_message(player_id, "Выбери свой мем!")
                message_ids_timer_send_memes[game_code][player_id] = message.message_id

            # в бар надо добавить элемент мем и бар(мини фотки)
        else:  # 1 раунд
            for pl in players:
                bot.send_message(pl, f"<b>Раунд 1 из 5</b>", parse_mode="HTML")
            # send_message_to_players(game_code, "1 раунд")
            send_situation(game_code)
            players = active_games[game_code]['players']

            # таймер
            if game_code not in message_ids_timer_send_memes:
                message_ids_timer_send_memes[game_code] = {}
            for player_id in players:
                message = bot.send_message(player_id, "Выбери свой мем!")
                message_ids_timer_send_memes[game_code][player_id] = message.message_id
            players_hand[game_code]['round'] = 1

        the_num_of_a_player = 0

        # ждать пока len(all_combined_images[game_code]) == len(players)
        start_time = time.time()
        if game_code in all_combined_images:
            while len(all_combined_images[game_code]) < len(players):
                # print(f"{len(all_combined_images[game_code])}")
                if time.time() - start_time > 20:
                    send_message_to_players(game_code, "Возникла ошибка. Попробуйте запустить игру ещё раз")

                    # перевести на главное меню и дропнуть игру
                    a_nu_ka_main_menu_all(game_code)

                    try:
                        delete_stuff_for_next_round(game_code)
                        delete_stuff_for_repeat(game_code)
                        delete_rest_stuff(game_code)
                    except Exception as e:
                        logging.error(f"Ошибка при завершении игры, когда не голосовали {game_code}: {e}")

                time.sleep(1)
            # print(f"{len(all_combined_images[game_code])}")



            # print(f"flag all_combined_images[game_code]: {len(all_combined_images[game_code])}")
            for player_id in players:
                # bot.send_message(player_id, str(all_combined_images[game_code].len()))
                combined_image_io = all_combined_images[game_code][the_num_of_a_player]
                the_num_of_a_player += 1
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

                # пока можно реагировть на отправку мема
                nothing_to_send_back_for_mem[game_code] = True

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

                # ошибка не в этом
                # if combined_image_io is None or combined_image_io.getbuffer().nbytes == 0:
                #     print("Ошибка: изображение пустое или не было загружено корректно")
                #     return

                try:
                    message = bot.send_photo(player_id, combined_image_io, reply_markup=markup)
                except Exception as e:
                    logging.error(f"Ошибка при отправке фото игроку {player_id} для игры {game_code}: {e}")
                    return

                # try:
                #     bot.send_photo(player_id, combined_image_io)
                # except Exception as e:
                #     logging.error(f"Ошибка даже если нет кнопок: {e}")
                #     return

                if game_code not in hands_mes_id:
                    hands_mes_id[game_code] = {}
                hands_mes_id[game_code][player_id] = message.message_id


                # Устанавливаем таймер на удаление сообщения через 5 секунд
                if player_id == players[-1]:  # последний игрок
                    # time.sleep(10)
                    wait_thread = threading.Thread(target=wait_and_check_meme_chose(game_code))
                    # wait_thread.start()
                    # wait_thread.join()
                    # если никто не выбрал мем
                    halavshik[game_code] = False
                    if (game_code not in flag_pl_otpravil and not stop_waiting_meme_chose[game_code]) or (kolvo_players_that_send_mem[game_code] == 0  and not stop_waiting_meme_chose[game_code]):

                        players = active_games[game_code]['players']
                        for pl in players:
                            try: # удаляем сообщение с таймером
                                bot.delete_message(pl, message_ids_timer_send_memes[game_code][pl])
                            except Exception as e:
                                logging.error(
                                    f"Ошибка при удалении сообщения в Никто не выбрал мем для игры {game_code}: {e}")

                        bot.delete_message(player_id, message.message_id)
                        send_message_to_players(game_code, "Никто не выбрал мем, поэтому игра завершилась. Можно начать новый тур!")
                        # перевести на главное меню и дропнуть игру
                        # if game_code in active_games and player_id == active_games[game_code]['creator']:

                        a_nu_ka_main_menu_all(game_code)

                        try:
                            delete_stuff_for_next_round(game_code)
                            delete_stuff_for_repeat(game_code)
                            delete_rest_stuff(game_code)
                        except Exception as e:
                            logging.error(f"Ошибка при удалении игры {game_code}: {e}")

                    elif len(active_games[game_code]['players']) != kolvo_players_that_send_mem[game_code] and not \
                    stop_waiting_meme_chose[game_code]:
                        flag_pl_otpravil[game_code] = []
                        kolvo_players_that_send_mem[game_code] = 0
                        halavshik[game_code] = True

                        for pl in players:
                            # если игрок не вкинул карту в иру
                            if pl not in players_order[game_code]:
                                # удаляем его руку с кнопками
                                bot.delete_message(chat_id=pl, message_id=hands_mes_id[game_code][pl])

                                try: # удаляем таймер
                                    bot.delete_message(pl, message_ids_timer_send_memes[game_code][pl])
                                except Exception as e:
                                    logging.error(
                                        f"Ошибка при удалении сообщения в combine_callback_handler для игры {game_code}: {e}")

                                bot.send_message(pl, "Ты не успел вкинуть свой мем в игру :(")
                            else:
                                try:
                                    bot.edit_message_text(chat_id=pl,
                                                      message_id=message_ids_timer_send_memes_after_sending[game_code][
                                                        pl], text="Ты отправил этот мем.")
                                except:
                                    pass
                        players = active_games[game_code]['players']
                        # send_message_to_players(game_code,
                        #                             "Среди нас халявщики, которые не успели отправить мем. Голосуем за самых быстрых!")
                        #
                        if game_code not in message_ids_timer_send_votes:
                            message_ids_timer_send_votes[game_code] = {}
                        for pl_id in players:
                            message = bot.send_message(pl_id, "Среди нас халявщики, которые не успели отправить мем. Голосуем за самых быстрых!")
                            message_ids_timer_send_votes[game_code][pl_id] = message.message_id

                        table(player_id, game_code)




# надо как-то сделать юот бесконечным, а то ун умирает через какое-то время, если его не использовать
bot.polling(none_stop=True, timeout=31536000)

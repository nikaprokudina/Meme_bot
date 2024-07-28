# from telebot import types
# from datetime import datetime, timedelta
# import database
# import telebot
# import telebot
# import random
# import string
# import math
# from telebot import types
# from io import BytesIO
# from PIL import Image
# import requests
# import concurrent.futures
# import io
# import threading
# # import sqlite3
# import bot
#
# from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
#
# from telebot import types
#
# def create_payment_keyboard():
#     keyboard = types.InlineKeyboardMarkup()
#     pay_button = types.InlineKeyboardButton(text="Оплатить 20 ⭐️", pay=True)
#     keyboard.add(pay_button)
#     return keyboard
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
#     if not bot.flag_double_oplata[game_code]:
#         bot.flag_double_oplata[game_code] = True
#         try:
#             bot.bot.delete_message(chat_id, bot.ids_3_otmena[game_code][2])  # вернуться к выбору карт
#         except:
#             pass
#
#         if game_code in bot.bot.flag_mes_oplat_id:
#             try:
#                 bot.bot.delete_message(chat_id, bot.bot.flag_mes_oplat_id[game_code])  # прошлая invoice
#             except:
#                 pass
#
#         bot.ids_3_otmena[game_code].pop(2)  # попаем вернуться к выбору
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
#         call_data = f"pay_mem:{game_code}"
#         markup = create_payment_keyboard()
#
#         bot.bot.send_invoice(
#             chat_id,
#             title=title_text,
#             description=descrip_text,
#             invoice_payload=call_data,
#             provider_token='',  # замените на ваш токен провайдера
#             currency='XTR',  # или другая валюта
#             prices=prices,
#             start_parameter='test',
#             reply_markup=markup
#         )
#
# @bot.bot.pre_checkout_query_handler(func=lambda query: True)
# def checkout(pre_checkout_query):
#     bot.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
#
# @bot.bot.message_handler(content_types=['successful_payment'])
# def got_payment(message):
#     payment_info = message.successful_payment.to_python()
#     game_code = payment_info['invoice_payload'].split(':')[1]
#     # Обработка успешной оплаты
#     bot.bot.send_message(message.chat.id, 'Оплата прошла успешно! Спасибо за покупку.')
#     # Тут можно добавить логику, например, добавление подписки в базу данных
#
#
#
# # def payment_keyboard():
# #     keyboard = InlineKeyboardMarkup()
# #     pay_button = InlineKeyboardButton(text="Оплатить 20 ⭐️", pay=True)
# #     keyboard.add(pay_button)
# #     return keyboard
# # # payment.py
# #
# # from telebot import types
# # from datetime import datetime, timedelta
# # from database import add_subscription
# #
# # all_names_of_tarifs = ['Демка', 'МЕМЫ: Весело и в точку!', 'МЕМЫ 2: СССР и 90-е', 'МЕМЫ 3: Котики и пр. нелюди', 'МЕМЫ НЕЙРО']
# # flag_mes_oplat_id = {}
# # all_available_tarifs_memes = {}
# # nazat_tarifs_memes = {}
# # kolvo_naz_green_buttons = {}
# # ids_3_otmena = {}
# #
# # def initiate_payment(bot, chat_id, button, game_code):
# #     start_payment(bot, chat_id, button, game_code)
# #
# # def start_payment(bot, chat_id, button, game_code):
# #     global all_names_of_tarifs
# #     days_text = 'день'
# #     days_number = 1
# #     price = 100
# #     name_of_cards = all_names_of_tarifs[button] if button != 1000 else 'Все наборы'
# #     prices = [types.LabeledPrice(label=f'{name_of_cards} на {days_text}', amount=price * 100)]
# #     descrip_text = f'💸 Приобрести "{name_of_cards}" на {days_text} 💸'
# #     title_text = f'Набор {name_of_cards}'
# #
# #     invoice_message = bot.send_invoice(
# #         chat_id,
# #         title=title_text,
# #         description=descrip_text,
# #         provider_token='YOUR_TELEGRAM_STARS_PROVIDER_TOKEN',
# #         currency='rub',
# #         prices=prices,
# #         start_parameter='start',
# #         invoice_payload=f'{chat_id} {chat_id} {button} {days_number}'
# #     )
# #     flag_mes_oplat_id[game_code] = invoice_message.message_id
# #
# #     call_data = f"pay_mem:{game_code}"
# #     markup = types.InlineKeyboardMarkup(row_width=1)
# #     chestno = types.InlineKeyboardButton(text="Вернуться к выбору карт для игры", callback_data=call_data)
# #     markup.row(chestno)
# #
# #     message_3 = bot.send_message(chat_id, text="Чтобы вернуться к выбору сетов, нажми на кнопку", reply_markup=markup)
# #     ids_3_otmena[game_code] = [invoice_message.message_id, message_3.message_id]
# #
# # @bot.message_handler(content_types=['successful_payment'])
# # def handle_successful_payment(message):
# #     chat_id = message.chat.id
# #     successful_payment_info_all = message.successful_payment
# #     useful_info_payment = (successful_payment_info_all.invoice_payload).split()
# #     player_id = int(useful_info_payment[0])
# #     player_nick = useful_info_payment[1]
# #     button = int(useful_info_payment[2])
# #     days = int(useful_info_payment[3])
# #
# #     current_datetime = datetime.now()
# #     if days == 1:
# #         expiration = current_datetime + timedelta(days=1)
# #     elif days == 30:
# #         expiration = current_datetime + timedelta(days=30)
# #     else:
# #         expiration = current_datetime + timedelta(days=365)
# #
# #     one_month_later_text = expiration.strftime("%d.%m.%Y %H:%M:%S")
# #     all_names_in_table = ['Демка', 'База', 'СССР', 'Котики', 'НЕЙРО']
# #     if button != 1000:
# #         text = all_names_in_table[button]
# #         add_subscription(player_id, player_nick, text, one_month_later_text)
# #     else:
# #         for text in all_names_in_table[1:]:
# #             add_subscription(player_id, player_nick, text, one_month_later_text)
# #
# #     bot.send_message(chat_id, 'Оплата прошла успешно!')
# #
# # @bot.pre_checkout_query_handler(func=lambda query: True)
# # def process_pre_checkout_query(pre_checkout_query):
# #     bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
# #
# #
# #
# # # bot = None
# # # all_names_of_tarifs = ['Демка', 'МЕМЫ: Весело и в точку!', 'МЕМЫ 2: СССР и 90-е', 'МЕМЫ 3: Котики и пр. нелюди', 'МЕМЫ НЕЙРО']
# # # flag_mes_oplat_id = {}
# # # all_available_tarifs_memes = {}
# # # nazat_tarifs_memes = {}
# # # kolvo_naz_green_buttons = {}
# # # ids_3_otmena = {}
# #
# # # def setup(bot_instance, available_tarifs_memes, nazat_tarifs, kolvo_naz, ids_otmena):
# # #     global bot, all_available_tarifs_memes, nazat_tarifs_memes, kolvo_naz_green_buttons, ids_3_otmena
# # #     bot = bot_instance
# # #     all_available_tarifs_memes = available_tarifs_memes
# # #     nazat_tarifs_memes = nazat_tarifs
# # #     kolvo_naz_green_buttons = kolvo_naz
# # #     ids_3_otmena = ids_otmena
# # #     add_handlers()
# # #
# # # def add_handlers():
# # #     @bot.message_handler(content_types=['successful_payment'])
# # #     def handle_successful_payment(message):
# # #         chat_id = message.chat.id
# # #         successful_payment_info_all = message.successful_payment
# # #         useful_info_payment = (successful_payment_info_all.invoice_payload).split()
# # #         player_id = int(useful_info_payment[0])
# # #         player_nick = useful_info_payment[1]
# # #         button = int(useful_info_payment[2])
# # #         days = int(useful_info_payment[3])
# # #
# # #         current_datetime = datetime.now()
# # #         if days == 1:
# # #             expiration = current_datetime + timedelta(days=1)
# # #         elif days == 30:
# # #             expiration = current_datetime + timedelta(days=30)
# # #         else:
# # #             expiration = current_datetime + timedelta(days=365)
# # #
# # #         one_month_later_text = expiration.strftime("%d.%m.%Y %H:%M:%S")
# # #         all_names_in_table = ['Демка', 'База', 'СССР', 'Котики', 'НЕЙРО']
# # #         if button != 1000:
# # #             text = all_names_in_table[button]
# # #             add_subscription(player_id, player_nick, text, one_month_later_text)
# # #         else:
# # #             for text in all_names_in_table[1:]:
# # #                 add_subscription(player_id, player_nick, text, one_month_later_text)
# # #
# # #         bot.send_message(chat_id, 'Оплата прошла успешно!')
# # #
# # #     @bot.pre_checkout_query_handler(func=lambda query: True)
# # #     def process_pre_checkout_query(pre_checkout_query):
# # #         bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
# # #
# # # def initiate_payment(bot, chat_id, button, game_code):
# # #     start_payment(chat_id, button, game_code)
# # #
# # # def start_payment(chat_id, button, game_code):
# # #     global all_names_of_tarifs
# # #     days_text = 'день'
# # #     days_number = 1
# # #     price = 100
# # #     name_of_cards = all_names_of_tarifs[button] if button != 1000 else 'Все наборы'
# # #     prices = [types.LabeledPrice(label=f'{name_of_cards} на {days_text}', amount=price * 100)]
# # #     descrip_text = f'💸 Приобрести "{name_of_cards}" на {days_text} 💸'
# # #     title_text = f'Набор {name_of_cards}'
# # #
# # #     invoice_message = bot.send_invoice(
# # #         chat_id,
# # #         title=title_text,
# # #         description=descrip_text,
# # #         provider_token='YOUR_TELEGRAM_STARS_PROVIDER_TOKEN',
# # #         currency='rub',
# # #         prices=prices,
# # #         start_parameter='start',
# # #         invoice_payload=f'{chat_id} {chat_id} {button} {days_number}'
# # #     )
# # #     flag_mes_oplat_id[game_code] = invoice_message.message_id
# # #
# # #     call_data = f"pay_mem:{game_code}"
# # #     markup = types.InlineKeyboardMarkup(row_width=1)
# # #     chestno = types.InlineKeyboardButton(text="Вернуться к выбору карт для игры", callback_data=call_data)
# # #     markup.row(chestno)
# # #
# # #     message_3 = bot.send_message(chat_id, text="Чтобы вернуться к выбору сетов, нажми на кнопку", reply_markup=markup)
# # #     ids_3_otmena[game_code] = [invoice_message.message_id, message_3.message_id]

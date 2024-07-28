
# @bot.callback_query_handler(func=lambda callback_query: callback_query.data.startswith('oplata:'))
# def oplata(callback_query):
#     data = callback_query.data.split(':')
#     game_code = data[5]
#     global all_names_of_tarifs
#     chat_id = callback_query.from_user.id
#     days_text = data[1]
#     days_number = data[2]  # 1, 30, 365
#     price = int(data[3])
#     price *= 100
#     button = int(data[4])
#
#     if not flag_double_oplata[game_code]:
#         flag_double_oplata[game_code] = True
#         try:
#             bot.delete_message(chat_id, ids_3_otmena[game_code][2])  # вернуться к выбору карт
#         except:
#             i = 0
#         if game_code in flag_mes_oplat_id:
#             try:
#                 bot.delete_message(chat_id, flag_mes_oplat_id[game_code])  # прошлая invoice
#             except:
#                 i = 0
#             # ids_3_otmena[game_code].pop(3) #попаем invoice
#         ids_3_otmena[game_code].pop(2)  # попаем вернуться к выбору
#
#         if button != 1000:
#             name_of_cards = all_names_of_tarifs[int(button)]
#             prices = [LabeledPrice(label=f'{name_of_cards} на 1 {days_text}', amount=price)]
#             descrip_text = f'💸 Приобрести "{name_of_cards}" на 1 {days_text} 💸'
#             title_text = f'Набор {name_of_cards}'
#
#         else:
#             prices = [LabeledPrice(label=f'Все наборы на 1 {days_text}', amount=price)]
#             descrip_text = f'💸 Приобрести ВСЕ наборы на 1 {days_text} 💸'
#             title_text = 'ВСЕ наборы'
#
#         call_data = f"pay_mem:{game_code}"
#         markup = types.InlineKeyboardMarkup(row_width=1)
#         mozno_obnovlat[game_code] = True
#         chestno = types.InlineKeyboardButton(text="Вернуться к выбору карт для игры", callback_data=call_data)
#         markup.row(chestno)
#
#         invoice_message = bot.send_invoice(
#             chat_id,
#             title=title_text,
#             description=descrip_text,
#             provider_token='381764678:TEST:66986',
#             currency='rub',
#             prices=prices,
#             start_parameter='start',
#             invoice_payload=f'{chat_id} {callback_query.from_user.username} {button} {days_number}'
#         )
#
#         flag_mes_oplat_id[game_code] = invoice_message.message_id
#
#         message_3 = bot.send_message(chat_id, text="Чтобы вернуться к выбору сетов, нажми на кнопку",
#                                      reply_markup=markup)
#         message_3_id = message_3.message_id
#
#         ids_3_otmena[game_code].append(message_3_id)  # вернуться
#         # ids_3_otmena[game_code].append(invoice_message.message_id) # invoce
#         flag_double_oplata[game_code] = False

#
# @bot.message_handler(content_types=['successful_payment'])
# def handle_successful_payment(message):
#     chat_id = message.chat.id
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
#         SQLFunc.add_subscription(player_id, player_nick, text, one_month_later_text)
#     else:
#         for text in all_names_in_table[1:]:
#             SQLFunc.add_subscription(player_id, player_nick, text, one_month_later_text)
#


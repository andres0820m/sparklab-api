import datetime
import json
import os
from json.decoder import JSONDecodeError

import telebot
from django.core.wsgi import get_wsgi_application
from django.forms.models import model_to_dict
from django.core.exceptions import ObjectDoesNotExist
from constants import STATUS_DATA, AUT_USER, P2P_DASHBOARD_BOT, ORDER_TEMPLATE
from utils import check_order_data

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = get_wsgi_application()
from orders.models import Order

bot = telebot.TeleBot(P2P_DASHBOARD_BOT)


@bot.message_handler(commands=['id'])
def send_welcome(message):
    print(message.from_user.id)
    bot.reply_to(message, str(message.from_user.id))


def init_message():
    bot.send_message(AUT_USER, 'running')


@bot.message_handler(commands=['order'])
def order_response(message):
    bot.send_message(message.chat.id, ORDER_TEMPLATE)


@bot.message_handler(commands=['order_id'])
def order_response(message):
    if message.from_user.id == AUT_USER:
        print('entre')
        args = message.text.split('/order_id')
        if len(args) == 2:
            try:
                order_id = int(args[-1])
                try:
                    order = Order.objects.get(binance_id=str(order_id))
                    order_dict = model_to_dict(order)
                    bot.send_message(message.chat.id, json.dumps(order_dict, indent=4))
                except ObjectDoesNotExist:
                    bot.send_message(message.chat.id, "el id no existe !!")
            except ValueError:
                bot.send_message(message.chat.id, "el id debe ser un numero entero !!")


@bot.message_handler(commands=['update'])
def order_response(message):
    if message.from_user.id == AUT_USER:
        args = message.text.split('/update')
        if len(args) == 2:
            data = args[-1]
            print(json.loads(data))
            try:
                data = json.loads(data)
                order_errors = check_order_data(data)
                if len(order_errors) == 0:
                    data["date"] = datetime.datetime.now()
                    data["status"] = 'created'
                    old_order = Order.objects.filter(binance_id=data['binance_id'])
                    if len(old_order) > 0:
                        old_order.update(**data)
                        bot.send_message(message.chat.id,
                                         "Orden {} actualizada correctamente en breve sera procesada".format(
                                             data['binance_id']))
                    else:
                        bot.send_message(message.chat.id, "el id no existe !!")

                else:
                    for error in order_errors:
                        bot.send_message(message.chat.id, error)
            except JSONDecodeError:
                bot.send_message(message.chat.id, "Upps, revisa el formato de los datos ingresados")


@bot.message_handler(commands=['orders'])
def order_response(message):
    hours = 3
    args = message.text.split('/orders')
    if len(args) == 2:
        try:
            hours = int(args[-1])
        except ValueError:
            pass
    time_threshold = datetime.datetime.now() - datetime.timedelta(hours=hours)
    orders = Order.objects.filter(date__gt=time_threshold)
    orders_data = '''Orders: \n'''
    for order in orders:
        print(order.date)
        orders_data = orders_data + "orden : {} status: {} \n".format(order.binance_id, STATUS_DATA[order.status])
    bot.send_message(message.chat.id, orders_data)


@bot.message_handler(func=lambda m: True)
def repeat(message):
    if message.from_user.id == AUT_USER:
        data = message.text
        try:
            data = json.loads(data)
            order_errors = check_order_data(data)
            if len(order_errors) == 0:
                new_order = Order(**data)
                new_order.save()
                print(Order.objects.all())
                bot.send_message(message.chat.id,
                                 "Orden {} creada correctamente en breve sera procesada".format(data['binance_id']))
            else:
                for error in order_errors:
                    bot.send_message(message.chat.id, error)
        except JSONDecodeError:
            bot.send_message(message.chat.id, "Upps, revisa el formato de los datos ingresados")
    else:
        bot.send_message(message.chat.id, "Usuario NO PERMITIDO !!!")
        bot.send_message(AUT_USER, "alguien intento crear una orden !!")


init_message()
bot.infinity_polling(timeout=10)

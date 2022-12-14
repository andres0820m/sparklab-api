import datetime
import json

from colorama import Fore
from termcolor import colored

from binance_wrapped import BinanceInfoGetter
from constants import MAPPED_BANKS_FOR_API, MAPPED_ORDER_KEY, ORDER_TEMPLATE, AUT_USER, \
    MAX_TIME_TO_CREATED_ORDER_SECONDS
from utils import mapped_dict_from_data
from tools import str_only_numbers


class BinanceListener(BinanceInfoGetter):

    @staticmethod
    def __get_type_of_document(number):
        id_len = len(number)
        if id_len == 10 and number[0] == '5':
            return 'pasaporte'
        else:
            if len(number) == 6:
                return 'cc_ext'
        return 'cc'

    def wws_on_message(self, ws, message):
        data = json.loads(message)
        binance_id = data['orderNo']
        status = self.order_wrapped.get_order(binance_id=binance_id).status_code
        print(Fore.GREEN + str(status))
        if status == 404:
            order = self.get_order_info(binance_id=binance_id)['data']
            order_date = order['createTime']
            order_date = datetime.datetime.fromtimestamp(order_date / 1000)
            if (datetime.datetime.now() - order_date).total_seconds() < MAX_TIME_TO_CREATED_ORDER_SECONDS:
                acc_dict = ORDER_TEMPLATE.copy()
                acc_dict['binance_id'] = str(order['orderNumber'])
                bank = MAPPED_BANKS_FOR_API[order['payType']]
                order_bank = self.order_wrapped.get_bank(bank='bancolombia')
                acc_dict['bank'] = order_bank
                acc_dict['amount'] = str(int(float(order['totalPrice'])))
                acc_dict['usdt_price'] = order['price']
                acc_dict['pay_id'] = order['payMethods'][0]['id']
                mapped_dict_from_data(acc_dict=acc_dict, data=order['payMethods'][0]['fields'], bank=bank)
                if acc_dict['id_number']:
                    order_document = self.order_wrapped.get_document(
                        document=self.__get_type_of_document(acc_dict['id_number']))
                else:
                    order_document = self.order_wrapped.get_document('cc')
                acc_dict['document_type'] = order_document
                try:
                    order_account_type = self.order_wrapped.get_account(account=acc_dict['account_type'])
                except:
                    order_account_type = self.order_wrapped.get_account(account='Ahorros')
                acc_dict['account_type'] = order_account_type
                order_data = dict((MAPPED_ORDER_KEY[key], value) for (key, value) in acc_dict.items())
                user = self.order_wrapped.get_user()
                order_data['user'] = user
                order_data = self.check_accounts_data(order_data)
                response = self.order_wrapped.create_order(order_data)
                if response.status_code > 201:
                    self.telegram_bot.send_message(chat_id=AUT_USER,
                                                   text="order {} could not be created !!".format(
                                                       order_data['binance_id']))
                else:
                    if order_data['status'] == 'created':
                        self.telegram_bot.send_message(chat_id=AUT_USER,
                                                       text="order {} is running :3".format(order_data['binance_id']))
                    else:
                        self.telegram_bot.send_message(chat_id=AUT_USER,
                                                       text='the order {} was created but need revision'.format(
                                                           order_data['binance_id']))
                print(Fore.GREEN + "order with id:{} was created".format(binance_id))

    def wws_on_error(self, ws, error):
        print(error)

    def wws_on_open(self, ws):
        print(Fore.GREEN + "connected")

    def wws_on_close(self, ws, close_status_code, close_msg):
        print(colored("### closed ###", 'green'))

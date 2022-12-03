import datetime
import json
import os

import requests
from termcolor import colored
from colorama import Fore

from binance_wrapped import BinanceInfoGetter
from constants import ORDERS_URL, MAPPED_BANKS_FOR_API, MAPPED_ORDER_KEY
from utils import mapped_dict_from_data


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
        print(Fore.GREEN + str(self.get_order_info(binance_id=binance_id)['data']))
        status = requests.get(ORDERS_URL.format(binance_id)).status_code
        print(Fore.GREEN + str(status))
        if status == 404:
            order = self.get_order_info(binance_id=binance_id)['data']
            acc_dict = dict()
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
            order_data['status'] = 'waiting_for_review'
            self.order_wrapped.create_order(order_data)
            print(Fore.GREEN + "order with id:{} was created".format(binance_id))

    def wws_on_error(self, ws, error):
        print(error)

    def wws_on_open(self, ws):
        print(Fore.GREEN + "connected")

    def wws_on_close(self, ws, close_status_code, close_msg):
        print(colored("### closed ###", 'green'))

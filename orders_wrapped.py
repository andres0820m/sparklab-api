import os
import requests
from requests.exceptions import ConnectTimeout

from django.forms.models import model_to_dict
from django.core.wsgi import get_wsgi_application
from constants import API_HEADERS, MAIN_URL
from Errors import ApiConnectionError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = get_wsgi_application()
from orders.models import Order


class OrderWrapped:
    def __init__(self):
        self._headers = API_HEADERS

    def __send_request(self, method, url, params={}, json_data={}, retry=3, timeout=5):
        while retry != 0:
            try:
                data = requests.request(method=method, url=url, timeout=timeout, json=json_data, params=params,
                                        headers=self._headers)
                return data
            except ConnectTimeout:
                retry -= 1
        raise ApiConnectionError

    def check_account(self, account_number):
        url = MAIN_URL.format('check_account/')
        json_data = {"account": account_number}
        data = self.__send_request(method="GET", url=url, json_data=json_data)
        return data

    def set_subscribe(self, binance_id):
        url = MAIN_URL.format('check_account/')
        json_data = {"binance_id": binance_id}
        data = self.__send_request(method="POST", url=url, json_data=json_data)
        return data

    def get_orders(self):
        url = MAIN_URL.format('potential_orders/')
        data = self.__send_request(method='GET', url=url)
        orders = []
        for order in data.json():
            orders.append(Order(**order))
        return orders

    def update_order(self, order: Order):
        binance_id = order.binance_id
        url = MAIN_URL.format('orders/' + binance_id + '/')
        json_data = model_to_dict(order)
        data = self.__send_request(method="PUT", url=url, json_data=json_data)
        return data

    def get_bank(self, bank):
        url = MAIN_URL.format('get_bank/')
        json_data = {"bank": bank}
        data = self.__send_request(method='GET', url=url, json_data=json_data).json()
        return data['id']

    def get_account(self, account):
        url = MAIN_URL.format('get_account/')
        json_data = {"account": account}
        data = self.__send_request(method='GET', url=url, json_data=json_data).json()
        return data['id']

    def get_document(self, document):
        url = MAIN_URL.format('get_document/')
        json_data = {"document": document}
        data = self.__send_request(method='GET', url=url, json_data=json_data).json()
        return data['id']

    def create_order(self, order):
        print(order)
        url = MAIN_URL.format('orders/')
        print(self.__send_request(method='POST', url=url, json_data=order))

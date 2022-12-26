import os
import requests
from requests.exceptions import ConnectTimeout, ConnectionError, ReadTimeout

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
        data = self.__login()
        self.__token = data['access']
        self.__refresh = data['refresh']

    def __refresh_token(self):
        refresh_url = MAIN_URL.format('api/token/refresh/')
        json_data = {"refresh": self.__refresh}
        data = self.__send_request(method='POST', url=refresh_url, json_data=json_data)
        if data.status_code == 401:
            self.__login()
        else:
            data = data.json()
            self.__token = data['access']

    def __login(self):
        url = MAIN_URL.format('api/token/')
        json_data = {"username": os.environ['api_username'], "password": os.environ['api_password']}
        data = self.__send_request(method="POST", url=url, json_data=json_data, use_auth=False)
        return data.json()

    def __send_request(self, method, url, params={}, json_data={}, retry=3, timeout=5, use_auth=True):
        continue_request = False
        while retry != 0:
            try:
                while not continue_request:
                    if use_auth:
                        self._headers['Authorization'] = 'Bearer {}'.format(self.__token)
                    data = requests.request(method=method, url=url, timeout=timeout, json=json_data, params=params,
                                            headers=self._headers)
                    if data.status_code == 401:
                        self.__refresh_token()
                    else:
                        continue_request = True
                return data
            except (ConnectTimeout, ConnectionError, ReadTimeout):
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

    def get_ads(self):
        url = MAIN_URL.format('get_ads/')
        data = self.__send_request(method='GET', url=url)
        return data.json()

    def get_amount(self):
        url = MAIN_URL.format('get_amount/')
        data = self.__send_request(method='GET', url=url)
        return data.json()[0]['amount']

    def update_amount(self, amount):
        url = MAIN_URL.format('get_amount/')
        json_data = {'amount': amount}
        return self.__send_request(method='POST', url=url, json_data=json_data)

    def update_order(self, order: Order):
        binance_id = order.binance_id
        url = MAIN_URL.format('api/v1/orders/' + binance_id + '/')
        print(url)
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
        url = MAIN_URL.format('api/v1/orders/')
        print(url)
        response = self.__send_request(method='POST', url=url, json_data=order)
        return response

    def get_user(self):
        url = MAIN_URL.format('get_user/')
        user = self.__send_request(method='GET', url=url).json()
        return user

    def get_order(self, binance_id):
        url = MAIN_URL.format('api/v1/orders/' + binance_id)
        data = self.__send_request(method='GET', url=url)
        return data

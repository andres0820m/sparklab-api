import datetime
import json
import os
import time

from telegram_wrapped import TelegramBot
import yaml
from PIL import Image
from cryptography.fernet import Fernet
from django.core.wsgi import get_wsgi_application
from unidecode import unidecode
from yaml.loader import SafeLoader

from Errors import *
from android_controller import AndroidController
from bank_automation import Bancolombia, Bbva, NequiPseBbva, NequiDavivienda, BancolombiaPymeWrapped
from binance_listener import BinanceListener
from constants import CONFIG_PATH, ORDER_STATUS_TO_RUN, AUT_USER, MAPPED_ACCOUNTS, MAPPED_DOCUMENTS, \
    PARTNER_IDS
from orders_wrapped import OrderWrapped
from utils import Dict2Class, left_only_numbers

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = get_wsgi_application()
from orders.models import Order

login_key = "126285836F7F84103B3D31A13EBFF3E31CD99F60989F95E4ED17F9F8D4FA341B613FB9BE8F085B4271CD0BAFED7345BE68DEC5F9A79C6FB7F57C6BDF24AF32B88F9233E9F4BFF94D9A3CA552F4B5DA96C437A1AE9B71A202802E86FDDEF8CEB530B9C32473B3F44585CE9600FACE39F69372BDF09D134B4E9778A9FF29DEA7B8DA92F81730864C84C6C35F37435FC9175013B69D1237D586072EB6191C3C37512E87A888888474C7E548B8DBB9A76E0A9EC8C030A7D763CE05C54DEA63ECFFF9EFC54C93E32DBF61B40543BCEF009F44E17B2854F09D0673280F86354A843AB94E37FB534295F45ACFB65CFFC65BA9FE1A26509238202756FE66688175193A80"


class PymeOrderExecutor:
    def __init__(self, listener: BinanceListener, dark_mode=False):
        with open(CONFIG_PATH) as f:
            self.config = Dict2Class(yaml.load(f, Loader=SafeLoader))
        self.android_controller = AndroidController(dark_mode=dark_mode)
        self.__telegram_bot = TelegramBot()
        self.listener = listener
        self.order_wrapped = OrderWrapped()
        self.__bancolombia = BancolombiaPymeWrapped(android_controller=self.android_controller, config=self.config)

    def run(self):
        self.__bancolombia.login(login_key=login_key)
        '''
            orders = self.order_wrapped.get_orders()
            self.__bancolombia.login(login_key=login_key)
            for order in orders:
                if not order.is_contact:
                    account_number = order.account.__str__()
                    name = order.name.__str__()
                    account_type = order.account_type.__str__()
                    document_type = order.document_type.__str__()
                    document_number = order.document_number.__str__()
                    print(account_number, document_number, document_type, account_type)
        '''
        print(self.__bancolombia.check_account(name='sandra guzman', document='35499230', account=91244361400,
                                               account_type='Cuenta ahorros', document_type='CC'))
        print(self.__bancolombia.transfer(account=91244361400, amount=100, document='35499230',
                                          account_type='Cuenta ahorros',
                                          document_type='CC', transfer_id='').json())


fernet = Fernet('L_V5YxcprMwMKyKtZt9ZGAe_iB2FfXPBYDcAHcpG190=')

with open('binance.data', 'rb') as enc_file:
    encrypted = enc_file.read()
    decrypted = fernet.decrypt(encrypted)
    data = json.loads(decrypted.decode("utf-8"))
    with open(CONFIG_PATH) as f:
        config = Dict2Class(yaml.load(f, Loader=SafeLoader))
    listener = BinanceListener(data=data, name=config.user_name, config=config, order_wrapped=OrderWrapped())
# listener.join_wss_stream()
# time.sleep(3)

executor = PymeOrderExecutor(listener=listener)
executor.run()

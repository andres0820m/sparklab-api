import json
import yaml
from yaml.loader import SafeLoader
from orders_wrapped import OrderWrapped
from utils import Dict2Class
from binance_listener import BinanceListener
from constants import MAPPED_BANKS_FOR_API, MAPPED_ORDER_KEY, ORDER_TEMPLATE, CONFIG_PATH
from utils import mapped_dict_from_data
from tools import str_only_numbers
from cryptography.fernet import Fernet


class BinanceListener2:

    @staticmethod
    def __get_type_of_document(number):
        id_len = len(number)
        if id_len == 10 and number[0] == '5':
            return 'pasaporte'
        else:
            if len(number) == 6:
                return 'cc_ext'
        return 'cc'

    @staticmethod
    def check_accounts_data(order: dict):
        is_contact = order['is_contact']
        bank_data = str_only_numbers(order['account'])
        if order['account'] != order['document_number']:
            if not is_contact:
                if len(str(bank_data)) == 11:
                    order['status'] = 'created'
                else:
                    order['status'] = 'waiting_for_review'
            else:
                if len(str(bank_data)) == 10:
                    order['status'] = 'created'
                else:
                    order['status'] = 'waiting_for_review'
        else:
            order['status'] = 'waiting_for_review'
        for key in order:
            if order[key] == '**********' and key not in ['user', ]:
                order['status'] = 'waiting_for_review'
        return order

    def wws_on_message(self, order):

        acc_dict = ORDER_TEMPLATE.copy()
        acc_dict['binance_id'] = str(order['orderNumber'])
        bank = MAPPED_BANKS_FOR_API[order['payType']]
        order_bank = 1
        acc_dict['bank'] = order_bank
        acc_dict['amount'] = str(int(float(order['totalPrice'])))
        acc_dict['usdt_price'] = order['price']
        acc_dict['pay_id'] = order['payMethods'][0]['id']
        mapped_dict_from_data(acc_dict=acc_dict, data=order['payMethods'][0]['fields'], bank=bank)
        if acc_dict['id_number']:
            order_document = 1
        else:
            order_document = 1
        acc_dict['document_type'] = order_document
        try:
            order_account_type = 1
        except:
            order_account_type = 1
        acc_dict['account_type'] = order_account_type
        order_data = dict((MAPPED_ORDER_KEY[key], value) for (key, value) in acc_dict.items())
        user = 2
        order_data['user'] = user
        order_data = self.check_accounts_data(order_data)
        print(order_data)


fernet = Fernet('L_V5YxcprMwMKyKtZt9ZGAe_iB2FfXPBYDcAHcpG190=')
with open('binance.data', 'rb') as enc_file:
    encrypted = enc_file.read()
    decrypted = fernet.decrypt(encrypted)
    data = json.loads(decrypted.decode("utf-8"))
    with open(CONFIG_PATH) as f:
        config = Dict2Class(yaml.load(f, Loader=SafeLoader))
    listener = BinanceListener(data=data, name='alvaro', config=config, order_wrapped=OrderWrapped())
test_model = BinanceListener2()

# order_data = listener.get_order_info('20412092467247161344')['data']
# print(order_data)
# test_model.wws_on_message(order_data)
# orders = OrderWrapped()
# order = orders.get_order('20412092467247161344')
prices = listener.get_asset_price(asset='USDT', amount=5000000, min_limit=0, banks=['BancolombiaSA'], trade_type='SELL')
print(prices)

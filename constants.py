import os
from enum import Enum
import yaml
from yaml.loader import SafeLoader

CONFIG_PATH = 'config.yaml'


class Dict2Class(object):

    def __init__(self, my_dict):
        for key in my_dict:
            setattr(self, key, my_dict[key])


with open(CONFIG_PATH) as f:
    config = Dict2Class(yaml.load(f, Loader=SafeLoader))
BANCOLOMBIA_APP_PACKAGE_NAME = 'com.todo1.mobile'
BBVA_APP_PACKAGE_NAME = 'co.com.bbva.mb'
KIWI_BROSER = 'com.kiwibrowser.browser'
NEQUI_PSE_URL = 'https://recarga.nequi.com.co/'
if os.environ['running_mode'] == 'local':
    ORDERS_URL = 'http://localhost:8000/orders/{}/'
    MAIN_URL = 'http://localhost:8000/{}'
else:
    ORDERS_URL = 'http://ec2-54-211-239-148.compute-1.amazonaws.com/orders/{}/'
    MAIN_URL = 'http://ec2-54-211-239-148.compute-1.amazonaws.com/{}'
VALID_BANKS = ['BBVA', 'bancolombia', 'pse_bbva']
VALID_ACCOUNTS_TYPE = ['Ahorros', 'corriente']
VALID_DOCUMENT_TYPE = ['cc', 'pasaporte', 'cc_ex']
STATUS_DATA = {"created": '🔜', "running": '🏃‍', "finish": '✅', "done": '✅', "fail": '😩'}
AUT_USER = config.AUT_USER
PARTNER_IDS = [2078612899, ]  # 1208740573, 1513124614]
P2P_SCREENSHOT_BOT = config.P2P_SCREENSHOT_BOT
P2P_DASHBOARD_BOT = config.P2P_DASHBOARD_BOT
API_URL = 'https://api.binance.com'
INTERNAL_ORDERS_LINK = "http://localhost:8000/admin/orders/order/{}/change/"
ORDER_STATUS_TO_RUN = ['created', 'fail', 'running']
DELETE_COMMAND = "--longpress $(printf 'KEYCODE_DEL %.0s' {1..250})"
MAX_TIME_TO_CREATED_ORDER_SECONDS = 21600
ORDER_MIN_LIMIT_LIST = [5000000, 3000000, 1000000, 700000]
COMPETITION_QUANTITY = 2000
MAX_TRM_DIFFERENCE = 110
EXCLUDE_USERS = ['Amj_crypto']


class AccountType(Enum):
    AHORROS = 0
    CORRIENTE = 1


class IDType(Enum):
    CC = 0
    NIT = 1
    PASSAPORT = 2
    CC_EXTRA = 3


MAPPED_ACCOUNTS = {"Ahorros": AccountType.AHORROS, "Corriente": AccountType.CORRIENTE}
MAPPED_DOCUMENTS = {'cc': IDType.CC, 'pasaporte': IDType.PASSAPORT, "nit": IDType.NIT, "cc_ext": IDType.CC_EXTRA}
MAPPED_TABS_BBVA_ACCOUNT_TYPE = {"Ahorros": 3, "Corriente": 4}
MAPPED_TABS_PSE_BANK_SELECTOR = {"davivienda": 9, "bbva": 5}
MAPPED_BANKS_FOR_API = {'BancolombiaSA': 'bancolombia', 'Nequi': 'Nequi'}
MAPPED_ORDER_KEY = {'binance_id': 'binance_id',
                    'bank': 'bank',
                    'amount': 'amount',
                    'usdt_price': 'usdt_price',
                    'is_contact': 'is_contact',
                    'pay_id': 'pay_id',
                    'name': 'name',
                    'account_number': 'account',
                    'id_number': 'document_number',
                    'account_type': 'account_type',
                    'document_type': 'document_type'}
NUMBERS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
KEYS_FOR_CHECK = ['name', 'id_number', 'account_number', 'account_type']
API_HEADERS = {'Accept': '*/*',
               'Accept-Encoding': 'gzip, deflate',
               'Content-Type': 'application/json'}
ORDER_TEMPLATE = {'binance_id': '**********',
                  'bank': 1,
                  'amount': '**********',
                  'usdt_price': '**********',
                  'is_contact': False,
                  'pay_id': '**********',
                  'name': '**********',
                  'account_number': '**********',
                  'id_number': '**********',
                  'account_type': 1,
                  'document_type': 1}
NEQUI_ACCOUNT_DATA_ERROR = '002'
BANCOLOMBIA_IS_DOWN = '005'
STABLE_ASSETS = ['USDT', 'BUSD']
ACCOUNT_CANT_HANDLE_THE_MONEY = '034'
ALREADY_SUBSCRIBER = 'El producto ya se encuentra'
BANCOLOMBIA_ACCOUNT_ERROR = 'verifica la inscripcion'
YAHOO_TRM_PRICE_URL = 'https://query1.finance.yahoo.com/v8/finance/chart/COP=X?region=US&lang=en-US&includePrePost=false&interval=2m&useYfid=true&range=1d&corsDomain=finance.yahoo.com&.tsrc=finance'
HTML_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    "content-type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/103.0.0.0 Safari/537.36 "}
SYMBOLS = {'ETH': 'ETHUSDT', 'BTC': 'BTCUSDT', 'BNB': 'BNBUSDT'}
SPOT_PRICE_URL = 'https://api.binance.com/api/v3/ticker/price?symbol={}'
TRANS_AMOUNT = [5000000, 3000000, 2000000]
MIN_LIMIT = 700000

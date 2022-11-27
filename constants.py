from enum import Enum

BANCOLOMBIA_APP_PACKAGE_NAME = 'com.todo1.mobile'
BBVA_APP_PACKAGE_NAME = 'co.com.bbva.mb'
KIWI_BROSER = 'com.kiwibrowser.browser'
NEQUI_PSE_URL = 'https://recarga.nequi.com.co/'
ORDERS_URL = 'http://localhost:8000/orders/{}/'
VALID_BANKS = ['BBVA', 'bancolombia', 'pse_bbva']
VALID_ACCOUNTS_TYPE = ['Ahorros', 'corriente', ""]
VALID_DOCUMENT_TYPE = ['cc', 'pasaporte', 'cc_ex', ""]
STATUS_DATA = {"created": '🔜', "running": '🏃‍', "finish": '✅', "done": '✅', "fail": '😩'}
AUT_USER = 749278100
PARTNER_IDS = [2078612899, 1208740573, 1513124614]
P2P_SCREENSHOT_BOT = '5626108765:AAEJdzS1_Zmu5uOsDu-HItPgvYdfcDFzk3I'
P2P_DASHBOARD_BOT = '5572206324:AAG_LVN8xLdFkxf4FY9IFwCmZMlV0gDWJyg'
CONFIG_PATH = 'config.yaml'
API_URL = 'https://api.binance.com'
INTERNAL_ORDERS_LINK = "http://localhost:8000/admin/orders/order/{}/change/"
ORDER_STATUS_TO_RUN = ['created', 'fail', 'running']
ORDER_TEMPLATE = '''{"bank": "",
"amount": "",
"is_contact": "",
"account": "",
"name": "",
"binance_id": "",
"document_type": "",
"account_type": "",
"document_number": ""}
'''
DELETE_COMMAND = "--longpress $(printf 'KEYCODE_DEL %.0s' {1..250})"


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
KEYS_FOR_CHECK = ['name', 'id_number', 'account_number']

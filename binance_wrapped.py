import datetime
import hashlib
import hmac
import json
import threading
import time
from abc import ABC, abstractmethod
from urllib.parse import urlencode
import pandas as pd
import requests
import websocket
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from constants import HTML_HEADERS, YAHOO_TRM_PRICE_URL, MAX_TRM_DIFFERENCE, EXCLUDE_USERS, SPOT_PRICE_URL, SYMBOLS, \
    STABLE_ASSETS, TRANS_AMOUNT, MIN_LIMIT
from Errors import OrderAsPaidError
from constants import API_URL
from telegram_wrapped import TelegramBot
from tools import str_only_numbers
from utils import send_request

CREDENTIALS_URL = '/sapi/v1/c2c/chat/retrieveChatCredential'
ORDER_PAID_URL = '/sapi/v1/c2c/orderMatch/markOrderAsPaid'
ORDER_DETAILS_URL = '/sapi/v1/c2c/orderMatch/getUserOrderDetail'
DRIVE_PARENT_FOLDER = '1T3kw9-qer4o_zhlCOFt4-_gLaxxv8xh7'
ADS_URL = '/sapi/v1/c2c/ads/search'
BRANCH_LONG = 1


class BinanceInfoGetter(ABC):
    def __init__(self, data, name, config, order_wrapped, use_trm=False):
        self.name = config.user_name
        self.trm = None
        self.spot_btc = None
        self.spot_eth = None
        self.spot_bnb = None
        self.spot_matic = None
        self.spot_doge = None
        if use_trm:
            self.__init_trm_value()
        self.telegram_bot = TelegramBot()
        self.config = config
        self.order_wrapped = order_wrapped
        self.__keep_wss = True
        self.__ws = None
        self.__secret_key = data[name]['secret_key']
        self.__public_key = data[name]['public_key']
        gauth = GoogleAuth()
        # Try to load saved client credentials
        gauth.LoadCredentialsFile("mycreds.txt")
        if gauth.credentials is None:
            # Authenticate if they're not there
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Refresh them if expired
            gauth.Refresh()
        else:
            # Initialize the saved creds
            gauth.Authorize()
        # Save the current credentials to a file
        gauth.SaveCredentialsFile("mycreds.txt")
        self.__drive = GoogleDrive(gauth)

    def __hashing(self, query_string):
        return hmac.new(self.__secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    @staticmethod
    def __get_timestamp():
        return int(time.time() * 1000)

    def send_close_wss(self):
        self.__keep_wss = False

    def __dispatch_request(self, http_method):
        session = requests.Session()

        session.headers.update({
            "User-Agent": "binance/python",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
            "Connection": "keep-alive",
            'Content-Type': 'application/json',
            'clientType': 'web',
            'X-MBX-APIKEY': self.__public_key,
        })

        return {
            'GET': session.get,
            'DELETE': session.delete,
            'PUT': session.put,
            'POST': session.post,
        }.get(http_method, 'GET')

    def send_signed_request(self, http_method, url_path, payload={}, data=None):
        retry = 3
        while retry != 0:
            query_string = urlencode(payload)
            # replace single quote to double quote
            query_string = query_string.replace('%27', '%22')
            if query_string:
                query_string = "{}&timestamp={}".format(query_string, self.__get_timestamp())
            else:
                query_string = 'timestamp={}'.format(self.__get_timestamp())

            url = API_URL + url_path + '?' + query_string + '&signature=' + self.__hashing(query_string)
            print(url)
            if data:
                params = {'url': url, 'params': {}, 'json': data}
            else:
                params = {'url': url, 'params': {}}
            response = self.__dispatch_request(http_method)(**params)
            if response.status_code >= 201:
                retry -= 1
            else:
                return response.json()

    # used for sending public data request
    def send_public_request(self, url_path, method='GET', payload={}, ):
        query_string = urlencode(payload, True)
        url = API_URL + url_path
        if query_string:
            url = url + '?' + query_string
        print("{}".format(url))
        response = self.__dispatch_request(method)(url=url)
        return response.json()

    def get_data_df(self, url, init_date, last_date):
        try:
            df = pd.DataFrame(self.send_signed_request('GET', url,
                                                       {'tradeType': 'BUY', 'startTimestamp': int(init_date),
                                                        'endTimestamp': int(last_date)})['data'])
            df = df[df['orderStatus'] == 'COMPLETED']
            df['amount'] = pd.to_numeric(df['amount'])
            df['totalPrice'] = pd.to_numeric(df['totalPrice'])
            df['unitPrice'] = pd.to_numeric(df['unitPrice'])
            df['createTime'] = df['createTime'].apply(
                lambda d: datetime.datetime.fromtimestamp(int(d) / 1000).strftime('%Y-%m-%d %H:%M:%S'))
            df['createTime'] = pd.to_datetime(df['createTime'])
            return df.sort_values(by='createTime', ascending=True)
        except:
            return pd.DataFrame(
                columns=['orderNumber', 'advNo', 'tradeType', 'asset', 'fiat', 'fiatSymbol', 'amount', 'totalPrice',
                         'unitPrice', 'orderStatus', 'createTime', 'commission', 'counterPartNickName',
                         'advertisementRole'])

    def get_wss_credentials(self):
        return self.send_signed_request(url_path=CREDENTIALS_URL, http_method='GET')

    def mark_order_as_paid(self, pay_id, order_number):

        json_data = {'orderNumber': order_number,
                     'payId': pay_id
                     }
        response = self.send_signed_request(url_path=ORDER_PAID_URL, http_method='POST', data=json_data)
        if response['message'] != 'success':
            raise OrderAsPaidError

    def get_order_info(self, binance_id):

        json_data = {"adOrderNo": binance_id}
        return self.send_signed_request(url_path=ORDER_DETAILS_URL, http_method='POST', data=json_data)

    @abstractmethod
    def wws_on_message(self, **kwargs):
        pass

    @abstractmethod
    def wws_on_error(self, **kwargs):
        pass

    @abstractmethod
    def wws_on_close(self, **kwargs):
        pass

    @abstractmethod
    def wws_on_open(self, **kwargs):
        pass

    def __join_wss_stream(self):
        while self.__keep_wss:
            try:
                wss_keys = self.get_wss_credentials()['data']
                url = '{}/{}?token={}&clientType=web'.format(wss_keys['chatWssUrl'], wss_keys['listenKey'],
                                                             wss_keys['listenToken'])

                # websocket.enableTrace(True)
                self.__ws = websocket.WebSocketApp(url,
                                                   on_open=self.wws_on_open,
                                                   on_message=self.wws_on_message,
                                                   on_error=self.wws_on_error,
                                                   on_close=self.wws_on_close)

                self.__ws.run_forever(ping_interval=15, ping_timeout=10)
                print("connection closed, reconnecting ....")
            except:
                pass

    def join_wss_stream(self):
        threading.Thread(target=self.__join_wss_stream).start()

    def send_message(self, binance_id: str, message: str):
        if self.__ws:
            self.__ws.send(json.dumps({
                "type": "text",
                "uuid": str(self.__get_timestamp()),
                "orderNo": binance_id,
                "content": message,
                "self": True,
                "clientType": "web",
                "createTime": str(self.__get_timestamp()),
                "sendStatus": "0"
            }))
        else:
            print("ws is not running !!")

    def upload_img_to_drive(self, img_path):
        retry = 3
        while retry != 0:
            try:
                gfile = self.__drive.CreateFile({'parents': [{'id': self.config.google_drive_parent}]})
                gfile.SetContentFile(img_path)
                gfile.Upload()
                file_id = gfile['id']
                url = 'https://drive.google.com/file/d/{}/view?usp=share_link'
                retry = 0
                return url.format(file_id)
            except:
                retry -= 1

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

    def get_trm_value(self):
        while 1:
            self.trm = self.get_yahoo_data()
            print(self.trm)
            time.sleep(30)

    def __init_trm_value(self):
        threading.Thread(target=self.get_trm_value).start()

    @staticmethod
    def get_yahoo_data():
        data = send_request(method='GET', headers=HTML_HEADERS, url=YAHOO_TRM_PRICE_URL)
        try:
            return float(data.json()['chart']['result'][0]['meta']['regularMarketPrice'])
        except KeyError:
            return float(data.json()['chart']['result'][0]['meta']['previousClose'])

    def get_asset_price(self, asset, amount, min_limits, banks, trade_type, fiat='COP'):
        if self.trm:
            if amount > 40000000:
                trans_mount = 5000000
            elif 20000000 <= amount <= 40000000:
                trans_mount = 3000000
            else:
                trans_mount = 2000000

            print(trans_mount)
            data = {
                "page": 1,
                "rows": 10,
                "asset": asset,
                "tradeType": trade_type,
                "fiat": fiat,
                "payTypes": banks,
                "transAmount": trans_mount,
                "publisherType": "merchant"
            }
            ads = self.send_signed_request(http_method='POST', url_path=ADS_URL, data=data)['data']
            ads_fits_trm = []
            for ad in ads:
                price = float(ad['adv']['price'])
                min_limit = float(ad['adv']['minSingleTransAmount'])
                quantity = float(ad['adv']['tradableQuantity'])
                name = ad['advertiser']['nickName']
                if self.trm - price >= MAX_TRM_DIFFERENCE and (
                        quantity >= 2000) and name not in EXCLUDE_USERS:
                    ads_fits_trm.append({'price': price, 'name': name, 'limit': min_limit})
            number_of_ads = len(ads_fits_trm)
            if not ads_fits_trm:
                return {'price': self.trm - MAX_TRM_DIFFERENCE, 'limit': 700000}

            best_ad = ads_fits_trm[0]
            best_post = 0
            for ad_position, ad in enumerate(ads_fits_trm):
                if abs(best_post - ad_position) > BRANCH_LONG:
                    break
                if ad_position < number_of_ads - 1:
                    price_diff = 5
                    if best_ad['price'] - ad['price'] >= price_diff:
                        best_ad = ad
                        best_post = ad_position
                    elif (best_ad['limit'] - ad['limit'] / best_ad['limit']) <= 0.2 and ad['limit'] < best_ad[
                        'limit']:
                        best_ad = ad
                        best_post = ad_position
            if best_ad['name'] not in ['AE_Mejia', ]:
                if (trans_mount - best_ad['limit']) / trans_mount < 0.5:
                    return {'price': best_ad['price'], 'limit': best_ad['limit'] - (best_ad['limit'] * 0.1)}
                else:
                    return {'price': best_ad['price'] + 0.01, 'limit': best_ad['limit']}
            else:
                return {'price': best_ad['price'], 'limit': best_ad['limit']}

    def get_ad_by_number(self, adb_number):
        url = '/sapi/v1/c2c/ads/getDetailByNo'
        return self.send_signed_request(http_method='POST', url_path=url, payload={'adsNo': adb_number})

    def update_abd(self, adb_number, price, low_limit, asset, trade_type='BUY', fiat='COP', status=3):

        data = {
            "advNo": adb_number,
            "advStatus": status,
            "asset": asset,
            "buyerBtcPositionLimit": '0.01000000',
            "buyerKycLimit": 1,
            "buyerRegDaysLimit": -1,
            "fiatUnit": fiat,
            "maxSingleTransAmount": '200000000',
            "minSingleTransAmount": str(int(low_limit)),
            "payTimeLimit": 360,
            "price": str(price),
            "priceType": 1,
            'rateFloatingRatio': '0.00000000',
            "tradeType": trade_type,
        }

        url = '/sapi/v1/c2c/ads/update'
        self.send_signed_request(http_method='POST', url_path=url, data=data)

    @staticmethod
    def get_spot_data(asset):
        url = SPOT_PRICE_URL.format(SYMBOLS[asset])
        print(url)
        response = send_request(method='GET', url=url, use_data=False)
        return response.json()

    def get_non_stable_price(self, asset, amount, banks, trade_type, fiat='COP'):
        asset_price = float(self.get_spot_data(asset=asset)['price'])
        if self.trm:
            for trans_mount in TRANS_AMOUNT:
                print(trans_mount)
                data = {
                    "page": 1,
                    "rows": 10,
                    "asset": asset,
                    "tradeType": trade_type,
                    "fiat": fiat,
                    "payTypes": banks,
                    "transAmount": trans_mount,
                    "publisherType": "merchant"
                }
                ads = self.send_signed_request(http_method='POST', url_path=ADS_URL, data=data)['data']
                for ad in ads:
                    price = float(ad['adv']['price'])
                    min_limit = float(ad['adv']['minSingleTransAmount'])
                    quantity = float(ad['adv']['tradableQuantity'])
                    name = ad['advertiser']['nickName']
                    asset_unit_price = (price / asset_price) + 3
                    quantity_in_usd = quantity * asset_price
                    final_ad = {}
                    if self.trm - asset_unit_price >= MAX_TRM_DIFFERENCE and quantity_in_usd >= 1200 and name not in [
                        'Amj_crypto', 'AE_Mejia']:
                        final_ad['price'] = price
                        final_ad['name'] = name
                        final_ad['min_limit'] = min_limit
                        break
                if final_ad:
                    print(asset, final_ad['price'] / asset_price)
                    if final_ad['min_limit'] >= (MIN_LIMIT + (MIN_LIMIT * 0.2)):
                        return {'price': price, 'limit': final_ad['min_limit'] - (final_ad['min_limit'] * 0.2),
                                'name': name}
                    else:
                        return {'price': price + 0.01, 'limit': MIN_LIMIT, 'name': name}

            return {'price': (self.trm - MAX_TRM_DIFFERENCE) * asset_price, 'limit': MIN_LIMIT, 'name': None}

    def get_stable_price(self, asset, ad_config, banks, trade_type, fiat='COP'):
        use_limit = ad_config['use_min_limit']
        min_ad_limit = float(ad_config['min_limit'])
        final_min = float('inf')
        if self.trm:
            for trans_mount in TRANS_AMOUNT:
                print(trans_mount)
                data = {
                    "page": 1,
                    "rows": 10,
                    "asset": asset,
                    "tradeType": trade_type,
                    "fiat": fiat,
                    "payTypes": banks,
                    "transAmount": trans_mount,
                    "publisherType": "merchant"
                }
                ads = self.send_signed_request(http_method='POST', url_path=ADS_URL, data=data)['data']
                for ad in ads:
                    price = float(ad['adv']['price'])
                    min_limit = float(ad['adv']['minSingleTransAmount'])
                    quantity = float(ad['adv']['tradableQuantity'])
                    name = ad['advertiser']['nickName']
                    asset_unit_price = price
                    quantity_in_usd = quantity
                    final_ad = {}
                    if min_limit < final_min:
                        final_min = min_limit
                    if self.trm - asset_unit_price >= MAX_TRM_DIFFERENCE and quantity_in_usd >= 2300 and name not in [
                        'Amj_crypto', 'AE_Mejia']:
                        final_ad['price'] = price
                        final_ad['name'] = name
                        final_ad['min_limit'] = min_limit
                        break
                if final_ad:
                    print(asset, final_ad['price'])
                    if final_min >= (MIN_LIMIT + (MIN_LIMIT * 0.2)):
                        if not use_limit:
                            final_min_price = final_min - (final_min * 0.2)
                        elif float(final_min) <= min_ad_limit:
                            final_min_price = MIN_LIMIT
                        else:
                            final_min_price = min_ad_limit
                        return {'price': price, 'limit': final_min_price, 'name': name}
                    else:
                        return {'price': price + 0.01, 'limit': MIN_LIMIT, 'name': name}

            return {'price': self.trm - MAX_TRM_DIFFERENCE, 'limit': MIN_LIMIT, 'name': None}

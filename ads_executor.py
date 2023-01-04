import json
import random
import time

import yaml
from yaml.loader import SafeLoader
from orders_wrapped import OrderWrapped
from utils import Dict2Class
from binance_listener import BinanceListener
from constants import CONFIG_PATH, STABLE_ASSETS
from cryptography.fernet import Fernet
import threading


class AdsRunner:
    def __init__(self, listener):
        self.__listener = listener

    def run_ads(self):
        orders_wrapped = OrderWrapped()
        old_prices = dict()
        while 1:
            try:
                old_price = None
                current_price = 0
                ads = orders_wrapped.get_ads()
                amount = float(orders_wrapped.get_amount())
                if amount < 1000000:
                    status = 3
                else:
                    status = 1
                for ad in ads:
                    asset = ad['asset']
                    if asset in STABLE_ASSETS:
                        result = self.__listener.get_stable_price(asset=asset, ad_config=ad,
                                                                  banks=['BancolombiaSA'], trade_type='SELL')
                    else:
                        result = self.__listener.get_non_stable_price(asset=asset, amount=amount,
                                                                      banks=['BancolombiaSA'],
                                                                      trade_type='SELL')
                    print(result, asset)

                    if result:
                        try:
                            old_price = old_prices[asset]
                            current_price = ads['prices']
                        except:
                            pass
                        if old_price != current_price:
                            self.__listener.update_abd(adb_number=ad['ad_id'], price=result['price'],
                                                       low_limit=result['limit'],
                                                       asset=asset,
                                                       status=status)
                    try:
                        old_prices[asset] = result['price']
                    except TypeError:
                        pass

                delay = random.randint(15, 20)
                print("the delay for update is: {}".format(str(delay)))
                time.sleep(delay)

            except:
                print("cant get prices")
                time.sleep(5)

    def run(self):
        threading.Thread(target=self.run_ads).start()

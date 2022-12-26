import json
import random
import time

import yaml
from yaml.loader import SafeLoader
from orders_wrapped import OrderWrapped
from utils import Dict2Class
from binance_listener import BinanceListener
from constants import CONFIG_PATH, ORDER_MIN_LIMIT_LIST, STABLE_ASSETS
from cryptography.fernet import Fernet

fernet = Fernet('L_V5YxcprMwMKyKtZt9ZGAe_iB2FfXPBYDcAHcpG190=')
with open('binance.data', 'rb') as enc_file:
    encrypted = enc_file.read()
    decrypted = fernet.decrypt(encrypted)
    data = json.loads(decrypted.decode("utf-8"))
    with open(CONFIG_PATH) as f:
        config = Dict2Class(yaml.load(f, Loader=SafeLoader))
    listener = BinanceListener(data=data, name=config.user_name, config=config, order_wrapped=OrderWrapped())
orders_wrapped = OrderWrapped()
while 1:
    ads = orders_wrapped.get_ads()
    amount = float(orders_wrapped.get_amount())
    if amount < 1000000:
        status = 3
    else:
        status = 1
    for ad in ads:
        asset = ad['asset']
        if asset in STABLE_ASSETS:
            result = listener.get_asset_price(asset=asset, amount=amount, min_limits=ORDER_MIN_LIMIT_LIST,
                                              banks=['BancolombiaSA'], trade_type='SELL')
        else:
            result = listener.get_non_stable_price(asset=asset, amount=amount, banks=['BancolombiaSA'],
                                                   trade_type='SELL')
        print(result, asset)
        if result:
            listener.update_abd(adb_number=ad['ad_id'], price=result['price'], low_limit=result['limit'], asset=asset,
                                status=status)

    delay = random.randint(15, 20)
    print("the delay for update is: {}".format(str(delay)))
    time.sleep(delay)
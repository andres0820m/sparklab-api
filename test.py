import requests
from constants import ORDERS_URL

print(requests.get(ORDERS_URL.format(9)).json())
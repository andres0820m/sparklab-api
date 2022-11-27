import os
from datetime import datetime
# mark django settings module as settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# instantiate a web sv for django which is a wsgi
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
from orders.models import Order

# Create Operations here
data_dict = {'amount': '4198000', 'is_contact': False,
             'account': "221147382",
             'name': "ERAZO CUELTAN DILVER ROBINSON",
             'binance_id': "20395197508415926272",
             'document_type': 'cc',
             'account_type': "Ahorros",
             'document_number': '1126451955',
             'date': datetime.now()}
order = Order(**data_dict)
order.save()

# Read operation logic
orders = Order.objects.all()

print(orders[0].binance_id)
# Prints Hello, I am Nimish, 23 y/o. Reachable at nimishverma@ymail.com

from django.forms import ModelForm
from .models import Order
from django import forms


class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ['binance_id', 'account', 'name', 'document_type', 'account_type',
                  'document_number', 'fail_retry']

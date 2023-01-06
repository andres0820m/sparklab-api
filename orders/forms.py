from django.forms import ModelForm
from .models import Order, Ads, AmountToBuy
from django import forms


class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ['binance_id', 'account', 'name', 'document_type', 'account_type',
                  'document_number', 'fail_retry']


class AdsForm(ModelForm):
    class Meta:
        model = Ads
        fields = ['ad_id', 'min_limit', 'asset', 'is_active', 'use_min_limit']


class AmountToBuyForm(ModelForm):
    class Meta:
        model = AmountToBuy
        fields = ['amount', 'is_active']

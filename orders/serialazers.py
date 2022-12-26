from .models import Order, Ads
from rest_framework import serializers


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'


class AdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ads
        fields = '__all__'

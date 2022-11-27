from django.shortcuts import render, redirect
from rest_framework import viewsets
from .serialazers import OrderSerializer
from .forms import OrderForm
from django.contrib import messages
from .models import Order, DocumentType, AccountType
import datetime


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    http_method_names = ['get', 'head', 'post']


def home(request):
    time_threshold = datetime.datetime.now() - datetime.timedelta(hours=27)
    orders = Order.objects.filter(date__gt=time_threshold).filter(status__in=['waiting_for_review'])
    return render(request, "orders_check.html", {"orders": orders})


def running_fail(request):
    time_threshold = datetime.datetime.now() - datetime.timedelta(hours=27)
    orders = Order.objects.filter(date__gt=time_threshold).filter(status__in=['fail', 'running', 'created'])
    return render(request, "running.html", {"orders": orders})


def save_order(request):
    binance_id = request.POST['binance_id']
    account = request.POST['account']
    document = request.POST['document_number']
    document_type = DocumentType(pk=request.POST['document_type'])
    account_type = AccountType(pk=request.POST['account_type'])
    name = request.POST['name']
    order = Order.objects.get(binance_id=binance_id)
    order.account = account
    order.document_type = document_type
    order.document_number = document
    order.account_type = account_type
    order.name = name
    order.status = 'created'
    order.save()
    return redirect('/status')


def edit_order(request, binance_id):
    order = Order.objects.get(binance_id=binance_id)
    initial_data = {
        'binance_id': order.binance_id,
        'account': order.account,
        'document_number': order.document_number,
        'document_type': order.document_type,
        'account_type': order.account_type,
        'name': order.name
    }
    order_form = OrderForm(initial=initial_data)
    data = {
        'order': order,
        'order_form': order_form
    }
    return render(request, "edit_orders.html", data)


def delete_order(request, binance_id):
    order = Order.objects.get(binance_id=binance_id)
    order.status = "cancelled"
    order.save()
    return redirect('/status')


def delete_order_running(request, binance_id):
    order = Order.objects.get(binance_id=binance_id)
    order.status = "cancelled"
    order.save()
    return redirect('/running')


def approve_order(request, binance_id):
    order = Order.objects.get(binance_id=binance_id)
    order.status = 'created'
    order.save()

    return redirect('/status')


def approve_order_running(request, binance_id):
    order = Order.objects.get(binance_id=binance_id)
    order.status = 'created'
    order.save()

    return redirect('/running')

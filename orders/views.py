from django.shortcuts import render, redirect
from rest_framework import viewsets
from .serialazers import OrderSerializer, AdsSerializer
from .forms import OrderForm, AdsForm, AmountToBuyForm
from rest_framework.views import APIView
from .models import Order, DocumentType, AccountType, Bank, Ads, AmountToBuy
import datetime
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
import locale

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
TRUE_OR_FALSE_MAP = {'on': True, 'off': False}


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    http_method_names = ['get', 'head', 'post', 'put']


class AbsVietSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = AdsSerializer
    queryset = Ads.objects.all()
    http_method_names = ['get', 'head']


class GetAds(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        ads = Ads.objects.filter(user=request.user).filter(is_active=True).values()
        return Response(ads, status=status.HTTP_200_OK)


class GetAmount(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        amount = AmountToBuy.objects.filter(user=request.user).values()
        return Response(amount, status=status.HTTP_200_OK)

    def post(self, request):
        actual_amount = AmountToBuy.objects.filter(user=request.user).values()[0]
        actual_amount = AmountToBuy(**actual_amount)
        amount = float(request.data['amount'])
        actual_amount.amount = actual_amount.amount + amount
        actual_amount.save()
        return Response(actual_amount.amount, status=status.HTTP_200_OK)


@login_required
def home(request):
    time_threshold = datetime.datetime.now() - datetime.timedelta(hours=27)
    orders = Order.objects.filter(user=request.user).filter(date__gt=time_threshold).filter(
        status__in=['waiting_for_review'])
    amount = locale.currency(float(AmountToBuy.objects.filter(user=request.user)[0].amount), grouping=True)
    amount_to_buy = AmountToBuy.objects.get(user=request.user)
    initial_data = {
        'amount': amount_to_buy.amount,
        'is_active': amount_to_buy.is_active
    }
    amount_form = AmountToBuyForm(initial=initial_data)
    return render(request, "orders_check.html",
                  {"orders": orders, 'amount': amount, 'is_active': amount_to_buy.is_active,
                   'amount_form': amount_form})


@login_required
def ads(request):
    ads = Ads.objects.filter(user=request.user)
    return render(request, "ads.html", {"ads": ads})


@login_required
def running_fail(request):
    time_threshold = datetime.datetime.now() - datetime.timedelta(hours=27)
    orders = Order.objects.filter(user=request.user).filter(date__gt=time_threshold).filter(
        status__in=['fail', 'running', 'created'])
    return render(request, "running.html", {"orders": orders})


@login_required
def save_order(request):
    print(request.get_full_path())
    binance_id = request.POST['binance_id']
    account = request.POST['account']
    document = request.POST['document_number']
    document_type = DocumentType(pk=request.POST['document_type'])
    account_type = AccountType(pk=request.POST['account_type'])
    fail_retry = request.POST['fail_retry']
    name = request.POST['name']
    order = Order.objects.get(binance_id=binance_id)
    order.account = account
    order.document_type = document_type
    order.document_number = document
    order.account_type = account_type
    order.name = name
    order.status = 'created'
    order.fail_retry = fail_retry
    order.save()
    return redirect('/status')


@login_required
def save_amount(request):
    user = request.user
    amount = float(request.POST['amount'])
    is_active = TRUE_OR_FALSE_MAP[request.POST.get('is_active', 'off')]
    print(is_active)
    user_amount = AmountToBuy.objects.get(user=user)
    user_amount.is_active = is_active
    user_amount.amount = amount
    user_amount.save()
    return redirect('/status')


@login_required
def save_order_running(request):
    binance_id = request.POST['binance_id']
    account = request.POST['account']
    document = request.POST['document_number']
    document_type = DocumentType(pk=request.POST['document_type'])
    account_type = AccountType(pk=request.POST['account_type'])
    fail_retry = request.POST['fail_retry']
    name = request.POST['name']
    order = Order.objects.get(binance_id=binance_id)
    order.account = account
    order.document_type = document_type
    order.document_number = document
    order.account_type = account_type
    order.name = name
    order.status = 'created'
    order.fail_retry = fail_retry
    order.save()
    return redirect('/running')


@login_required
def save_ad(request):
    ad_id = request.POST['ad_id']
    min_limit = request.POST['min_limit']
    asset = request.POST['asset']
    is_active = TRUE_OR_FALSE_MAP[request.POST.get('is_active', 'off')]
    use_min_limit = TRUE_OR_FALSE_MAP[request.POST.get('use_min_limit', 'off')]
    ad = Ads.objects.get(ad_id=ad_id)
    ad.ad_id = ad_id
    ad.asset = asset
    ad.min_limit = min_limit
    ad.is_active = is_active
    ad.use_min_limit = use_min_limit
    ad.save()
    return redirect('/ads')


@login_required
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


@login_required
def edit_ad(request, ad_id):
    ad = Ads.objects.get(ad_id=ad_id)
    initial_data = {
        'ad_id': ad.ad_id,
        'min_limit': ad.min_limit,
        'asset': ad.asset,
        'is_active': ad.is_active,
        'use_min_limit': ad.use_min_limit,
    }
    ad_form = AdsForm(initial=initial_data)
    data = {
        'ad': ad,
        'ad_form': ad_form
    }
    return render(request, "ads_edit.html", data)


@login_required
def edit_order_running(request, binance_id):
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
    return render(request, "edit_orders_running.html", data)


@login_required
def delete_order(request, binance_id):
    order = Order.objects.get(binance_id=binance_id)
    order.status = "cancelled"
    order.save()
    return redirect('/status')


@login_required
def delete_order_running(request, binance_id):
    order = Order.objects.get(binance_id=binance_id)
    order.status = "cancelled"
    order.save()
    return redirect('/running')


@login_required
def approve_order(request, binance_id):
    order = Order.objects.get(binance_id=binance_id)
    order.status = 'created'
    order.save()

    return redirect('/status')


@login_required
def approve_order_running(request, binance_id):
    order = Order.objects.get(binance_id=binance_id)
    order.status = 'created'
    order.save()

    return redirect('/running')


class CheckAccount(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        account = request.data['account']
        try:
            order = Order.objects.filter(user=request.user).filter(status='done').filter(account=account)
            if len(order) > 1:
                return Response("True", status=status.HTTP_200_OK)
            else:
                return Response("False", status=status.HTTP_404_NOT_FOUND)
        except:
            return Response("False", status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            binance_id = request.data['binance_id']
            order = Order.objects.get(binance_id=binance_id)
            order.subscribe = True
            order.save()
            return Response(True, status=status.HTTP_200_OK)
        except:
            return Response(False, status=status.HTTP_400_BAD_REQUEST)


class PotentialOrders(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        time_threshold = datetime.datetime.now() - datetime.timedelta(hours=15)
        orders = Order.objects.filter(user=request.user).filter(date__gt=time_threshold).values()
        return Response(orders, status=status.HTTP_200_OK)


class GetBank(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            return Response(Bank.objects.filter(bank=request.data['bank']).values()[0], status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class GetAccount(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            return Response(AccountType.objects.filter(account_type=request.data['account']).values()[0],
                            status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class GetDocument(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            return Response(DocumentType.objects.filter(document=request.data['document']).values()[0],
                            status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class GetUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(request.user.pk, status=status.HTTP_200_OK)


class GetNotification(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            return Response(AmountToBuy.objects.filter(user=request.user).values()[0],
                            status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

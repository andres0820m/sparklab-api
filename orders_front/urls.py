from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from orders.views import OrderViewSet, home, edit_order, save_order, delete_order, approve_order, running_fail, \
    delete_order_running, approve_order_running, CheckAccount, PotentialOrders, save_order_running, edit_order_running

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename="snippets")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('status/', home),
    path('running/', running_fail),
    path('save_edit/', save_order),
    path('save_edit_running/', save_order_running),
    path('status/edit_order/<binance_id>', edit_order),
    path('status/approve_order/<binance_id>', approve_order),
    path('status/delete_order/<binance_id>', delete_order),
    path('running/edit_order/<binance_id>', edit_order_running),
    path('running/approve_order/<binance_id>', approve_order_running),
    path('running/delete_order/<binance_id>', delete_order_running),
    path('', include(router.urls)),
    path('check_account/', CheckAccount.as_view()),
    path('potential_orders/', PotentialOrders.as_view())

]

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as jwt_views
from orders.views import OrderViewSet, home, edit_order, save_order, delete_order, approve_order, running_fail, \
    delete_order_running, approve_order_running
from django.contrib.auth.views import LoginView

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename="snippets")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('status/', home),
    path('running/', running_fail),
    path('save_edit/', save_order),
    path('status/edit_order/<binance_id>', edit_order),
    path('status/approve_order/<binance_id>', approve_order),
    path('status/delete_order/<binance_id>', delete_order),
    path('running/edit_order/<binance_id>', edit_order),
    path('running/approve_order/<binance_id>', approve_order_running),
    path('running/delete_order/<binance_id>', delete_order_running),
    path('login/status/', home),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', LoginView.as_view(template_name='login.html'), name="login"),
    path('', include(router.urls)),

]

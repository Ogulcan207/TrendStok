from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Sol paneldeki işlemler için URL'ler
    path('stock-management/', views.stock_management, name='stock_management'),
    path('pie-chart/', views.pie_chart, name='pie_chart'),
    path('order-management/', views.order_management, name='order_management'),

    # Sepet işlemleri
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),

    # Sipariş işlemleri
    path('place-order/', views.place_order, name='place_order'),
    path('admin/order-list/', views.admin_order_list, name='admin_order_list'),
    path('order-management/approve-all/', views.approve_all_orders, name='approve_all_orders'),
    path('order-management/update-priorities/', views.update_priorities_view, name='update_priorities'),
    path('order-management/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    

    # Kullanıcı profili
    path('user-profile/', views.user_profile, name='user_profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('user-orders/', views.user_orders, name='user_orders'),
    path('user-orders/cancel/<int:order_id>/', views.cancel_user_order, name='cancel_user_order'),
]
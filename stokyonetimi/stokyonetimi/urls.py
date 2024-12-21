from django.urls import include, path
from django.shortcuts import redirect
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login')),  # Root URL login sayfasına yönlendirilir
    path('isleyis/', include('isleyis.urls')),  # 'isleyis' uygulamasının URL'leri
]

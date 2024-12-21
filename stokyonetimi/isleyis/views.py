from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from .models import Customer

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = Customer.objects.get(username=username)
            if check_password(password, user.password):
                # Kullanıcı girişi başarılı
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                return redirect('user_dashboard')  # Tek bir kullanıcı dashboard sayfasına yönlendirme
            else:
                return render(request, 'login.html', {'error': 'Hatalı şifre!'})
        except Customer.DoesNotExist:
            return render(request, 'login.html', {'error': 'Kullanıcı bulunamadı!'})
    return render(request, 'login.html')

def user_dashboard(request):
    username = request.session.get('username', 'Anonim Kullanıcı')
    return render(request, 'user_dashboard.html', {'username': username})

def admin_dashboard(request):
    username = request.session.get('username', 'Anonim Kullanıcı')
    return render(request, 'admin_dashboard.html', {'username': username})

def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def user_dashboard(request):
    username = request.session.get('username', 'Anonim Kullanıcı')
    return render(request, 'user_dashboard.html', {'username': username})
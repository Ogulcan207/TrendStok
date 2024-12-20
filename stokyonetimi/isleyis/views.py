from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                request.session['username'] = username  # Kullanıcı adını session'a ekle
                return redirect('home')  # Başarılı girişten sonra ana sayfaya yönlendir
            else:
                return render(request, 'login.html', {'form': form, 'error': 'Geçersiz kullanıcı adı veya şifre'})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)  # Kullanıcının oturumunu sonlandır
    return redirect('login')  # Çıkıştan sonra giriş sayfasına yönlendir

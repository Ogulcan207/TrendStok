from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import authenticate, login
from .models import Customer, Product
from django.contrib.auth.models import User  # User modelini ekleyin
import json

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

def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def user_dashboard(request):
    user = Customer.objects.get(id=request.session['user_id'])  # Oturumdaki kullanıcıyı al
    products = Product.objects.all()  # Tüm ürünleri al
    search_query = request.GET.get('search', '').strip()
    price_filter = request.GET.get('price', '')

    if search_query:
        products = products.filter(product_name__icontains=search_query)
    if price_filter == 'low':
        products = products.order_by('price')
    elif price_filter == 'high':
        products = products.order_by('-price')

    return render(request, 'user_dashboard.html', {
        'user': user,  # Kullanıcı bilgilerini gönder
        'products': products,
        'search_query': search_query,
        'price_filter': price_filter,
    })


def admin_dashboard(request):
    username = request.session.get('username', 'Anonim Kullanıcı')
    products = Product.objects.all()  # Tüm ürünleri al
    
    products_data = [
    {"product_name": product.product_name, "stock": product.stock}
    for product in products
    ]
    products_data_json = json.dumps(products_data)  # JSON formatına dönüştür


    if request.method == 'POST':
        if 'add_product' in request.POST:
            product_name = request.POST.get('product_name')
            stock = request.POST.get('stock')
            price = request.POST.get('price')
            Product.objects.create(product_name=product_name, stock=stock, price=price)
            return redirect('admin_dashboard')  # Ekleme sonrası yönlendirme

        elif 'update_product' in request.POST:
            product_id = request.POST.get('product_id')
            product_name = request.POST.get('product_name')
            stock = request.POST.get('stock')
            price = request.POST.get('price')

            # Ürünü güncelle
            product = Product.objects.get(id=product_id)
            product.product_name = product_name
            product.stock = stock
            product.price = price
            product.save()
            return redirect('admin_dashboard')

        elif 'delete_product' in request.POST:
            product_id = request.POST.get('product_id')
            product = Product.objects.get(id=product_id)
            product.delete()  # Ürünü sil
            return redirect('admin_dashboard')

    return render(request, 'admin_dashboard.html', {
        'username': username,
        'products': products,
        'products_data': products_data_json  # Grafik verileri
    })


@login_required
def user_profile(request):
    user = Customer.objects.get(id=request.session['user_id'])  # Oturumdaki kullanıcıyı al
    return render(request, 'user_profile.html', {'user': user})

def update_profile(request):
    if request.method == 'POST':
        user = Customer.objects.get(id=request.session['user_id'])

        # Kullanıcı bilgilerini güncelle
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')

        # Şifre boş değilse güncelle
        password = request.POST.get('password')
        if password:
            user.password = make_password(password)

        user.save()
        return redirect('user_dashboard')  # Güncelledikten sonra dashboard'a yönlendir
    else:
        user = Customer.objects.get(id=request.session['user_id'])
        return render(request, 'user_dashboard.html', {
            'user': user,  # Kullanıcı bilgilerini tekrar gönder
            'products': Product.objects.all(),  # Ürün bilgilerini de gönder
        })


def cart_view(request):
    cart = request.session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart)
    

    return render(request, 'cart.html', {
        'cart': cart,
        'total_price': total_price,
    })


def add_to_cart(request):
    if request.method == 'POST':
        product_id = int(request.POST.get('product_id'))
        product = get_object_or_404(Product, id=product_id)

        cart = request.session.get('cart', [])
        for item in cart:
            if item['id'] == product_id:
                if item['quantity'] < 5:  # Maksimum 5 adet kontrolü
                    item['quantity'] += 1
                else:
                    from django.contrib import messages
                    messages.warning(request, "Bu üründen en fazla 5 adet alabilirsiniz.")
                request.session['cart'] = cart
                return redirect('cart')

        # Resim yolunu ekleyin
        cart.append({
            'id': product.id,
            'name': product.product_name,
            'price': float(product.price),
            'quantity': 1,
            'image': product.image.url if product.image else '',  # Resim yolunu ekle
        })
        request.session['cart'] = cart
        return redirect('cart')


def update_cart(request):
    if request.method == 'POST':
        product_id = int(request.POST.get('product_id'))
        quantity = int(request.POST.get('quantity'))

        # Miktar kontrolü (En fazla 5 adet)
        if quantity > 5:
            quantity = 5

        cart = request.session.get('cart', [])
        for item in cart:
            if item['id'] == product_id:
                item['quantity'] = quantity
                break
        request.session['cart'] = cart
        return redirect('cart')


def remove_from_cart(request):
    if request.method == 'POST':
        product_id = int(request.POST.get('product_id'))

        cart = request.session.get('cart', [])
        cart = [item for item in cart if item['id'] != product_id]
        request.session['cart'] = cart
        return redirect('cart')

from .models import Order

def place_order(request):
    if request.method == 'POST':
        cart = request.session.get('cart', [])
        user = Customer.objects.get(id=request.session['user_id'])

        for item in cart:
            Order.objects.create(
                customer=user,
                product_id=item['id'],
                quantity=item['quantity'],
                total_price=item['price'] * item['quantity'],
                order_status='Pending',
            )
        request.session['cart'] = []  # Sepeti temizle
        return redirect('user_dashboard')

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        # Kullanıcının superuser olup olmadığını kontrol et
        if user is not None and user.is_superuser:  # Sadece superuser'lar admin olabilir
            login(request, user)
            return redirect('admin_dashboard')  # Giriş başarılıysa admin paneline yönlendir
        else:
            return render(request, 'admin_login.html', {'error': 'Geçersiz kullanıcı adı veya şifre!'})

    return render(request, 'admin_login.html')

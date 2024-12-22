from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import check_password
from .models import Customer, Product

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
    products = Product.objects.all()  # Tüm ürünleri al
    search_query = request.GET.get('search', '').strip()  # Arama sorgusunu al
    price_filter = request.GET.get('price', '')  # Fiyat sıralama filtresi

    # Arama sorgusu uygulanıyorsa filtrele
    if search_query:
        products = products.filter(product_name__icontains=search_query)

    # Fiyat sıralama filtresi uygulanıyorsa sırala
    if price_filter == 'low':
        products = products.order_by('price')  # Fiyatı düşükten yükseğe sırala
    elif price_filter == 'high':
        products = products.order_by('-price')  # Fiyatı yüksekten düşüğe sırala

    username = request.session.get('username', 'Anonim Kullanıcı')

    return render(request, 'user_dashboard.html', {
        'username': username,
        'products': products,
        'search_query': search_query,
        'price_filter': price_filter,
    })


def admin_dashboard(request):
    username = request.session.get('username', 'Anonim Kullanıcı')
    return render(request, 'admin_dashboard.html', {'username': username})

def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        # Oturumda sepet oluşturulmamışsa oluştur
        if 'cart' not in request.session:
            request.session['cart'] = []

        # Sepete ürün ekle
        cart = request.session['cart']
        cart.append({
            'id': product.id,
            'name': product.product_name,
            'price': float(product.price),
            'quantity': 1
        })
        request.session['cart'] = cart  # Değişiklikleri kaydet

        return redirect('user_dashboard')
def cart_view(request):
    cart = request.session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart)

    return render(request, 'cart.html', {
        'cart': cart,
        'total_price': total_price
    })

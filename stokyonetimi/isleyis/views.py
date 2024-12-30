from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import check_password, make_password
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from .models import Customer, Product, Order, OrderDetail
import json, time, queue
from django.utils.timezone import now
from threading import Thread, Lock
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from celery import shared_task
from decimal import Decimal

class OrderThread(Thread):
    def __init__(self, order):
        super().__init__()
        self.order = order

    def run(self):
        print(f"Sipariş {self.order.id} işleniyor...")
        time.sleep(5)  # İşleme süresi (örnek olarak 5 saniye verildi)
        self.order.order_status = 'Completed'
        self.order.save()
        print(f"Sipariş {self.order.id} tamamlandı.")

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
    products = Product.objects.all()
    products_data = [
        {"product_name": product.product_name, "stock": product.stock}
        for product in products
    ]
    return render(request, 'admin_dashboard.html', {
        'username': request.session.get('username', 'Anonim Kullanıcı'),
        'products_data': json.dumps(products_data)
    })

def stock_management(request):
    products = Product.objects.all()

    if request.method == 'POST':
        if 'add_product' in request.POST:
            product_name = request.POST.get('product_name')
            stock = request.POST.get('stock')
            price = request.POST.get('price')
            Product.objects.create(product_name=product_name, stock=stock, price=price)
            return redirect('stock_management')
        elif 'update_product' in request.POST:
            product_id = request.POST.get('product_id')
            product_name = request.POST.get('product_name')
            stock = request.POST.get('stock')
            price = request.POST.get('price')
            product = Product.objects.get(id=product_id)
            product.product_name = product_name
            product.stock = stock
            product.price = price
            product.save()
            return redirect('stock_management')
        elif 'delete_product' in request.POST:
            product_id = request.POST.get('product_id')
            product = Product.objects.get(id=product_id)
            product.delete()
            return redirect('stock_management')

    return render(request, 'stock_management.html', {'products': products})

def pie_chart(request):
    products = Product.objects.all()

    products_data = [
        {"product_name": product.product_name, "stock": product.stock}
        for product in products
    ]
    products_data_json = json.dumps(products_data)

    return render(request, 'pie_chart.html', {'products_data': products_data_json})

@csrf_exempt
def update_priorities_view(request):
    """
    Dinamik öncelik güncelleme işlemini tetikler.
    """
    update_order_priorities()
    return JsonResponse({'status': 'success', 'message': 'Priorities updated!'})

def order_management(request):
    update_order_priorities()
    orders = Order.objects.prefetch_related('order_details').filter(order_status='Pending').order_by('-priority_score')

    if request.method == 'POST':
        if 'approve_all' in request.POST:
            for order in orders:
                thread = OrderThread(order)
                thread.start()
            return redirect('order_management')

    return render(request, 'order_management.html', {'orders': orders})

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

@login_required
def user_orders(request):
    user = Customer.objects.get(id=request.session['user_id'])
    orders = Order.objects.filter(customer=user).prefetch_related('order_details').order_by('-order_date')

    return render(request, 'user_orders.html', {'orders': orders})

from django.contrib import messages

@login_required
def cancel_user_order(request, order_id):
    """
    Kullanıcının kendi siparişini iptal etmesine izin verir.
    """
    try:
        # Oturumdaki kullanıcıyı alın
        user = Customer.objects.get(id=request.session['user_id'])
        
        # Kullanıcıya ait siparişi bulun
        order = Order.objects.get(id=order_id, customer=user)

        # Yalnızca beklemede olan siparişler iptal edilebilir
        if order.order_status == 'Pending':
            order.delete()
            messages.success(request, "Sipariş başarıyla iptal edildi.")
        else:
            messages.warning(request, "Tamamlanmış veya başarısız siparişleri iptal edemezsiniz.")
    
    except Order.DoesNotExist:
        messages.error(request, "Sipariş bulunamadı veya size ait değil.")

    # Kullanıcının sipariş sayfasına yönlendirin
    return redirect('user_orders')

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

def place_order(request):
    if request.method == 'POST':
        cart = request.session.get('cart', [])
        user = Customer.objects.get(id=request.session['user_id'])

        if not cart:
            return redirect('cart')

        # Toplam fiyatı hesapla
        total_price = sum(Decimal(item['price']) * item['quantity'] for item in cart)

        # Kullanıcının bütçesini kontrol et
        if user.budget < total_price:
            from django.contrib import messages
            messages.error(request, "Yetersiz bütçe. Siparişi tamamlayamazsınız.")
            return redirect('cart')

        # Yeni siparişi oluştur
        order = Order.objects.create(
            customer=user,
            total_price=total_price,
            order_status='Pending',
            priority_score=0,  # Gerekirse hesaplayabilirsiniz
            elapsed_time=0
        )

        # Sipariş detaylarını oluştur
        for item in cart:
            product = Product.objects.filter(id=item.get('id')).first()
            if product:
                if item.get('quantity', 1) > 5:  # Ürün miktarını tekrar kontrol et
                    from django.contrib import messages
                    messages.error(request, f"{product.product_name} ürününden en fazla 5 adet alabilirsiniz.")
                    return redirect('cart')

                OrderDetail.objects.create(
                    order=order,
                    product=product,
                    quantity=item.get('quantity', 1),
                    price=Decimal(item.get('price', 0))
                )
        user.save()
        # Sepeti temizle
        request.session['cart'] = []
        return redirect('user_dashboard')

def update_order_priorities():
    """
    Tüm bekleyen siparişlerin dinamik öncelik skorunu günceller.
    """
    pending_orders = Order.objects.filter(order_status='Pending')
    with transaction.atomic():
        for order in pending_orders:
            order.elapsed_time = (now() - order.order_date).total_seconds()
            order.priority_score = calculate_priority_score(order.customer.customer_type, order.elapsed_time)
            order.save()

def admin_order_list(request):
    pending_orders = Order.objects.filter(order_status='Pending').order_by('-priority_score')
    orders_data = [
        {
            'customer_name': order.customer.customer_name,
            'product_name': order.product.product_name,
            'priority_score': order.priority_score,
            'status': order.order_status,
        }
        for order in pending_orders
    ]
    return JsonResponse({'orders': orders_data})

def calculate_priority_score(customer_type, elapsed_time, weight=0.5):
    """
    Dinamik öncelik skorunu hesaplar.
    :param customer_type: Müşteri türü (Premium veya Standard)
    :param elapsed_time: Geçen süre (saniye olarak)
    :param weight: Bekleme süresinin ağırlığı (varsayılan 0.5)
    :return: Dinamik öncelik skoru (float)
    """
    base_priority = 15 if customer_type == 'Premium' else 10
    return base_priority + (elapsed_time * weight)

# Global mutex dictionary
product_locks = {}

# Initialize locks for each product
for product in Product.objects.all():
    product_locks[product.id] = Lock()

def process_order(order):
    order_details = OrderDetail.objects.filter(order=order)
    
    for detail in order_details:
        with product_locks[detail.product.id]:  # Mutex kilidi
            if detail.product.stock >= detail.quantity:
                detail.product.stock -= detail.quantity
                detail.product.save()
            else:
                order.order_status = 'Failed'
                order.save()
                print(f"Sipariş {order.id} başarısız. Yetersiz stok.")
                return  # Yetersiz stok varsa diğer detayları işlememek için çıkış yapıyoruz.

    # Eğer tüm ürünler başarıyla işlendiyse sipariş durumu tamamlandı olarak güncellenir.
    order.order_status = 'Completed'
    order.save()
    print(f"Sipariş {order.id} tamamlandı.")

def approve_all_orders(request):
    if request.method == 'POST':
        orders = Order.objects.filter(order_status='Pending')
        
        for order in orders:
            thread = Thread(target=process_order, args=(order,))
            thread.start()

        return redirect('order_management')
    
def cancel_order(request, order_id):
    """
    Siparişi iptal eder ve veritabanından siler.
    """
    try:
        order = Order.objects.get(id=order_id)
        order.delete()
        return redirect('order_management')  # Sipariş yönetim sayfasına geri dön
    except Order.DoesNotExist:
        return HttpResponse("Sipariş bulunamadı", status=404)
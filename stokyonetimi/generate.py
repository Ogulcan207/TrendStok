import os
import django
import random
from faker import Faker
from django.db import connection
from django.contrib.auth.hashers import make_password

# Django ayarlarını yükleyin
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stokyonetimi.settings')
django.setup()

from isleyis.models import Customer, Product, Order

fake = Faker()

# Tabloyu sıfırlama
def reset_table_sequences():
    with connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE isleyis_order;")
        cursor.execute("TRUNCATE TABLE isleyis_customer;")
        cursor.execute("TRUNCATE TABLE isleyis_product;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

# Mevcut verileri temizleme ve ID sıfırlama
def clear_data():
    print("Mevcut veriler siliniyor ve ID sıfırlanıyor...")
    reset_table_sequences()

# Sahte müşteri verisi oluşturma
def create_customers():
    customer_types = ['Premium', 'Standard']

    for _ in range(random.randint(5, 10)):
        customer_type = 'Premium' if _ < 2 else random.choice(customer_types)  # En az 2 Premium müşteri
        budget = random.randint(500, 3000)
        total_spent = 0.00
        username = fake.user_name()
        password = make_password('test123')  # Şifre hash'lenerek kaydediliyor
        email = fake.email()  # E-posta oluşturuluyor

        Customer.objects.create(
            customer_name=fake.name(),
            username=username,
            password=password,
            email=email,  # E-posta alanı eklendi
            budget=budget,
            customer_type=customer_type,
            total_spent=total_spent
        )

# Sahte ürün verisi oluşturma
def create_products():
    product_data = [
        ("Product1", 500, 100),
        ("Product2", 10, 50),
        ("Product3", 200, 45),
        ("Product4", 75, 75),
        ("Product5", 0, 500),
    ]

    for name, stock, price in product_data:
        Product.objects.create(
            product_name=name,
            stock=stock,
            price=price
        )

# Sahte sipariş verisi oluşturma
def create_orders():
    customers = list(Customer.objects.all())
    products = list(Product.objects.all())

    for _ in range(20):  # 20 sahte sipariş
        customer = random.choice(customers)
        product = random.choice(products)
        quantity = random.randint(1, 5)
        total_price = quantity * product.price

        if customer.budget >= total_price and product.stock >= quantity:
            # Müşteri bütçesi ve stok uygun olduğunda siparişi oluştur
            Order.objects.create(
                customer=customer,
                product=product,
                quantity=quantity,
                total_price=total_price,
                order_status="Completed"
            )

            # Müşteri bütçesini ve toplam harcamasını güncelle
            customer.budget -= total_price
            customer.total_spent += total_price
            customer.save()

            # Ürün stoğunu güncelle
            product.stock -= quantity
            product.save()
        else:
            # Sipariş başarısız
            Order.objects.create(
                customer=customer,
                product=product,
                quantity=quantity,
                total_price=total_price,
                order_status="Failed"
            )

if __name__ == "__main__":
    print("Sahte veriler oluşturuluyor...")
    #clear_data()
    create_customers()
    #create_products()
    #create_orders()
    print("Sahte veriler başarıyla oluşturuldu!")

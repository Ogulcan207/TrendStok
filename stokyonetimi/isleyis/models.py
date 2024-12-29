from django.db import models
from django.contrib.auth.hashers import make_password
from django.utils.timezone import now

# Customers Table
class Customer(models.Model):
    CUSTOMER_TYPES = [
        ('Premium', 'Premium'),
        ('Standard', 'Standard'),
    ]

    customer_name = models.CharField(max_length=100, null=True)
    username = models.CharField(max_length=50, unique=True)  # Kullanıcı adı
    password = models.CharField(max_length=128, null=True)
    email = models.EmailField(max_length=254, unique=True, null=True)  # E-posta alanı eklendi
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    customer_type = models.CharField(max_length=10, choices=CUSTOMER_TYPES, null=True)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)

    def save(self, *args, **kwargs):
        # Şifre hashlenmemişse hashle
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.customer_name

# Products Table
class Product(models.Model):
    product_name = models.CharField(max_length=100)
    stock = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(null=True, blank=True)  # Resim yolu
    description = models.TextField(null=True, blank=True)  # Ürün açıklaması
    def __str__(self):
        return self.product_name


class Order(models.Model):
    ORDER_STATUS = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_status = models.CharField(max_length=10, choices=ORDER_STATUS, default='Pending')
    order_date = models.DateTimeField(auto_now_add=True)
    order_received_time = models.DateTimeField(default=now)
    elapsed_time = models.FloatField(default=0.0)
    priority_score = models.FloatField(default=0.0)

    def __str__(self):
        return f"Order {self.id} - {self.customer.customer_name}"

class OrderDetail(models.Model):
    order = models.ForeignKey(Order, related_name='order_details', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} adet"


# Logs Table
class Log(models.Model):
    LOG_TYPES = [
        ('Info', 'Info'),
        ('Warning', 'Warning'),
        ('Error', 'Error'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    log_date = models.DateTimeField(auto_now_add=True)
    log_type = models.CharField(max_length=10, choices=LOG_TYPES)
    log_details = models.TextField()

    def __str__(self):
        return f"Log {self.id} - {self.log_type}"

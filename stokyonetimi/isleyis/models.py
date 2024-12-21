from django.db import models
from django.contrib.auth.hashers import make_password

# Customers Table
class Customer(models.Model):
    CUSTOMER_TYPES = [
        ('Premium', 'Premium'),
        ('Standard', 'Standard'),
    ]

    customer_name = models.CharField(max_length=100, null=True)
    username = models.CharField(max_length=50, unique=True)  # Kullanıcı adı
    password = models.CharField(max_length=128, null=True)
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
    image = models.ImageField(upload_to='products/', null=True, blank=True)  # Resim yolu

    def __str__(self):
        return self.product_name

# Orders Table
class Order(models.Model):
    ORDER_STATUS = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=10, choices=ORDER_STATUS, default='Pending')

    def __str__(self):
        return f"Order {self.id} - {self.customer.customer_name}"

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

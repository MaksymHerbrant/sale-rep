from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """Категорія товарів"""
    name = models.CharField(max_length=200, verbose_name="Назва")
    description = models.TextField(blank=True, verbose_name="Опис")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар"""
    name = models.CharField(max_length=200, verbose_name="Назва")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="Категорія")
    description = models.TextField(blank=True, verbose_name="Опис")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Ціна")
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Штрихкод/Артикул")
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    @property
    def current_stock(self):
        """Поточний залишок на складі"""
        incoming = Stock.objects.filter(product=self, transaction_type='in').aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        outgoing = Stock.objects.filter(product=self, transaction_type='out').aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        # Корекції можуть бути позитивними (збільшення) або негативними (зменшення)
        adjustments = Stock.objects.filter(product=self, transaction_type='adjustment').aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        return incoming - outgoing + adjustments


class Stock(models.Model):
    """Складські залишки та операції"""
    TRANSACTION_TYPES = [
        ('in', 'Надходження'),
        ('out', 'Продаж'),
        ('adjustment', 'Корекція'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.IntegerField(verbose_name="Кількість")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='in', verbose_name="Тип операції")
    notes = models.TextField(blank=True, verbose_name="Примітки")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Створено користувачем")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")

    class Meta:
        verbose_name = "Складська операція"
        verbose_name_plural = "Складські операції"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.quantity} ({self.get_transaction_type_display()})"

    @property
    def current_balance(self):
        """Поточний баланс після цієї операції"""
        if self.transaction_type == 'in':
            return sum(s.quantity for s in Stock.objects.filter(product=self.product, created_at__lte=self.created_at, transaction_type='in')) - \
                   sum(s.quantity for s in Stock.objects.filter(product=self.product, created_at__lte=self.created_at, transaction_type='out'))
        return None


class Sale(models.Model):
    """Продаж"""
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Касир")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Загальна сума")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата продажу")

    class Meta:
        verbose_name = "Продаж"
        verbose_name_plural = "Продажі"
        ordering = ['-created_at']

    def __str__(self):
        return f"Продаж #{self.id} - {self.total_amount} грн ({self.created_at.strftime('%d.%m.%Y %H:%M')})"

    def calculate_total(self):
        """Розрахувати загальну суму продажу"""
        return sum(item.subtotal for item in self.saleitem_set.all())


class SaleItem(models.Model):
    """Позиція продажу"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, verbose_name="Продаж")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Товар")
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Кількість")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Ціна продажу")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Підсумок")

    class Meta:
        verbose_name = "Позиція продажу"
        verbose_name_plural = "Позиції продажу"

    def __str__(self):
        return f"{self.product.name} x{self.quantity} = {self.subtotal} грн"

    def save(self, *args, **kwargs):
        """Автоматично розраховувати підсумок"""
        self.subtotal = self.quantity * self.price
        super().save(*args, **kwargs)
        # Оновлюємо загальну суму продажу
        self.sale.total_amount = self.sale.calculate_total()
        self.sale.save()

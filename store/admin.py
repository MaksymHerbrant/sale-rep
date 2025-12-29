from django.contrib import admin
from .models import Category, Product, Stock, Sale, SaleItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'barcode', 'is_active', 'current_stock']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'barcode']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'transaction_type', 'created_by', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['product__name']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'price', 'subtotal']
    list_filter = ['sale__created_at']

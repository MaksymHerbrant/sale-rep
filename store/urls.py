from django.urls import path
from . import views

urlpatterns = [
    # Головна
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    
    # Категорії
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Товари
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Склад
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/create/', views.stock_create, name='stock_create'),
    
    # Продажі
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/create/', views.sale_create, name='sale_create'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/receipt/pdf/', views.sale_receipt_pdf, name='sale_receipt_pdf'),
    
    # Звіти та аналітика
    path('reports/', views.reports_view, name='reports'),
    path('reports/sales/pdf/', views.sales_report_pdf, name='sales_report_pdf'),
    path('api/analytics/', views.analytics_data, name='analytics_data'),
    path('api/product/<int:pk>/price/', views.product_price_api, name='product_price_api'),
    
    # Користувачі
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
]


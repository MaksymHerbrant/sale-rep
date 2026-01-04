"""
URL patterns для Class-Based Views
Використовує принципи ООП
"""
from django.urls import path
from . import views as views

urlpatterns = [
    # Головна
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Категорії
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Товари
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Склад
    path('stock/', views.StockListView.as_view(), name='stock_list'),
    path('stock/create/', views.StockCreateView.as_view(), name='stock_create'),
    
    # Продажі
    path('sales/', views.SaleListView.as_view(), name='sale_list'),
    path('sales/create/', views.SaleCreateView.as_view(), name='sale_create'),
    path('sales/<int:pk>/', views.SaleDetailView.as_view(), name='sale_detail'),
    path('sales/<int:pk>/receipt/pdf/', views.SaleReceiptPDFView.as_view(), name='sale_receipt_pdf'),
    
    # Звіти та аналітика
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/sales/pdf/', views.SalesReportPDFView.as_view(), name='sales_report_pdf'),
    path('api/analytics/', views.AnalyticsDataView.as_view(), name='analytics_data'),
    path('api/product/<int:pk>/price/', views.ProductPriceAPIView.as_view(), name='product_price_api'),
    
    # Користувачі
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
]


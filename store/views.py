"""
Class-Based Views для системи обліку товарів
Використовує принципи ООП: наслідування, інкапсуляція, поліморфізм
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.template.loader import render_to_string
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, 
    DetailView, TemplateView, View
)
from django.urls import reverse_lazy
from datetime import datetime, timedelta
import json
import subprocess
import os
from django.conf import settings
from io import BytesIO
import base64

try:
    if os.path.exists('/opt/homebrew/lib'):
        os.environ.setdefault('DYLD_LIBRARY_PATH', '/opt/homebrew/lib')
    from weasyprint import HTML
except ImportError:
    HTML = None
except Exception as e:
    HTML = None
    import logging
    logging.warning(f'WeasyPrint не може бути імпортований: {e}')

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError:
    plt = None

from .models import Category, Product, Stock, Sale, SaleItem
from .forms import (
    UserRegistrationForm, CategoryForm, ProductForm, 
    StockForm, SaleItemForm
)


# ========== МІКСИНИ ДЛЯ ПЕРЕВІРКИ РОЛЕЙ ==========

class RoleCheckMixin:
    """Базовий міксин для перевірки ролей користувачів"""
    
    @staticmethod
    def is_cashier(user):
        """Перевірка чи користувач касир"""
        return user.groups.filter(name='Касир').exists()
    
    @staticmethod
    def is_admin(user):
        """Перевірка чи користувач адміністратор"""
        return user.groups.filter(name='Адміністратор').exists() or user.is_superuser
    
    @staticmethod
    def is_manager(user):
        """Перевірка чи користувач керівник"""
        return user.groups.filter(name='Керівник').exists() or user.is_superuser


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin, RoleCheckMixin):
    """Міксин для перевірки прав адміністратора"""
    
    def test_func(self):
        return self.is_admin(self.request.user)


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin, RoleCheckMixin):
    """Міксин для перевірки прав керівника"""
    
    def test_func(self):
        return self.is_manager(self.request.user)


class CashierRequiredMixin(LoginRequiredMixin, UserPassesTestMixin, RoleCheckMixin):
    """Міксин для перевірки прав касира"""
    
    def test_func(self):
        return self.is_cashier(self.request.user)


class StaffOrManagerMixin(LoginRequiredMixin, UserPassesTestMixin, RoleCheckMixin):
    """Міксин для перевірки прав адміна або керівника"""
    
    def test_func(self):
        user = self.request.user
        return self.is_admin(user) or self.is_manager(user)


class CashierOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin, RoleCheckMixin):
    """Міксин для перевірки прав касира або адміна"""
    
    def test_func(self):
        user = self.request.user
        return self.is_cashier(user) or self.is_admin(user)


class AllRolesMixin(LoginRequiredMixin, UserPassesTestMixin, RoleCheckMixin):
    """Міксин для перевірки прав касира, адміна або керівника"""
    
    def test_func(self):
        user = self.request.user
        return self.is_cashier(user) or self.is_admin(user) or self.is_manager(user)


# ========== АВТЕНТИФІКАЦІЯ ==========

class LoginView(View):
    """Клас для обробки входу користувача"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'store/login.html')
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Невірний логін або пароль')
            return render(request, 'store/login.html')


class LogoutView(LoginRequiredMixin, View):
    """Клас для обробки виходу користувача"""
    
    def post(self, request):
        logout(request)
        messages.success(request, 'Ви успішно вийшли з системи')
        return redirect('login')
    
    def get(self, request):
        return self.post(request)


class RegisterView(View):
    """Клас для реєстрації (застаріла - використовується user_create)"""
    
    def get(self, request):
        messages.info(request, 'Реєстрація доступна тільки для адміністраторів')
        return redirect('login')


# ========== DASHBOARD ==========

class DashboardView(LoginRequiredMixin, RoleCheckMixin, TemplateView):
    """Клас для головної сторінки після входу"""
    template_name = 'store/dashboard_admin.html'
    
    def get_template_names(self):
        """Вибір шаблону залежно від ролі користувача"""
        user = self.request.user
        if self.is_manager(user):
            return ['store/dashboard_manager.html']
        elif self.is_admin(user):
            return ['store/dashboard_admin.html']
        else:
            return ['store/dashboard_cashier.html']
    
    def get_context_data(self, **kwargs):
        """Отримання контексту залежно від ролі"""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if self.is_manager(user):
            context.update(self._get_manager_context())
        elif self.is_admin(user):
            context.update(self._get_admin_context())
        else:
            context.update(self._get_cashier_context())
        
        return context
    
    def _get_manager_context(self):
        """Контекст для керівника"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        sales_today = Sale.objects.filter(created_at__date=today).aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        
        sales_week = Sale.objects.filter(created_at__date__gte=week_ago).aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        
        return {
            'sales_today': sales_today,
            'sales_week': sales_week,
        }
    
    def _get_admin_context(self):
        """Контекст для адміністратора"""
        products_count = Product.objects.count()
        categories_count = Category.objects.count()
        low_stock_products = []
        
        for product in Product.objects.filter(is_active=True):
            stock = product.current_stock
            if stock < 10:
                low_stock_products.append({'product': product, 'stock': stock})
        
        return {
            'products_count': products_count,
            'categories_count': categories_count,
            'low_stock_products': low_stock_products[:5],
        }
    
    def _get_cashier_context(self):
        """Контекст для касира"""
        today = timezone.now().date()
        sales_today = Sale.objects.filter(
            user=self.request.user, 
            created_at__date=today
        )
        return {'sales_today': sales_today}


# ========== КАТЕГОРІЇ (CRUD) ==========

class CategoryListView(AdminRequiredMixin, ListView):
    """Клас для відображення списку категорій"""
    model = Category
    template_name = 'store/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class CategoryCreateView(AdminRequiredMixin, CreateView):
    """Клас для створення категорії"""
    model = Category
    form_class = CategoryForm
    template_name = 'store/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Створити категорію'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Категорію створено успішно!')
        return super().form_valid(form)


class CategoryUpdateView(AdminRequiredMixin, UpdateView):
    """Клас для редагування категорії"""
    model = Category
    form_class = CategoryForm
    template_name = 'store/category_form.html'
    success_url = reverse_lazy('category_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редагувати категорію'
        context['category'] = self.get_object()
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Категорію оновлено успішно!')
        return super().form_valid(form)


class CategoryDeleteView(AdminRequiredMixin, DeleteView):
    """Клас для видалення категорії"""
    model = Category
    template_name = 'store/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Категорію видалено!')
        return super().delete(request, *args, **kwargs)


# ========== ТОВАРИ (CRUD) ==========

class ProductListView(StaffOrManagerMixin, ListView):
    """Клас для відображення списку товарів"""
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        queryset = Product.objects.select_related('category').all()
        search = self.request.GET.get('search', '')
        category_id = self.request.GET.get('category', '')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(barcode__icontains=search)
            )
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search'] = self.request.GET.get('search', '')
        context['category_id'] = self.request.GET.get('category', '')
        context['can_edit'] = self.is_admin(self.request.user)
        return context


class ProductCreateView(AdminRequiredMixin, CreateView):
    """Клас для створення товару"""
    model = Product
    form_class = ProductForm
    template_name = 'store/product_form.html'
    success_url = reverse_lazy('product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Створити товар'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Товар створено успішно!')
        return super().form_valid(form)


class ProductUpdateView(AdminRequiredMixin, UpdateView):
    """Клас для редагування товару"""
    model = Product
    form_class = ProductForm
    template_name = 'store/product_form.html'
    success_url = reverse_lazy('product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редагувати товар'
        context['product'] = self.get_object()
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Товар оновлено успішно!')
        return super().form_valid(form)


class ProductDeleteView(AdminRequiredMixin, DeleteView):
    """Клас для видалення товару"""
    model = Product
    template_name = 'store/product_confirm_delete.html'
    success_url = reverse_lazy('product_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Товар видалено!')
        return super().delete(request, *args, **kwargs)


# ========== СКЛАД ==========

class StockListView(StaffOrManagerMixin, ListView):
    """Клас для відображення списку складських операцій"""
    model = Stock
    template_name = 'store/stock_list.html'
    context_object_name = 'stocks'
    
    def get_queryset(self):
        queryset = Stock.objects.select_related('product', 'created_by').all()
        product_id = self.request.GET.get('product', '')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        context['product_id'] = self.request.GET.get('product', '')
        context['can_edit'] = (
            self.is_admin(self.request.user) or 
            self.is_manager(self.request.user)
        )
        context['is_manager'] = (
            self.is_manager(self.request.user) and 
            not self.is_admin(self.request.user)
        )
        return context


class StockCreateView(StaffOrManagerMixin, CreateView):
    """Клас для створення складської операції"""
    model = Stock
    form_class = StockForm
    template_name = 'store/stock_form.html'
    success_url = reverse_lazy('stock_list')
    
    def get_form_kwargs(self):
        """Передача параметрів користувача в форму"""
        kwargs = super().get_form_kwargs()
        is_manager_user = (
            self.is_manager(self.request.user) and 
            not self.is_admin(self.request.user)
        )
        kwargs['user'] = self.request.user
        kwargs['is_manager'] = is_manager_user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_manager_user = (
            self.is_manager(self.request.user) and 
            not self.is_admin(self.request.user)
        )
        context['title'] = (
            'Створити надходження на склад' if is_manager_user 
            else 'Створити складську операцію'
        )
        context['is_manager'] = is_manager_user
        return context
    
    def form_valid(self, form):
        # Додаткова перевірка для керівника
        is_manager_user = (
            self.is_manager(self.request.user) and 
            not self.is_admin(self.request.user)
        )
        
        if is_manager_user:
            transaction_type = form.cleaned_data.get('transaction_type')
            if transaction_type != 'in':
                messages.error(
                    self.request, 
                    'Керівник може створювати тільки надходження на склад'
                )
                return self.form_invalid(form)
        
        stock = form.save(commit=False)
        stock.created_by = self.request.user
        stock.save()
        messages.success(self.request, 'Складську операцію створено успішно!')
        return redirect(self.success_url)


# ========== ПРОДАЖІ ==========

class SaleListView(AllRolesMixin, ListView):
    """Клас для відображення списку продажів"""
    model = Sale
    template_name = 'store/sale_list.html'
    context_object_name = 'sales'
    
    def get_queryset(self):
        queryset = Sale.objects.select_related('user').all()
        
        # Касир бачить тільки свої продажі
        if not (self.is_admin(self.request.user) or 
                self.is_manager(self.request.user)):
            queryset = queryset.filter(user=self.request.user)
        
        # Фільтрація по датах
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        return context


class SaleCreateView(CashierOrAdminMixin, View):
    """Клас для створення продажу"""
    template_name = 'store/sale_create.html'
    
    def get(self, request):
        products = Product.objects.filter(is_active=True).select_related('category')
        return render(request, self.template_name, {'products': products})
    
    def post(self, request):
        sale = Sale.objects.create(user=request.user, total_amount=0)
        
        # Обробка позицій продажу
        items_data = json.loads(request.POST.get('items', '[]'))
        for item_data in items_data:
            product = get_object_or_404(Product, pk=item_data['product_id'])
            quantity = int(item_data['quantity'])
            price = float(item_data['price'])
            
            # Перевірка наявності на складі
            current_stock = product.current_stock
            if quantity > current_stock:
                messages.error(
                    request, 
                    f'Недостатньо товару "{product.name}" на складі. '
                    f'Доступно: {current_stock}'
                )
                sale.delete()
                return redirect('sale_create')
            
            # Створення позиції
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                price=price
            )
            
            # Створення складської операції (списання)
            Stock.objects.create(
                product=product,
                quantity=quantity,
                transaction_type='out',
                notes=f'Продаж #{sale.id}',
                created_by=request.user
            )
        
        sale.total_amount = sale.calculate_total()
        sale.save()
        messages.success(request, f'Продаж #{sale.id} створено успішно!')
        return redirect('sale_detail', pk=sale.id)


class SaleDetailView(AllRolesMixin, DetailView):
    """Клас для відображення деталей продажу"""
    model = Sale
    template_name = 'store/sale_detail.html'
    context_object_name = 'sale'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Перевірка доступу
        if not (self.is_admin(self.request.user) or 
                self.is_manager(self.request.user)):
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.saleitem_set.select_related('product').all()
        return context


class SaleReceiptPDFView(AllRolesMixin, DetailView):
    """Клас для генерації PDF чека продажу"""
    model = Sale
    
    def get(self, request, *args, **kwargs):
        if HTML is None:
            messages.error(
                request, 
                'WeasyPrint не встановлено. Встановіть: pip install WeasyPrint'
            )
            return redirect('sale_detail', pk=kwargs['pk'])
        
        try:
            sale = self.get_object()
            
            # Перевірка доступу
            is_cashier_user = self.is_cashier(request.user)
            if is_cashier_user and sale.user != request.user:
                messages.error(request, 'У вас немає доступу до цього чека')
                return redirect('sale_list')
            
            items = sale.saleitem_set.all()
            
            context = {
                'sale': sale,
                'items': items,
                'date': sale.created_at.strftime('%d.%m.%Y'),
                'time': sale.created_at.strftime('%H:%M'),
            }
            
            html_string = render_to_string('store/receipt.html', context)
            html = HTML(string=html_string, base_url=request.build_absolute_uri())
            pdf_file = html.write_pdf()
            
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'inline; filename="receipt_{sale.id}.pdf"'
            )
            return response
        except Exception as e:
            messages.error(request, f'Помилка генерації PDF: {str(e)}')
            return redirect('sale_detail', pk=kwargs['pk'])


# ========== ЗВІТИ ТА АНАЛІТИКА ==========

class ReportsView(ManagerRequiredMixin, TemplateView):
    """Клас для відображення сторінки звітів"""
    template_name = 'store/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Отримуємо дати
        date_from_str = self.request.GET.get('date_from', '')
        date_to_str = self.request.GET.get('date_to', '')
        
        if not date_from_str:
            date_from_str = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to_str:
            date_to_str = timezone.now().strftime('%Y-%m-%d')
        
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            date_from = (timezone.now() - timedelta(days=30)).date()
            date_to = timezone.now().date()
            date_from_str = date_from.strftime('%Y-%m-%d')
            date_to_str = date_to.strftime('%Y-%m-%d')
        
        # Фільтруємо продажі
        sales = Sale.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )
        total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
        total_count = sales.count()
        average_check = (total_revenue / total_count) if total_count > 0 else 0
        
        # Отримуємо аналітику з C++ модуля
        cpp_data = self._call_cpp_analytics(date_from_str, date_to_str)
        
        # Топ товарів
        top_products = self._get_top_products(cpp_data, date_from, date_to)
        
        # Залишки на складі
        stock_products = self._get_stock_products()
        
        context.update({
            'date_from': date_from_str,
            'date_to': date_to_str,
            'total_revenue': total_revenue,
            'total_count': total_count,
            'average_check': average_check,
            'top_products': top_products,
            'stock_products': stock_products,
            'cpp_data': cpp_data if 'error' not in cpp_data else None,
        })
        
        return context
    
    def _get_top_products(self, cpp_data, date_from, date_to):
        """Отримання топ товарів"""
        top_products = []
        if 'error' not in cpp_data and 'top_products_by_revenue' in cpp_data:
            for item in cpp_data['top_products_by_revenue'][:10]:
                top_products.append({
                    'product__name': item['product_name'],
                    'total_quantity': item.get('quantity', 0),
                    'total_amount': item['revenue']
                })
        else:
            top_products_raw = SaleItem.objects.filter(
                sale__created_at__date__gte=date_from,
                sale__created_at__date__lte=date_to
            ).values('product__name').annotate(
                total_quantity=Sum('quantity'),
                total_amount=Sum('subtotal')
            ).order_by('-total_amount')[:10]
            
            for item in top_products_raw:
                top_products.append({
                    'product__name': item['product__name'],
                    'total_quantity': item['total_quantity'],
                    'total_amount': float(item['total_amount'] or 0)
                })
        return top_products
    
    def _get_stock_products(self):
        """Отримання залишків на складі"""
        stock_products = []
        for product in Product.objects.filter(is_active=True):
            stock = product.current_stock
            stock_products.append({
                'product': product,
                'stock': stock,
                'value': stock * product.price
            })
        stock_products.sort(key=lambda x: x['value'], reverse=True)
        return stock_products
    
    def _call_cpp_analytics(self, date_from_str, date_to_str):
        """Виклик C++ модуля для аналітики"""
        return call_cpp_analytics(date_from_str, date_to_str)


class SalesReportPDFView(StaffOrManagerMixin, View):
    """Клас для генерації PDF звіту про продажі"""
    
    def get(self, request):
        if HTML is None:
            messages.error(
                request, 
                'WeasyPrint не встановлено. Встановіть: pip install WeasyPrint'
            )
            return redirect('reports')
        
        if plt is None:
            messages.error(
                request, 
                'matplotlib не встановлено. Встановіть: pip install matplotlib'
            )
            return redirect('reports')
        
        # Отримуємо дати
        date_from_str = request.GET.get(
            'start', 
            (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        )
        date_to_str = request.GET.get('end', timezone.now().strftime('%Y-%m-%d'))
        
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Невірний формат дати')
            return redirect('reports')
        
        # Продажі за період
        sales = Sale.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        )
        
        # Отримуємо аналітику з C++
        cpp_data = call_cpp_analytics(date_from_str, date_to_str)
        
        # Обробка даних для PDF
        context = self._prepare_pdf_context(sales, cpp_data, date_from, date_to)
        
        # Генерація графіка
        try:
            chart_image = self._generate_chart(cpp_data, sales, date_from, date_to)
            context['chart_image'] = chart_image
        except Exception as e:
            # Якщо не вдалося згенерувати графік, використовуємо порожній рядок
            context['chart_image'] = ''
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Помилка генерації графіка: {str(e)}')
        
        # Генерація PDF
        try:
            html_string = render_to_string('store/report.html', context)
            html = HTML(string=html_string, base_url=request.build_absolute_uri())
            pdf_file = html.write_pdf()
            
            response = HttpResponse(pdf_file, content_type='application/pdf')
            filename = f"sales_report_{date_from_str}_{date_to_str}.pdf"
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Помилка генерації PDF: {str(e)}')
            messages.error(request, f'Помилка генерації PDF: {str(e)}')
            return redirect('reports')
    
    def _prepare_pdf_context(self, sales, cpp_data, date_from, date_to):
        """Підготовка контексту для PDF"""
        # Реалізація аналогічна до оригінальної функції
        # (скорочено для читабельності)
        if 'error' not in cpp_data:
            top_by_amount = [
                {
                    'product_name': item.get('product_name', ''),
                    'product__name': item.get('product_name', ''),
                    'revenue': item.get('revenue', 0),
                    'total_amount': item.get('revenue', 0),
                    'total_quantity': item.get('quantity', 0)
                }
                for item in cpp_data.get('top_products_by_revenue', [])
            ]
            
            top_by_quantity = [
                {
                    'product_name': item.get('product_name', ''),
                    'product__name': item.get('product_name', ''),
                    'quantity': item.get('quantity', 0),
                    'total_quantity': item.get('quantity', 0),
                    'total_amount': float(item.get('revenue', 0))
                }
                for item in cpp_data.get('top_products_by_quantity', [])
            ]
            
            stats = cpp_data.get('statistics', {})
            total_revenue = stats.get('total_revenue', 0)
            total_count = stats.get('total_sales', sales.count())
            average_check = stats.get('mean', 0)
        else:
            # Резервний варіант
            total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
            total_count = sales.count()
            average_check = total_revenue / total_count if total_count > 0 else 0
            
            top_by_amount_raw = SaleItem.objects.filter(
                sale__created_at__date__gte=date_from,
                sale__created_at__date__lte=date_to
            ).values('product__name').annotate(
                total_amount=Sum('subtotal'),
                total_quantity=Sum('quantity')
            ).order_by('-total_amount')
            
            top_by_amount = [
                {
                    'product__name': item['product__name'],
                    'product_name': item['product__name'],
                    'total_amount': float(item['total_amount'] or 0),
                    'revenue': float(item['total_amount'] or 0),
                    'total_quantity': item['total_quantity']
                }
                for item in top_by_amount_raw
            ]
            
            top_by_quantity_raw = SaleItem.objects.filter(
                sale__created_at__date__gte=date_from,
                sale__created_at__date__lte=date_to
            ).values('product__name').annotate(
                total_amount=Sum('subtotal'),
                total_quantity=Sum('quantity')
            ).order_by('-total_quantity')
            
            top_by_quantity = [
                {
                    'product__name': item['product__name'],
                    'product_name': item['product__name'],
                    'total_quantity': item['total_quantity'],
                    'quantity': item['total_quantity'],
                    'total_amount': float(item['total_amount'] or 0)
                }
                for item in top_by_quantity_raw
            ]
            
            # Статистики
            sale_amounts = [float(x) for x in sales.values_list('total_amount', flat=True) if x and x > 0]
            if sale_amounts:
                sale_amounts.sort()
                n = len(sale_amounts)
                mean = sum(sale_amounts) / n
                median = (sale_amounts[n // 2] if n % 2 == 1 
                         else (sale_amounts[n // 2 - 1] + sale_amounts[n // 2]) / 2)
                variance = sum((x - mean) ** 2 for x in sale_amounts) / n
                std_dev = variance ** 0.5
                min_val = min(sale_amounts)
                max_val = max(sale_amounts)
            else:
                mean = median = std_dev = min_val = max_val = 0
            
            cpp_data['statistics'] = {
                'total_revenue': float(total_revenue),
                'mean': float(mean),
                'median': float(median),
                'std_dev': float(std_dev),
                'min': float(min_val),
                'max': float(max_val),
                'total_sales': total_count
            }
        
        # Залишки на складі
        stock_data = []
        for product in Product.objects.filter(is_active=True):
            incoming = Stock.objects.filter(
                product=product, transaction_type='in'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            outgoing = Stock.objects.filter(
                product=product, transaction_type='out'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            adjustments = Stock.objects.filter(
                product=product, transaction_type='adjustment'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            balance = incoming - outgoing + adjustments
            stock_data.append({
                'product': product,
                'balance': balance,
                'value': float(balance * product.price) if balance > 0 else 0
            })
        
        stock_data.sort(key=lambda x: x['value'], reverse=True)
        
        return {
            'date_from': date_from.strftime('%d.%m.%Y'),
            'date_to': date_to.strftime('%d.%m.%Y'),
            'total_revenue': float(total_revenue),
            'total_count': total_count,
            'average_check': float(average_check),
            'top_by_amount': top_by_amount,
            'top_by_quantity': top_by_quantity,
            'stock_data': stock_data,
            'cpp_stats': cpp_data.get('statistics', {}),
            'abc_analysis': cpp_data.get('abc_analysis', []) if 'error' not in cpp_data else [],
            'category_shares': cpp_data.get('category_shares', []) if 'error' not in cpp_data else [],
        }
    
    def _generate_chart(self, cpp_data, sales, date_from, date_to):
        """Генерація графіка виручки по днях"""
        if 'error' not in cpp_data and 'daily_revenue' in cpp_data:
            dates = []
            revenues = []
            for item in cpp_data['daily_revenue']:
                date_str = item.get('date', '')
                # Пропускаємо порожні або невалідні дати
                if date_str and date_str != 'date' and len(date_str) >= 10:
                    try:
                        dates.append(datetime.strptime(date_str[:10], '%Y-%m-%d'))
                        revenues.append(item.get('revenue', 0))
                    except (ValueError, TypeError):
                        continue
        else:
            daily_revenue = sales.extra(
                select={'day': 'date(created_at)'}
            ).values('day').annotate(
                revenue=Sum('total_amount')
            ).order_by('day')
            
            dates = []
            revenues = []
            for item in daily_revenue:
                try:
                    dates.append(datetime.strptime(item['day'], '%Y-%m-%d'))
                    revenues.append(float(item['revenue'] or 0))
                except (ValueError, TypeError, KeyError):
                    continue
        
        # Якщо немає даних для графіка
        if not dates or not revenues:
            return ''
        
        plt.figure(figsize=(10, 5))
        plt.plot(dates, revenues, marker='o', linewidth=2, markersize=6)
        plt.title('Виручка по днях', fontsize=14, fontweight='bold')
        plt.xlabel('Дата', fontsize=12)
        plt.ylabel('Виручка (грн)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return image_base64


class AnalyticsDataView(ManagerRequiredMixin, View):
    """Клас для API отримання даних для аналітики"""
    
    def get(self, request):
        date_from_str = request.GET.get(
            'date_from', 
            (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        )
        date_to_str = request.GET.get('date_to', timezone.now().strftime('%Y-%m-%d'))
        
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            date_from = (timezone.now() - timedelta(days=30)).date()
            date_to = timezone.now().date()
            date_from_str = date_from.strftime('%Y-%m-%d')
            date_to_str = date_to.strftime('%Y-%m-%d')
        
        # Виклик C++ модуля
        cpp_data = call_cpp_analytics(date_from_str, date_to_str)
        
        if 'error' in cpp_data:
            # Резервний варіант
            sales_by_date = Sale.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to
            ).extra(
                select={'day': 'date(created_at)'}
            ).values('day').annotate(
                total=Sum('total_amount'),
                count=Count('id')
            ).order_by('day')
            
            sales_by_date_list = [
                {
                    'day': item['day'],
                    'total': float(item['total'] or 0),
                    'count': item['count']
                }
                for item in sales_by_date
            ]
            
            category_sales = SaleItem.objects.filter(
                sale__created_at__date__gte=date_from,
                sale__created_at__date__lte=date_to
            ).values('product__category__name').annotate(
                total=Sum('subtotal')
            ).order_by('-total')
            
            category_sales_list = [
                {
                    'product__category__name': item['product__category__name'],
                    'total': float(item['total'] or 0)
                }
                for item in category_sales
            ]
            
            return JsonResponse({
                'sales_by_date': sales_by_date_list,
                'category_sales': category_sales_list,
                'cpp_error': cpp_data.get('error'),
            })
        
        # Використовуємо дані з C++
        sales_by_date_list = [
            {
                'day': item['date'],
                'total': item['revenue'],
                'count': 0
            }
            for item in cpp_data.get('daily_revenue', [])
        ]
        
        category_sales_list = [
            {
                'product__category__name': item['category'],
                'total': item['share']
            }
            for item in cpp_data.get('category_shares', [])
        ]
        
        return JsonResponse({
            'sales_by_date': sales_by_date_list,
            'category_sales': category_sales_list,
            'daily_revenue': cpp_data.get('daily_revenue', []),
            'weekly_revenue': cpp_data.get('weekly_revenue', []),
            'monthly_revenue': cpp_data.get('monthly_revenue', []),
            'top_products_by_revenue': cpp_data.get('top_products_by_revenue', []),
            'top_products_by_quantity': cpp_data.get('top_products_by_quantity', []),
            'category_shares': cpp_data.get('category_shares', []),
            'statistics': cpp_data.get('statistics', {}),
            'abc_analysis': cpp_data.get('abc_analysis', []),
        })


class ProductPriceAPIView(LoginRequiredMixin, DetailView):
    """Клас для API отримання ціни товару"""
    model = Product
    
    def get(self, request, *args, **kwargs):
        product = self.get_object()
        return JsonResponse({
            'price': float(product.price),
            'stock': product.current_stock,
        })


# ========== КЕРУВАННЯ КОРИСТУВАЧАМИ ==========

class UserListView(AdminRequiredMixin, ListView):
    """Клас для відображення списку користувачів"""
    model = User
    template_name = 'store/user_list.html'
    context_object_name = 'users'


class UserCreateView(AdminRequiredMixin, CreateView):
    """Клас для створення нового користувача"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'store/user_create.html'
    success_url = reverse_lazy('user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Додати користувача'
        return context
    
    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f'Користувач "{user.username}" успішно створений!')
        return super().form_valid(form)


class UserUpdateView(AdminRequiredMixin, UpdateView):
    """Клас для редагування користувача та ролей"""
    model = User
    template_name = 'store/user_edit.html'
    fields = ['first_name', 'last_name', 'email', 'is_staff', 'is_superuser']
    success_url = reverse_lazy('user_list')
    
    def post(self, request, *args, **kwargs):
        user = self.get_object()
        try:
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.is_staff = request.POST.get('is_staff') == 'on'
            user.is_superuser = request.POST.get('is_superuser') == 'on'
            user.save()
            
            # Оновлення груп
            user.groups.clear()
            for group_name in request.POST.getlist('groups'):
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                except Group.DoesNotExist:
                    messages.warning(request, f'Група "{group_name}" не знайдена')
            
            messages.success(request, 'Користувача оновлено!')
            return redirect(self.success_url)
        except Exception as e:
            messages.error(request, f'Помилка при оновленні користувача: {str(e)}')
            return self.get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.all()
        return context


# ========== ДОПОМІЖНІ ФУНКЦІЇ ==========

def call_cpp_analytics(date_from_str, date_to_str):
    """Виклик C++ модуля для аналітики - ядро обчислень (ООП версія)"""
    try:
        # Спробуємо використати ООП версію, якщо вона існує
        cpp_executable_oop = os.path.join(settings.BASE_DIR, 'cpp_analytics', 'analytics_oop')
        cpp_executable = os.path.join(settings.BASE_DIR, 'cpp_analytics', 'analytics')
        
        # Перевіряємо чи існує ООП версія
        if os.path.exists(cpp_executable_oop):
            cpp_executable = cpp_executable_oop
        elif not os.path.exists(cpp_executable):
            return {'error': 'C++ модуль не знайдено'}
        
        if not os.path.exists(cpp_executable):
            return {'error': 'C++ модуль не знайдено'}
        
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            date_from = (timezone.now() - timedelta(days=30)).date()
            date_to = timezone.now().date()
        
        # ОДИН запит до БД
        sales = Sale.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).prefetch_related('saleitem_set__product__category')
        
        # Формуємо JSON
        input_data = {'sales': []}
        
        for sale in sales:
            sale_data = {
                'id': sale.id,
                'date': sale.created_at.strftime('%Y-%m-%d'),
                'total_amount': float(sale.total_amount),
                'items': []
            }
            
            for item in sale.saleitem_set.all():
                sale_data['items'].append({
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'category_id': item.product.category.id,
                    'category_name': item.product.category.name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'subtotal': float(item.subtotal),
                })
            
            input_data['sales'].append(sale_data)
        
        # Виклик C++ програми
        result = subprocess.run(
            [cpp_executable],
            input=json.dumps(input_data, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {'error': result.stderr or 'Помилка виконання C++ модуля'}
    
    except json.JSONDecodeError as e:
        return {'error': f'Помилка парсингу JSON від C++: {str(e)}'}
    except Exception as e:
        return {'error': str(e)}
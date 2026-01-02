from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.template.loader import render_to_string
from datetime import datetime, timedelta
import json
import subprocess
import os
from django.conf import settings
from io import BytesIO
import base64

try:
    import os
    # Налаштування для WeasyPrint на macOS
    if os.path.exists('/opt/homebrew/lib'):
        os.environ.setdefault('DYLD_LIBRARY_PATH', '/opt/homebrew/lib')
    from weasyprint import HTML
except ImportError:
    HTML = None
except Exception as e:
    # Якщо є інші помилки (наприклад, з бібліотеками)
    HTML = None
    import logging
    logging.warning(f'WeasyPrint не може бути імпортований: {e}')

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError:
    plt = None

from .models import Category, Product, Stock, Sale, SaleItem
from .forms import UserRegistrationForm, CategoryForm, ProductForm, StockForm, SaleItemForm


def is_cashier(user):
    """Перевірка чи користувач касир"""
    return user.groups.filter(name='Касир').exists() or user.is_staff


def is_admin(user):
    """Перевірка чи користувач адміністратор"""
    return user.groups.filter(name='Адміністратор').exists() or user.is_superuser


def is_manager(user):
    """Перевірка чи користувач керівник"""
    return user.groups.filter(name='Керівник').exists() or user.is_superuser


def login_view(request):
    """Вхід користувача"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
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


def register_view(request):
    """Реєстрація користувача (застаріла - використовується user_create)"""
    # Реєстрація тепер доступна тільки через адмін-панель
    messages.info(request, 'Реєстрація доступна тільки для адміністраторів')
    return redirect('login')


@login_required
def dashboard_view(request):
    """Головна сторінка після входу"""
    user = request.user
    
    if is_manager(user):
        # Для керівника - статистика
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
        
        context = {
            'sales_today': sales_today,
            'sales_week': sales_week,
        }
        return render(request, 'store/dashboard_manager.html', context)
    
    elif is_admin(user):
        # Для адміністратора - загальна інформація
        products_count = Product.objects.count()
        categories_count = Category.objects.count()
        low_stock_products = []
        for product in Product.objects.filter(is_active=True):
            stock = product.current_stock
            if stock < 10:
                low_stock_products.append({'product': product, 'stock': stock})
        
        context = {
            'products_count': products_count,
            'categories_count': categories_count,
            'low_stock_products': low_stock_products[:5],
        }
        return render(request, 'store/dashboard_admin.html', context)
    
    else:
        # Для касира - його продажі
        today = timezone.now().date()
        sales_today = Sale.objects.filter(user=user, created_at__date=today)
        context = {
            'sales_today': sales_today,
        }
        return render(request, 'store/dashboard_cashier.html', context)


# ========== КАТЕГОРІЇ ==========
@login_required
@user_passes_test(is_admin)
def category_list(request):
    """Список категорій"""
    categories = Category.objects.all()
    search = request.GET.get('search', '')
    if search:
        categories = categories.filter(name__icontains=search)
    return render(request, 'store/category_list.html', {'categories': categories, 'search': search})


@login_required
@user_passes_test(is_admin)
def category_create(request):
    """Створення категорії"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категорію створено успішно!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'store/category_form.html', {'form': form, 'title': 'Створити категорію'})


@login_required
@user_passes_test(is_admin)
def category_edit(request, pk):
    """Редагування категорії"""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категорію оновлено успішно!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'store/category_form.html', {'form': form, 'title': 'Редагувати категорію', 'category': category})


@login_required
@user_passes_test(is_admin)
def category_delete(request, pk):
    """Видалення категорії"""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Категорію видалено!')
        return redirect('category_list')
    return render(request, 'store/category_confirm_delete.html', {'category': category})


# ========== ТОВАРИ ==========
@login_required
@user_passes_test(is_admin)
def product_list(request):
    """Список товарів"""
    products = Product.objects.select_related('category').all()
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    
    if search:
        products = products.filter(Q(name__icontains=search) | Q(barcode__icontains=search))
    if category_id:
        products = products.filter(category_id=category_id)
    
    categories = Category.objects.all()
    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'search': search,
        'category_id': category_id,
    })


@login_required
@user_passes_test(is_admin)
def product_create(request):
    """Створення товару"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар створено успішно!')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'store/product_form.html', {'form': form, 'title': 'Створити товар'})


@login_required
@user_passes_test(is_admin)
def product_edit(request, pk):
    """Редагування товару"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар оновлено успішно!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/product_form.html', {'form': form, 'title': 'Редагувати товар', 'product': product})


@login_required
@user_passes_test(is_admin)
def product_delete(request, pk):
    """Видалення товару"""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Товар видалено!')
        return redirect('product_list')
    return render(request, 'store/product_confirm_delete.html', {'product': product})


# ========== СКЛАД ==========
@login_required
@user_passes_test(is_admin)
def stock_list(request):
    """Список складських операцій"""
    stocks = Stock.objects.select_related('product', 'created_by').all()
    product_id = request.GET.get('product', '')
    
    if product_id:
        stocks = stocks.filter(product_id=product_id)
    
    products = Product.objects.all()
    return render(request, 'store/stock_list.html', {
        'stocks': stocks,
        'products': products,
        'product_id': product_id,
    })


@login_required
@user_passes_test(is_admin)
def stock_create(request):
    """Створення складської операції"""
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            stock = form.save(commit=False)
            stock.created_by = request.user
            stock.save()
            messages.success(request, 'Складську операцію створено успішно!')
            return redirect('stock_list')
    else:
        form = StockForm()
    return render(request, 'store/stock_form.html', {'form': form, 'title': 'Створити складську операцію'})


# ========== ПРОДАЖІ ==========
@login_required
@user_passes_test(is_cashier)
def sale_list(request):
    """Список продажів"""
    sales = Sale.objects.select_related('user').all()
    
    # Касир бачить тільки свої продажі
    if not is_admin(request.user) and not is_manager(request.user):
        sales = sales.filter(user=request.user)
    
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    
    return render(request, 'store/sale_list.html', {
        'sales': sales,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
@user_passes_test(is_cashier)
def sale_create(request):
    """Створення продажу"""
    if request.method == 'POST':
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
                messages.error(request, f'Недостатньо товару "{product.name}" на складі. Доступно: {current_stock}')
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
    
    products = Product.objects.filter(is_active=True).select_related('category')
    return render(request, 'store/sale_create.html', {'products': products})


@login_required
@user_passes_test(is_cashier)
def sale_detail(request, pk):
    """Деталі продажу"""
    sale = get_object_or_404(Sale, pk=pk)
    
    # Перевірка доступу
    if not is_admin(request.user) and not is_manager(request.user) and sale.user != request.user:
        messages.error(request, 'Немає доступу до цього продажу')
        return redirect('sale_list')
    
    items = sale.saleitem_set.select_related('product').all()
    return render(request, 'store/sale_detail.html', {'sale': sale, 'items': items})


@login_required
def sale_receipt_pdf(request, pk):
    """Генерація PDF чека продажу"""
    if HTML is None:
        messages.error(request, 'WeasyPrint не встановлено. Встановіть: pip install WeasyPrint')
        return redirect('sale_detail', pk=pk)
    
    try:
        sale = get_object_or_404(Sale, pk=pk)
        
        # Перевірка доступу: Касир тільки свої продажі, Адмін та Керівник - всі
        user = request.user
        is_cashier_user = user.groups.filter(name='Касир').exists() and not user.is_staff
        if is_cashier_user and sale.user != user:
            messages.error(request, 'У вас немає доступу до цього чека')
            return redirect('sale_list')
        
        # Перевірка чи користувач має доступ (Касир, Адмін або Керівник)
        has_access = (
            is_cashier(user) or 
            is_admin(user) or 
            is_manager(user)
        )
        if not has_access:
            messages.error(request, 'У вас немає доступу до генерації чеків')
            return redirect('dashboard')
        
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
        response['Content-Disposition'] = f'inline; filename="receipt_{sale.id}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Помилка генерації PDF: {str(e)}')
        return redirect('sale_detail', pk=pk)


# ========== ЗВІТИ ==========
@login_required
@user_passes_test(is_manager)
def reports_view(request):
    """Сторінка звітів"""
    # Отримуємо дати з параметрів запиту
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    
    # Якщо дати не передані, використовуємо значення за замовчуванням
    if not date_from_str:
        date_from_str = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to_str:
        date_to_str = timezone.now().strftime('%Y-%m-%d')
    
    # Конвертуємо рядки в date об'єкти
    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # Якщо дати невалідні, використовуємо значення за замовчуванням
        date_from = (timezone.now() - timedelta(days=30)).date()
        date_to = timezone.now().date()
        date_from_str = date_from.strftime('%Y-%m-%d')
        date_to_str = date_to.strftime('%Y-%m-%d')
    
    # Фільтруємо продажі за вибраним періодом
    sales = Sale.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_count = sales.count()
    average_check = (total_revenue / total_count) if total_count > 0 else 0
    
    # Отримуємо аналітику з C++ модуля (ядро обчислень)
    cpp_data = call_cpp_analytics(date_from_str, date_to_str)
    
    # Топ товарів - використовуємо дані з C++
    top_products = []
    if 'error' not in cpp_data and 'top_products_by_revenue' in cpp_data:
        # Використовуємо дані з C++
        for item in cpp_data['top_products_by_revenue'][:10]:
            top_products.append({
                'product__name': item['product_name'],
                'total_quantity': item.get('quantity', 0),  # Тепер отримуємо кількість з C++
                'total_amount': item['revenue']
            })
    else:
        # Резервний варіант через Python ORM
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
    
    # Діагностика (можна видалити після перевірки)
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f'Топ товарів для періоду {date_from} - {date_to}: знайдено {len(top_products)} товарів')
    
    # Залишки на складі
    stock_products = []
    for product in Product.objects.filter(is_active=True):
        stock = product.current_stock
        stock_products.append({
            'product': product,
            'stock': stock,
            'value': stock * product.price
        })
    stock_products.sort(key=lambda x: x['value'], reverse=True)
    
    # Додаємо дані з C++ для відображення в шаблоні
    context = {
        'date_from': date_from_str,
        'date_to': date_to_str,
        'total_revenue': total_revenue,
        'total_count': total_count,
        'average_check': average_check,
        'top_products': top_products,
        'stock_products': stock_products,
        'cpp_data': cpp_data if 'error' not in cpp_data else None,  # Дані з C++ для додаткової аналітики
    }
    return render(request, 'store/reports.html', context)


@login_required
@user_passes_test(lambda u: is_admin(u) or is_manager(u))
def sales_report_pdf(request):
    """Генерація PDF звіту про продажі"""
    if HTML is None:
        messages.error(request, 'WeasyPrint не встановлено. Встановіть: pip install WeasyPrint')
        return redirect('reports')
    
    if plt is None:
        messages.error(request, 'matplotlib не встановлено. Встановіть: pip install matplotlib')
        return redirect('reports')
    
    # Отримуємо дати з параметрів
    date_from_str = request.GET.get('start', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
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
    
    # Отримуємо аналітику з C++ модуля (ядро обчислень)
    cpp_data = call_cpp_analytics(date_from_str, date_to_str)
    
    # Використовуємо дані з C++ для топ товарів та статистик
    if 'error' not in cpp_data:
        # Топ товарів з C++
        top_by_amount = []
        for item in cpp_data.get('top_products_by_revenue', []):
            top_by_amount.append({
                'product_name': item.get('product_name', ''),
                'product__name': item.get('product_name', ''),  # Для сумісності з шаблоном
                'revenue': item.get('revenue', 0),
                'total_amount': item.get('revenue', 0),  # Для сумісності з шаблоном
                'total_quantity': item.get('quantity', 0)  # Тепер отримуємо кількість з C++
            })
        
        top_by_quantity = []
        for item in cpp_data.get('top_products_by_quantity', []):
            top_by_quantity.append({
                'product_name': item.get('product_name', ''),
                'product__name': item.get('product_name', ''),  # Для сумісності з шаблоном
                'quantity': item.get('quantity', 0),
                'total_quantity': item.get('quantity', 0),  # Для сумісності з шаблоном
                'total_amount': float(item.get('revenue', 0))  # Тепер отримуємо виручку з C++
            })
        
        # Статистики з C++
        stats = cpp_data.get('statistics', {})
        total_revenue_from_stats = stats.get('total_revenue', 0)
        if total_revenue_from_stats == 0:
            # Якщо C++ не повернув, рахуємо з sales
            total_revenue_from_stats = sales.aggregate(total=Sum('total_amount'))['total'] or 0
        total_count = stats.get('total_sales', sales.count())
        average_check = stats.get('mean', (total_revenue_from_stats / total_count if total_count > 0 else 0))
    else:
        # Резервний варіант через Python ORM
        total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
        total_count = sales.count()
        average_check = total_revenue / total_count if total_count > 0 else 0
        total_revenue_from_stats = total_revenue  # Для уніфікації
        
        # Розрахунок статистик (медіана, std dev, min, max) для резервного варіанту
        sale_amounts = list(sales.values_list('total_amount', flat=True))
        if sale_amounts:
            sale_amounts = [float(x) for x in sale_amounts if x]
            sale_amounts.sort()
            n = len(sale_amounts)
            if n > 0:
                mean = sum(sale_amounts) / n
                median = sale_amounts[n // 2] if n % 2 == 1 else (sale_amounts[n // 2 - 1] + sale_amounts[n // 2]) / 2
                variance = sum((x - mean) ** 2 for x in sale_amounts) / n if n > 0 else 0
                std_dev = variance ** 0.5
                min_val = min(sale_amounts)
                max_val = max(sale_amounts)
            else:
                mean = median = std_dev = min_val = max_val = 0
        else:
            mean = median = std_dev = min_val = max_val = 0
        
        # Додаємо статистики до cpp_data для уніфікації (завжди, навіть якщо C++ не працює)
        cpp_data['statistics'] = {
            'total_revenue': float(total_revenue),
            'mean': float(mean),
            'median': float(median),
            'std_dev': float(std_dev),
            'min': float(min_val),
            'max': float(max_val),
            'total_sales': total_count
        }
        
        top_by_amount_raw = SaleItem.objects.filter(
            sale__created_at__date__gte=date_from,
            sale__created_at__date__lte=date_to
        ).values('product__name').annotate(
            total_amount=Sum('subtotal'),
            total_quantity=Sum('quantity')
        ).order_by('-total_amount')
        
        # Конвертуємо в список словників для сумісності з шаблоном
        top_by_amount = []
        for item in top_by_amount_raw:
            top_by_amount.append({
                'product__name': item['product__name'],
                'product_name': item['product__name'],  # Для сумісності
                'total_amount': float(item['total_amount'] or 0),
                'revenue': float(item['total_amount'] or 0),  # Для сумісності з C++ форматом
                'total_quantity': item['total_quantity']
            })
        
        top_by_quantity_raw = SaleItem.objects.filter(
            sale__created_at__date__gte=date_from,
            sale__created_at__date__lte=date_to
        ).values('product__name').annotate(
            total_amount=Sum('subtotal'),
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')
        
        # Конвертуємо в список словників для сумісності з шаблоном
        top_by_quantity = []
        for item in top_by_quantity_raw:
            top_by_quantity.append({
                'product__name': item['product__name'],
                'product_name': item['product__name'],  # Для сумісності
                'total_quantity': item['total_quantity'],
                'quantity': item['total_quantity'],  # Для сумісності з C++ форматом
                'total_amount': float(item['total_amount'] or 0)
            })
    
    # Залишки на складі (in - out)
    stock_data = []
    for product in Product.objects.filter(is_active=True):
        incoming = Stock.objects.filter(
            product=product,
            transaction_type='in'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        outgoing = Stock.objects.filter(
            product=product,
            transaction_type='out'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        adjustments = Stock.objects.filter(
            product=product,
            transaction_type='adjustment'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        balance = incoming - outgoing + adjustments
        stock_data.append({
            'product': product,
            'balance': balance,
            'value': float(balance * product.price) if balance > 0 else 0
        })
    
    stock_data.sort(key=lambda x: x['value'], reverse=True)
    
    # Графік виручки по днях - використовуємо дані з C++
    if 'error' not in cpp_data and 'daily_revenue' in cpp_data:
        dates = [datetime.strptime(item['date'], '%Y-%m-%d') for item in cpp_data['daily_revenue']]
        revenues = [item['revenue'] for item in cpp_data['daily_revenue']]
    else:
        # Резервний варіант
        daily_revenue = sales.extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            revenue=Sum('total_amount')
        ).order_by('day')
        
        dates = [datetime.strptime(item['day'], '%Y-%m-%d') for item in daily_revenue]
        revenues = [float(item['revenue'] or 0) for item in daily_revenue]
    
    # Генерація графіка
    plt.figure(figsize=(10, 5))
    plt.plot(dates, revenues, marker='o', linewidth=2, markersize=6)
    plt.title('Виручка по днях', fontsize=14, fontweight='bold')
    plt.xlabel('Дата', fontsize=12)
    plt.ylabel('Виручка (грн)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Конвертація графіка в base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    # Додаємо дані з C++ для PDF
    context = {
        'date_from': date_from.strftime('%d.%m.%Y'),
        'date_to': date_to.strftime('%d.%m.%Y'),
        'total_revenue': float(total_revenue_from_stats if 'error' not in cpp_data else total_revenue),
        'total_count': total_count,
        'average_check': float(average_check),
        'top_by_amount': top_by_amount,
        'top_by_quantity': top_by_quantity,
        'stock_data': stock_data,
        'chart_image': image_base64,
        # Додаткові дані з C++ (або розраховані в Python якщо C++ не працює)
        'cpp_stats': cpp_data.get('statistics', {}),
        'abc_analysis': cpp_data.get('abc_analysis', []) if 'error' not in cpp_data else [],
        'category_shares': cpp_data.get('category_shares', []) if 'error' not in cpp_data else [],
    }
    
    html_string = render_to_string('store/report.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    
    pdf_file = html.write_pdf()
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"sales_report_{date_from_str}_{date_to_str}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@login_required
@user_passes_test(is_manager)
def analytics_data(request):
    """API для отримання даних для аналітики"""
    # Отримуємо дати з параметрів запиту
    date_from_str = request.GET.get('date_from', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to_str = request.GET.get('date_to', timezone.now().strftime('%Y-%m-%d'))
    
    # Конвертуємо рядки в date об'єкти
    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # Якщо дати невалідні, використовуємо значення за замовчуванням
        date_from = (timezone.now() - timedelta(days=30)).date()
        date_to = timezone.now().date()
        date_from_str = date_from.strftime('%Y-%m-%d')
        date_to_str = date_to.strftime('%Y-%m-%d')
    
    # Виклик C++ модуля - ядро аналітики
    # C++ робить ВСІ обчислення: агрегацію, топ товарів, статистики, ABC-аналіз
    cpp_data = call_cpp_analytics(date_from_str, date_to_str)
    
    # Якщо C++ модуль повернув помилку, використовуємо резервний варіант
    if 'error' in cpp_data:
        # Резервний варіант через Python ORM (якщо C++ не працює)
        sales_by_date = Sale.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('day')
        
        sales_by_date_list = []
        for item in sales_by_date:
            sales_by_date_list.append({
                'day': item['day'],
                'total': float(item['total'] or 0),
                'count': item['count']
            })
        
        category_sales = SaleItem.objects.filter(
            sale__created_at__date__gte=date_from,
            sale__created_at__date__lte=date_to
        ).values('product__category__name').annotate(
            total=Sum('subtotal')
        ).order_by('-total')
        
        category_sales_list = []
        for item in category_sales:
            category_sales_list.append({
                'product__category__name': item['product__category__name'],
                'total': float(item['total'] or 0)
            })
        
        return JsonResponse({
            'sales_by_date': sales_by_date_list,
            'category_sales': category_sales_list,
            'cpp_error': cpp_data.get('error'),
        })
    
    # Використовуємо дані з C++ - вони є основним джерелом
    # Конвертуємо формат C++ в формат для Chart.js
    sales_by_date_list = []
    if 'daily_revenue' in cpp_data:
        for item in cpp_data['daily_revenue']:
            sales_by_date_list.append({
                'day': item['date'],
                'total': item['revenue'],
                'count': 0  # C++ не рахує count, можна додати якщо потрібно
            })
    
    category_sales_list = []
    if 'category_shares' in cpp_data:
        for item in cpp_data['category_shares']:
            category_sales_list.append({
                'product__category__name': item['category'],
                'total': item['share']  # Відсоток, можна перерахувати в суму якщо потрібно
            })
    
    return JsonResponse({
        'sales_by_date': sales_by_date_list,
        'category_sales': category_sales_list,
        # Всі дані з C++ модуля
        'daily_revenue': cpp_data.get('daily_revenue', []),
        'weekly_revenue': cpp_data.get('weekly_revenue', []),
        'monthly_revenue': cpp_data.get('monthly_revenue', []),
        'top_products_by_revenue': cpp_data.get('top_products_by_revenue', []),
        'top_products_by_quantity': cpp_data.get('top_products_by_quantity', []),
        'category_shares': cpp_data.get('category_shares', []),
        'statistics': cpp_data.get('statistics', {}),
        'abc_analysis': cpp_data.get('abc_analysis', []),
    })


def call_cpp_analytics(date_from_str, date_to_str):
    """Виклик C++ модуля для аналітики - ядро обчислень"""
    try:
        cpp_executable = os.path.join(settings.BASE_DIR, 'cpp_analytics', 'analytics')
        
        if not os.path.exists(cpp_executable):
            return {'error': 'C++ модуль не знайдено'}
        
        # Конвертуємо рядки в date об'єкти
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            date_from = (timezone.now() - timedelta(days=30)).date()
            date_to = timezone.now().date()
        
        # ОДИН запит до БД - отримуємо всі дані з позиціями
        sales = Sale.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).prefetch_related('saleitem_set__product__category')
        
        # Формуємо JSON з реальними даними: продажі + позиції
        input_data = {
            'sales': []
        }
        
        for sale in sales:
            sale_data = {
                'id': sale.id,
                'date': sale.created_at.strftime('%Y-%m-%d'),
                'total_amount': float(sale.total_amount),
                'items': []
            }
            
            # Додаємо всі позиції продажу з реальними даними
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
        
        # Виклик C++ програми з повними даними
        result = subprocess.run(
            [cpp_executable],
            input=json.dumps(input_data, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=30  # Збільшено таймаут для складних обчислень
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {'error': result.stderr or 'Помилка виконання C++ модуля'}
    
    except json.JSONDecodeError as e:
        return {'error': f'Помилка парсингу JSON від C++: {str(e)}'}
    except Exception as e:
        return {'error': str(e)}


# ========== КЕРУВАННЯ КОРИСТУВАЧАМИ ==========
@login_required
@user_passes_test(is_admin)
def user_list(request):
    """Список користувачів"""
    users = User.objects.all()
    return render(request, 'store/user_list.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """Створення нового користувача (тільки для адміністраторів)"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Користувач "{user.username}" успішно створений!')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'store/user_create.html', {'form': form, 'title': 'Додати користувача'})


@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    """Редагування користувача та ролей"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
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
            return redirect('user_list')
        except Exception as e:
            messages.error(request, f'Помилка при оновленні користувача: {str(e)}')
    
    groups = Group.objects.all()
    return render(request, 'store/user_edit.html', {'user': user, 'groups': groups})


@login_required
def logout_view(request):
    """Вихід користувача"""
    logout(request)
    messages.success(request, 'Ви успішно вийшли з системи')
    return redirect('login')


@login_required
def product_price_api(request, pk):
    """API для отримання ціни товару"""
    product = get_object_or_404(Product, pk=pk)
    return JsonResponse({
        'price': float(product.price),
        'stock': product.current_stock,
    })

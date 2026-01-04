from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db.models import Sum
from django.utils import timezone
from store.models import Category, Product, Stock, Sale, SaleItem
from decimal import Decimal
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Створює демонстраційні дані для тестування'

    def handle(self, *args, **options):
        self.stdout.write('Створення демонстраційних даних...')

        # Створення груп
        cashier_group, _ = Group.objects.get_or_create(name='Касир')
        admin_group, _ = Group.objects.get_or_create(name='Адміністратор')
        manager_group, _ = Group.objects.get_or_create(name='Керівник')

        # Створення користувачів
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Адміністратор',
                last_name='Системи'
            )
            admin.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS(f'Створено користувача: {admin.username}'))

        if not User.objects.filter(username='cashier1').exists():
            cashier1 = User.objects.create_user(
                username='cashier1',
                email='cashier1@example.com',
                password='cashier123',
                first_name='Олена',
                last_name='Касир'
            )
            cashier1.groups.add(cashier_group)
            self.stdout.write(self.style.SUCCESS(f'Створено користувача: {cashier1.username}'))

        if not User.objects.filter(username='manager1').exists():
            manager1 = User.objects.create_user(
                username='manager1',
                email='manager1@example.com',
                password='manager123',
                first_name='Петро',
                last_name='Керівник',
                is_staff=True  # Керівник має доступ до Django admin
            )
            manager1.groups.add(manager_group)
            self.stdout.write(self.style.SUCCESS(f'Створено користувача: {manager1.username}'))

        # Створення категорій
        categories_data = [
            {'name': 'Електроніка', 'description': 'Електронні пристрої та аксесуари'},
            {'name': 'Одяг', 'description': 'Одяг та взуття'},
            {'name': 'Продукти харчування', 'description': 'Харчові продукти'},
            {'name': 'Побутова техніка', 'description': 'Техніка для дому'},
            {'name': 'Книги', 'description': 'Книги та журнали'},
        ]

        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(category)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Створено категорію: {category.name}'))

        # Створення товарів (ціни зменшені в 10 разів)
        products_data = [
            {'name': 'Смартфон Samsung', 'category': 'Електроніка', 'price': 15000, 'barcode': '1234567890123'},
            {'name': 'Ноутбук HP', 'category': 'Електроніка', 'price': 25000, 'barcode': '1234567890124'},
            {'name': 'Футболка чоловіча', 'category': 'Одяг', 'price': 500, 'barcode': '1234567890125'},
            {'name': 'Джинси', 'category': 'Одяг', 'price': 1200, 'barcode': '1234567890126'},
            {'name': 'Хліб білий', 'category': 'Продукти харчування', 'price': 25, 'barcode': '1234567890127'},
            {'name': 'Молоко', 'category': 'Продукти харчування', 'price': 35, 'barcode': '1234567890128'},
            {'name': 'Холодильник', 'category': 'Побутова техніка', 'price': 18000, 'barcode': '1234567890129'},
            {'name': 'Пральна машина', 'category': 'Побутова техніка', 'price': 12000, 'barcode': '1234567890130'},
            {'name': 'Книга "Python для початківців"', 'category': 'Книги', 'price': 300, 'barcode': '1234567890131'},
            {'name': 'Журнал "Компьютер"', 'category': 'Книги', 'price': 50, 'barcode': '1234567890132'},
        ]

        products = []
        for prod_data in products_data:
            category = next(c for c in categories if c.name == prod_data['category'])
            product, created = Product.objects.update_or_create(
                barcode=prod_data['barcode'],
                defaults={
                    'name': prod_data['name'],
                    'category': category,
                    'price': Decimal(str(prod_data['price'])),
                    'is_active': True
                }
            )
            products.append(product)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Створено товар: {product.name}'))
            else:
                self.stdout.write(f'Оновлено товар: {product.name}')

        # Очищаємо всі старі дані
        self.stdout.write('Очищення старих даних...')
        Sale.objects.all().delete()
        Stock.objects.all().delete()
        self.stdout.write('Видалено всі старі продажі та складські операції')
        
        # Створення складських надходжень з достатньою кількістю товару (зменшено в 10 разів)
        admin_user = User.objects.get(username='admin')
        for product in products:
            # Створюємо надходження (зменшено в 10 разів)
            quantity = random.randint(100, 200)  # Зменшено з 1000-2000 до 100-200
            Stock.objects.create(
                product=product,
                quantity=quantity,
                transaction_type='in',
                notes='Початкове надходження',
                created_by=admin_user,
                created_at=timezone.make_aware(datetime(2025, 11, 25, 8, 0))  # 25 листопада, до початку продажів
            )
            self.stdout.write(f'Створено надходження: {product.name} - {quantity} шт.')
        
        # Створення продажів від 1 грудня до сьогодні
        cashier = User.objects.get(username='cashier1')
        from datetime import date as date_class
        start_date = date_class(2025, 12, 1)  # 1 грудня 2025
        end_date = timezone.now().date()
        current_date = start_date
        
        total_sales = 0
        days_count = 0
        self.stdout.write(f'Створення продажів з {start_date} до {end_date}')
        while current_date <= end_date:
            days_count += 1
            if days_count <= 3 or days_count % 7 == 0:  # Логуємо перші 3 дні та кожен 7-й
                self.stdout.write(f'Обробка дня: {current_date}')
            # Створюємо 2-8 продажів на день (більше в вихідні)
            day_of_week = current_date.weekday()
            if day_of_week >= 5:  # Субота або неділя
                num_sales = random.randint(5, 12)
            else:
                num_sales = random.randint(2, 8)
            
            for sale_num in range(num_sales):
                # Випадковий час протягом дня (від 9:00 до 20:00)
                hour = random.randint(9, 20)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                # Створюємо datetime для конкретного дня
                # Використовуємо timezone.make_aware з правильним timezone
                sale_datetime = datetime(
                    current_date.year,
                    current_date.month,
                    current_date.day,
                    hour, minute, second
                )
                # Використовуємо timezone з settings
                from django.conf import settings
                from zoneinfo import ZoneInfo
                tz = ZoneInfo(settings.TIME_ZONE)
                sale_time = sale_datetime.replace(tzinfo=tz)
                
                # Створюємо продаж з правильною датою
                sale = Sale.objects.create(
                    user=cashier,
                    total_amount=0
                )
                # Встановлюємо дату безпосередньо через update, щоб уникнути конвертації
                Sale.objects.filter(id=sale.id).update(created_at=sale_time)
                sale.refresh_from_db()
                
                # Додаємо 1-2 позицій до продажу
                num_items = random.randint(1, 2)
                selected_products = random.sample(products, min(num_items, len(products)))
                
                items_added = 0
                for product in selected_products:
                    # Отримуємо поточний залишок товару
                    current_stock = product.current_stock
                    
                    # Якщо залишок достатній, додаємо товар
                    if current_stock > 0:
                        # Обмежуємо кількість доступним залишком
                        quantity = min(random.randint(1, 2), current_stock)
                        price = product.price
                        
                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=quantity,
                            price=price
                        )
                        
                        # Створення складської операції з правильним часом
                        Stock.objects.create(
                            product=product,
                            quantity=quantity,
                            transaction_type='out',
                            notes=f'Продаж #{sale.id}',
                            created_by=cashier,
                            created_at=sale_time
                        )
                        items_added += 1
                
                # Оновлюємо загальну суму продажу
                sale.total_amount = sale.calculate_total()
                sale.save()
                
                # Рахуємо тільки продажі з позиціями
                if items_added > 0:
                    total_sales += 1
                else:
                    # Якщо немає позицій, видаляємо продаж
                    sale.delete()
            
            # Переходимо до наступного дня
            current_date += timedelta(days=1)
        
        self.stdout.write(self.style.SUCCESS(f'Створено {total_sales} продажів за {days_count} днів з 1 грудня до сьогодні'))

        self.stdout.write(self.style.SUCCESS('Демонстраційні дані успішно створено!'))
        self.stdout.write('\nДані для входу:')
        self.stdout.write('Адміністратор: admin / admin123')
        self.stdout.write('Касир: cashier1 / cashier123')
        self.stdout.write('Керівник: manager1 / manager123')


from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
import logging

logger = logging.getLogger(__name__)


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        """
        Автоматичний запуск seed_data при старті сервера, якщо:
        1. БД готова (таблиці існують)
        2. Адміністратора ще немає
        3. Не запускається під час migrate
        """
        # Перевірка, чи не запускається під час migrate
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return
        
        # Перевірка, чи не запускається під час тестів
        if 'test' in sys.argv:
            return
        
        try:
            from django.contrib.auth.models import User
            from django.db import connection
            
            # Перевірка, чи БД готова (таблиця auth_user існує)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='auth_user'
                """)
                if not cursor.fetchone():
                    # Таблиці ще не створені
                    return
            
            # Перевірка, чи адміністратор вже існує
            if not User.objects.filter(username='admin').exists():
                logger.info('Адміністратор не знайдено, запуск seed_data...')
                from django.core.management import call_command
                call_command('seed_data', verbosity=0)
                logger.info('seed_data виконано успішно')
        except (OperationalError, ProgrammingError) as e:
            # БД ще не готова або помилка доступу
            logger.debug(f'БД ще не готова: {e}')
            pass
        except Exception as e:
            # Інші помилки - логуємо, але не падаємо
            logger.warning(f'Помилка при автоматичному запуску seed_data: {e}')
            pass

#!/bin/bash
# Скрипт для деплою проекту на сервер

set -e  # Зупинитися при помилці

echo "🚀 Початок деплою..."

# 1. Компіляція C++ модуля
echo "📦 Компіляція C++ модуля..."
cd cpp_analytics
if ! make; then
    echo "❌ Помилка компіляції C++ модуля!"
    echo "Перевірте, чи встановлений g++: g++ --version"
    exit 1
fi
cd ..

# Перевірка, чи файл створено
if [ ! -f "cpp_analytics/analytics" ]; then
    echo "❌ C++ модуль не скомпільовано!"
    exit 1
fi

# Надання прав на виконання
chmod +x cpp_analytics/analytics
echo "✅ C++ модуль скомпільовано успішно"

# 2. Встановлення залежностей Python (якщо потрібно)
if [ -f "requirements.txt" ]; then
    echo "📦 Встановлення Python залежностей..."
    pip install -r requirements.txt
fi

# 3. Міграції Django
echo "🗄️  Виконання міграцій..."
python manage.py migrate --noinput

# 4. Збір статичних файлів (якщо потрібно)
if [ -d "staticfiles" ] || grep -q "STATIC_ROOT" settings.py 2>/dev/null; then
    echo "📁 Збір статичних файлів..."
    python manage.py collectstatic --noinput
fi

echo "✅ Деплой завершено успішно!"
echo ""
echo "Для запуску сервера:"
echo "  python manage.py runserver"
echo ""
echo "Або для production:"
echo "  gunicorn inventory_system.wsgi:application"


# Встановлення залежностей для PDF

## 1. Встановити пакети

```bash
pip install WeasyPrint matplotlib
```

**Примітка для WeasyPrint:**
- На Linux може знадобитися: `sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0`
- На macOS: `brew install pango`
- На Windows: зазвичай працює з pip

## 2. Перевірка settings.py

Вже налаштовано:
- `TIME_ZONE = 'Europe/Kyiv'`
- `STATIC_URL = 'static/'`
- `MEDIA_URL = 'media/'`

## 3. Endpoints

- **Чек продажу**: `/sales/<id>/receipt/pdf/`
  - Доступ: Касир (свої), Адмін, Керівник (всі)
  
- **Звіт продажів**: `/reports/sales/pdf/?start=YYYY-MM-DD&end=YYYY-MM-DD`
  - Доступ: Адмін, Керівник

## 4. Використання

- На сторінці деталей продажу є кнопка "Завантажити чек (PDF)"
- На сторінці звітів є кнопка "Завантажити звіт (PDF)"


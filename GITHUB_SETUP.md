# Інструкція для завантаження на GitHub

## ✅ Що вже зроблено:
- ✅ Git репозиторій ініціалізовано
- ✅ Всі файли додано до git
- ✅ Зроблено перший commit
- ✅ Гілка перейменована на `main`

## 📋 Наступні кроки:

### 1. Створіть репозиторій на GitHub

1. Відкрийте https://github.com
2. Натисніть кнопку **"New"** або **"+"** → **"New repository"**
3. Заповніть форму:
   - **Repository name**: `inventory-management-system` (або інша назва)
   - **Description**: "Django inventory management system with C++ analytics and PDF generation"
   - **Visibility**: Public або Private (на ваш вибір)
   - ⚠️ **НЕ** ставлять галочки на "Add a README file", "Add .gitignore", "Choose a license" (все вже є)
4. Натисніть **"Create repository"**

### 2. Підключіть локальний репозиторій до GitHub

Після створення репозиторію GitHub покаже інструкції. Виконайте команди:

```bash
cd /Users/maksimgerbrant/kurs

# Додайте remote (замініть YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/inventory-management-system.git

# Або якщо використовуєте SSH:
# git remote add origin git@github.com:YOUR_USERNAME/inventory-management-system.git

# Завантажте код на GitHub
git push -u origin main
```

### 3. Перевірка

Відкрийте ваш репозиторій на GitHub - всі файли мають з'явитися!

## 🔐 Якщо використовуєте SSH ключі:

Якщо у вас налаштований SSH ключ для GitHub, використовуйте:
```bash
git remote add origin git@github.com:YOUR_USERNAME/inventory-management-system.git
```

## 🔑 Якщо потрібна автентифікація:

GitHub може запитати логін/пароль. Якщо використовуєте Personal Access Token:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Створіть новий token з правами `repo`
3. Використовуйте token замість пароля

## 📝 Після першого push:

Всі наступні зміни можна завантажувати командами:
```bash
git add .
git commit -m "Опис змін"
git push
```


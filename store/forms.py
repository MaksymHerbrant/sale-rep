from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Category, Product, Stock, Sale, SaleItem


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Ім'я")
    last_name = forms.CharField(max_length=30, required=True, label="Прізвище")

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'barcode', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['product', 'quantity', 'transaction_type', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        is_manager = kwargs.pop('is_manager', False)
        super().__init__(*args, **kwargs)
        
        # Для керівника - тільки надходження
        if is_manager:
            self.fields['transaction_type'].choices = [('in', 'Надходження')]
            self.fields['transaction_type'].initial = 'in'
            # Не використовуємо disabled, бо тоді поле не відправляється в POST
            # Замість цього використовуємо readonly input в шаблоні
        
        # Для корекції дозволяємо негативні значення
        if self.instance and self.instance.transaction_type == 'adjustment':
            self.fields['quantity'].widget.attrs['min'] = None
        else:
            self.fields['quantity'].widget.attrs['min'] = '1'
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        transaction_type = self.cleaned_data.get('transaction_type')
        
        # Для надходжень та продажів кількість має бути позитивною
        if transaction_type in ['in', 'out'] and quantity <= 0:
            raise forms.ValidationError('Кількість має бути більше 0 для надходжень та продажів')
        
        # Для корекції дозволяємо будь-які значення (позитивні для збільшення, негативні для зменшення)
        return quantity
    
    def clean_transaction_type(self):
        transaction_type = self.cleaned_data.get('transaction_type')
        # Перевірка для керівника (якщо форма була змінена через інспектор браузера)
        # Це додаткова перевірка, основна логіка в view
        return transaction_type


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import UserProfile, SearchRequest, RequestResponse  # Import the models

class UserRegisterForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Repeat Password")
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        
        if password and password2 and password != password2:
            raise ValidationError("Passwords don't match")
        
        return cleaned_data

class UserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'phone_number', 'address']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
        }

class SearchRequestForm(forms.ModelForm):
    class Meta:
        model = SearchRequest
        fields = ['city', 'vin', 'make', 'model', 'generation', 'search', 'condition', 'image']
        widgets = {
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город'}),
            'vin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VIN номер'}),
            'make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Марка'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Модель'}),
            'generation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Поколение'}),
            'search': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название запчасти'}),
            'condition': forms.Select(attrs={'class': 'form-control'}, choices=[("new", "Новая"), ("used", "Б/у")]),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

class RequestResponseForm(forms.ModelForm):
    class Meta:
        model = RequestResponse
        fields = ['description', 'price', 'is_vin_matched', 'is_new', 'city', 'address', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Описание', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Цена'}),
            'is_vin_matched': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_new': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Адрес'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

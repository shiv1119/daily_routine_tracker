from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Category, DailyLog

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    dob = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'bio', 'dob', 'personal_target']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'target_value', 'unit', 'icon', 'penalty_text']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'target_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ✅, 💪, 📚'}),
            'penalty_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['completed', 'value_achieved', 'missed_reason']
        widgets = {
            'value_achieved': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'missed_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
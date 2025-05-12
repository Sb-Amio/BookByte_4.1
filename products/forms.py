from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from .models import *
from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', max_length=100)

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            return cleaned_data

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username'
        self.fields['email'].label = 'Email Address'
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Confirm Password'

class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'publisher', 'description', 'image', 'category', 'price', 'quantity', 'type_choice']

class EBookForm(ModelForm):
    class Meta:
        model = Ebook
        fields = ['title', 'author', 'description', 'image' ,'price']

class AccessoriesForm(ModelForm):
    class Meta:
        model = Accessories
        fields = ['title', 'description', 'price', 'quantity', 'image']

class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ['quantity']

class ReviewForm(ModelForm):
    class Meta:
        model = Review
        fields = ['review_choice']

class DonateBookForm(ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'publisher', 'description', 'image', 'category', 'price', 'quantity', 'type_choice']
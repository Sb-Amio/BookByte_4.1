from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register([Profile, Book, Ebook, Accessories, Order, CartItem, Review])

# admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm

class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

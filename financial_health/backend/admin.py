# from django.contrib import admin

# # Register your models here.
from django.contrib import admin
from .models import *
# Register your models here.
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
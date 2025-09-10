from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'mobile_phone', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'country')
    search_fields = ('email', 'first_name', 'last_name', 'mobile_phone')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'mobile_phone', 'profile_picture', 'birthdate', 'facebook_profile', 'country')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'mobile_phone', 'password1', 'password2'),
        }),
    )

admin.site.register(User, CustomUserAdmin)
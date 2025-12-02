from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Transaction, Category, SavingGoal, UserProfile

# --- Advanced Admin Configuration ---

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline] # Show profile (currency) in User page
    list_display = ('username', 'email', 'is_staff', 'date_joined')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'transaction_type', 'date', 'category', 'user')
    list_filter = ('transaction_type', 'date', 'user')
    search_fields = ('title', 'user__username')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    list_filter = ('user',)

@admin.register(SavingGoal)
class SavingGoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_amount', 'target_amount', 'user')
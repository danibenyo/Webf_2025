from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Core
    path('', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('income/', views.income_view, name='income'),
    path('expenses/', views.expense_view, name='expenses'),
    path('export/', views.export_csv, name='export_csv'),
    
    # Categories
    path('categories/', views.manage_categories, name='manage_categories'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    
    # Transactions
    path('add/', views.add_transaction, name='add_transaction'),
    path('delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('edit/<int:pk>/', views.edit_transaction, name='edit_transaction'),

    # Savings
    path('savings/', views.savings_view, name='savings'),
    path('savings/add/', views.add_goal, name='add_goal'),
    path('savings/edit/<int:pk>/', views.edit_goal, name='edit_goal'),
    path('savings/delete/<int:pk>/', views.delete_goal, name='delete_goal'),
    path('savings/update/<int:pk>/', views.update_saving_amount, name='update_saving_amount'),

    # Custom Admin
    path('staff/users/', views.admin_user_list, name='admin_user_list'),
    path('staff/users/edit/<int:pk>/', views.admin_user_edit, name='admin_user_edit'),
    path('staff/users/delete/<int:pk>/', views.admin_user_delete, name='admin_user_delete'),
]
import csv
import json
from decimal import Decimal
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from .forms import UserRegistrationForm, TransactionForm, CategoryForm, SavingGoalForm, UserUpdateForm
from .models import Transaction, Category, SavingGoal, UserProfile

# --- Auth Views ---
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            # Default Categories
            defaults = ["Salary", "Food", "Rent", "Books", "Party"]
            for name in defaults:
                Category.objects.create(user=user, name=name)
            messages.success(request, "Registration successful!")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@csrf_exempt
def logout_view(request):
    logout(request)
    return redirect('login')

# --- Main Views ---
@login_required
def dashboard_view(request):
    transactions = Transaction.objects.filter(user=request.user)
    total_income = transactions.filter(transaction_type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = transactions.filter(transaction_type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense

    expense_data = transactions.filter(transaction_type='EXPENSE').values('category__name').annotate(total=Sum('amount'))
    chart_labels = [entry['category__name'] or 'Uncategorized' for entry in expense_data]
    chart_data = [float(entry['total']) for entry in expense_data]

    context = {
        'transactions': transactions[:5], # Limit to 5 for summary
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'dashboard.html', context)

@login_required
def profile_view(request):
    # Handle Currency Update
    if request.method == 'POST':
        new_currency = request.POST.get('currency')
        if new_currency in ['Ft', '$', '€']:
            # Access userprofile safely
            if not hasattr(request.user, 'userprofile'):
                UserProfile.objects.create(user=request.user)
            
            request.user.userprofile.currency = new_currency
            request.user.userprofile.save()
            messages.success(request, "Currency preference updated.")
            return redirect('profile')

    categories = Category.objects.filter(user=request.user)
    return render(request, 'profile.html', {'categories': categories})

@login_required
def income_view(request):
    transactions = Transaction.objects.filter(user=request.user, transaction_type='INCOME')
    return render(request, 'transaction_list.html', {'transactions': transactions, 'title': 'Income History', 'type': 'INCOME'})

@login_required
def expense_view(request):
    transactions = Transaction.objects.filter(user=request.user, transaction_type='EXPENSE')
    return render(request, 'transaction_list.html', {'transactions': transactions, 'title': 'Expense History', 'type': 'EXPENSE'})

# --- Category Views ---
@login_required
def manage_categories(request):
    categories = Category.objects.filter(user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.user = request.user
            cat.save()
            messages.success(request, "Category added.")
            return redirect('manage_categories')
    else:
        form = CategoryForm()
    return render(request, 'manage_categories.html', {'categories': categories, 'form': form})

@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted.")
    return redirect('manage_categories')

# --- Transaction CRUD ---
@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.user = request.user
            t.save()
            messages.success(request, "Transaction added.")
            return redirect('dashboard')
    else:
        form = TransactionForm(request.user)
    return render(request, 'add_transaction.html', {'form': form})

@login_required
def delete_transaction(request, pk):
    t = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        t.delete()
        messages.success(request, "Deleted.")
    return redirect('dashboard')

@login_required
def edit_transaction(request, pk):
    t = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST, instance=t)
        if form.is_valid():
            form.save()
            messages.success(request, "Updated.")
            return redirect('dashboard')
    else:
        form = TransactionForm(request.user, instance=t)
    return render(request, 'edit_transaction.html', {'form': form})

@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Webf_2025_data.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Title', 'Category', 'Type', 'Amount'])
    for t in Transaction.objects.filter(user=request.user):
        writer.writerow([t.date, t.title, t.category.name if t.category else "None", t.transaction_type, t.amount])
    return response

# --- Savings Views ---
@login_required
def savings_view(request):
    goals = SavingGoal.objects.filter(user=request.user)
    return render(request, 'savings.html', {'goals': goals})

@login_required
def update_saving_amount(request, pk):
    goal = get_object_or_404(SavingGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            action = request.POST.get('action')
            
            if amount > 0:
                if action == 'add':
                    goal.current_amount += amount
                elif action == 'subtract':
                    goal.current_amount -= amount
                    if goal.current_amount < 0:
                        goal.current_amount = Decimal(0)
                
                goal.save()
                messages.success(request, f"Updated {goal.name}.")
            else:
                messages.error(request, "Enter a valid amount.")
        except:
             messages.error(request, "Invalid input.")
    return redirect('savings')

@login_required
def add_goal(request):
    if request.method == 'POST':
        form = SavingGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, "Goal created.")
            return redirect('savings')
    else:
        form = SavingGoalForm()
    return render(request, 'add_goal.html', {'form': form})

@login_required
def edit_goal(request, pk):
    goal = get_object_or_404(SavingGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        form = SavingGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, "Goal updated.")
            return redirect('savings')
    else:
        form = SavingGoalForm(instance=goal)
    return render(request, 'add_goal.html', {'form': form, 'is_edit': True})

@login_required
def delete_goal(request, pk):
    goal = get_object_or_404(SavingGoal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, "Goal deleted.")
    return redirect('savings')

# --- Custom Admin Views (Superuser only) ---
@user_passes_test(lambda u: u.is_superuser)
def admin_user_list(request):
    users = User.objects.all()
    return render(request, 'admin_user_list.html', {'users': users})

@user_passes_test(lambda u: u.is_superuser)
def admin_user_edit(request, pk):
    user_to_edit = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user_to_edit.username} updated.")
            return redirect('admin_user_list')
    else:
        form = UserUpdateForm(instance=user_to_edit)
    return render(request, 'admin_user_edit.html', {'form': form, 'target_user': user_to_edit})

@user_passes_test(lambda u: u.is_superuser)
def admin_user_delete(request, pk):
    user_to_delete = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        # Prevent self-deletion
        if user_to_delete == request.user:
            messages.error(request, "You cannot delete yourself.")
        else:
            user_to_delete.delete()
            messages.success(request, "User deleted.")
    return redirect('admin_user_list')
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- User Profile for Currency Settings ---
class UserProfile(models.Model):
    CURRENCY_CHOICES = [
        ('Ft', 'HUF (Ft)'),
        ('$', 'USD ($)'),
        ('€', 'EUR (€)'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default='Ft')

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signals to automatically create/save UserProfile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Ensure profile exists before saving (for older users or superusers created via CLI)
    if not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()

# --- Core Models ---
class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    
    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.amount}"

class SavingGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings')
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)

    def progress_percentage(self):
        if self.target_amount > 0:
            percent = (self.current_amount / self.target_amount) * 100
            return min(percent, 100) # Cap at 100%
        return 0

    def __str__(self):
        return self.name
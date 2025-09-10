from django.contrib.auth.models import AbstractUser
from django.db import models
# library that helps input time-date for a preexisting records with new created_at column
from django.utils.timezone import now

# FloatUser model with role-based system
class FloatUser(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('investor', 'Investor'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    # this is put here to avoid conflict between 'auth.User.groups' and 'float_me_app.FloatUser.groups'
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  
        blank=True,
    )

    # this is put here to avoid conflict between 'auth.User.user_permissions' and 'float_me_app.FloatUser.user_permissions'
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  
        blank=True,
    )

    def __str__(self):
        return f"{self.username} | {self.role} | {self.first_name} {self.last_name} | {self.phone_number} | {self.email}"

# Role model (optional if roles need more attributes)
class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=now, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# Admin model with additional permissions
class Admin(models.Model):
    user = models.OneToOneField(FloatUser, on_delete=models.CASCADE)
    permissions = models.JSONField(default=dict)
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=now, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} | {self.permissions}"

# Investment plans
class InvestmentPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration_in_months = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2)
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=now, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

# Subscriptions model
class Subscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
        ('matured', 'Matured'),
    )

    user = models.ForeignKey(FloatUser, on_delete=models.CASCADE, related_name='investor_subscriptions')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    amount_invested = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    maturity_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    payout_count = models.IntegerField(default=0, blank=True)
    sub_token = models.CharField(max_length=100, unique=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=now, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Username: {self.user.username} | Plan Name: {self.plan.name} | Amount: {self.amount_invested} | Status: {self.status} | Start Date: {self.start_date} | | Maturity date: {self.maturity_date}"

# Transactions model
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('payout', 'Payout'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    )

    user = models.ForeignKey(FloatUser, on_delete=models.CASCADE, related_name='investor_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    reference = models.CharField(max_length=100, unique=True)
    performed_by = models.ForeignKey(FloatUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_created_transactions')
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=now, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"

# Payments model
class Payment(models.Model):
    user = models.ForeignKey(FloatUser, on_delete=models.CASCADE, related_name='investor_payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20)
    transaction_reference = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(FloatUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_created_payments')
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=now, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.subscription.plan.name} - {self.amount_paid}"

# Payouts model
class Payout(models.Model):
    user = models.ForeignKey(FloatUser, on_delete=models.CASCADE, related_name='investor_payouts')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payout_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=(('pending', 'Pending'), ('completed', 'Completed')))
    reference = models.CharField(max_length=100, unique=True)
    performed_by = models.ForeignKey(FloatUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_created_payouts')
    # created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=now, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.subscription.plan.name} - {self.amount_paid} - {self.status}"

# Audit logs for tracking admin actions
class AuditLog(models.Model):
    performed_by = models.ForeignKey(FloatUser, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.performed_by.username} - {self.action}"

# Notifications model
class Notification(models.Model):
    user = models.ForeignKey(FloatUser, on_delete=models.CASCADE)
    message = models.TextField()
    notification_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=(('sent', 'Sent'), ('read', 'Read')), default='sent')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.notification_type} - {self.status}"
    
# UserPaymentInfo model
class UserPaymentInfo(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(FloatUser, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=10)
    bank_name = models.CharField(max_length=50)
    account_name = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

    def __str__(self):
        return f"{self.user.username} - {self.account_number} - {self.bank_name} - {self.account_name}"


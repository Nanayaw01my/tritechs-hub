from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Ghana Regions (16 regions)
GHANA_REGIONS = [
    ('AH', 'Ahafo Region'),
    ('AR', 'Ashanti Region'),
    ('BO', 'Bono East Region'),
    ('BR', 'Bono Region'),
    ('CR', 'Central Region'),
    ('ER', 'Eastern Region'),
    ('GAR', 'Greater Accra Region'),
    ('NER', 'North East Region'),
    ('NR', 'Northern Region'),
    ('OR', 'Oti Region'),
    ('SAR', 'Savannah Region'),
    ('UER', 'Upper East Region'),
    ('UWR', 'Upper West Region'),
    ('VR', 'Volta Region'),
    ('WR', 'Western Region'),
    ('WNR', 'Western North Region'),
]

# Payment Frequency
FREQUENCY_CHOICES = [
    ('daily', 'Daily (180 payments)'),
    ('weekly', 'Weekly (26 payments)'),
    ('monthly', 'Monthly (6 payments)'),
]

# iPhone Models with Prices
IPHONE_MODELS = [
    ('iPhone 14', 'iPhone 14', 8500),
    ('iPhone 14 Pro', 'iPhone 14 Pro', 11000),
    ('iPhone 14 Pro Max', 'iPhone 14 Pro Max', 12500),
    ('iPhone 15', 'iPhone 15', 10500),
    ('iPhone 15 Pro', 'iPhone 15 Pro', 14000),
    ('iPhone 15 Pro Max', 'iPhone 15 Pro Max', 16000),
    ('iPhone 16', 'iPhone 16', 18000),
]

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15, unique=True)
    alternative_phone = models.CharField(max_length=15, blank=True, null=True)
    ghana_card_id = models.CharField(max_length=20, blank=True, null=True)
    
    # Employment
    occupation = models.CharField(max_length=100)
    income_amount = models.DecimalField(max_digits=10, decimal_places=2)
    income_source = models.CharField(max_length=200)
    
    # Location
    region = models.CharField(max_length=20, choices=GHANA_REGIONS)
    district = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    landmark = models.CharField(max_length=200, blank=True, null=True)
    gps_address = models.CharField(max_length=50, blank=True, null=True)
    
    # Guarantor
    guarantor_name = models.CharField(max_length=200)
    guarantor_phone = models.CharField(max_length=15)
    guarantor_ghana_card = models.CharField(max_length=20, blank=True, null=True)
    guarantor_relationship = models.CharField(max_length=50)
    
    # Documents & Photos
    customer_photo = models.ImageField(upload_to='customers/', null=True, blank=True)
    guarantor_photo = models.ImageField(upload_to='guarantors/', null=True, blank=True)
    proof_of_income = models.FileField(upload_to='income_proofs/', null=True, blank=True)
    
    # Metadata
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='registered_customers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.phone}"
    
    class Meta:
        ordering = ['-created_at']


class IphoneDevice(models.Model):
    # Model choices
    MODEL_CHOICES = [(model[0], f"{model[0]} - GHS {model[2]:,}") for model in IPHONE_MODELS]
    
    model = models.CharField(max_length=50, choices=MODEL_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    serial_number = models.CharField(max_length=100, unique=True)
    simplemdm_udid = models.CharField(max_length=200, unique=True, blank=True, null=True)
    
    # Assignment
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    
    # Lock Status
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    last_locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        status = "🔒 Locked" if self.is_locked else "🔓 Unlocked"
        return f"{self.model} - {self.serial_number} ({status})"
    
    def save(self, *args, **kwargs):
        # Auto-set price based on model
        for model in IPHONE_MODELS:
            if self.model == model[0]:
                self.price = model[2]
                break
        super().save(*args, **kwargs)


class InstallmentPlan(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='plans')
    device = models.ForeignKey(IphoneDevice, on_delete=models.CASCADE, related_name='plans')
    
    # Financial
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    down_payment = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Installment Details
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_installments = models.IntegerField()
    payments_made = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Dates
    start_date = models.DateField()
    next_due_date = models.DateField()
    last_payment_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.device.model} - {self.status}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    installment_plan = models.ForeignKey(InstallmentPlan, on_delete=models.CASCADE, related_name='payments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Dates
    paid_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField()
    
    # Who recorded this payment
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment of GHS {self.amount} - {self.status}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('lock', 'Device Locked'),
        ('unlock', 'Device Unlocked'),
        ('payment', 'Payment Made'),
        ('customer_registration', 'Customer Registered'),
        ('device_assigned', 'Device Assigned'),
        ('plan_created', 'Installment Plan Created'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    device = models.ForeignKey(IphoneDevice, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
from django.contrib import admin
from .models import Customer, IphoneDevice, InstallmentPlan, Payment, AuditLog

class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'region', 'created_at']
    search_fields = ['full_name', 'phone', 'email']
    list_filter = ['region', 'created_at']
    readonly_fields = ['created_at', 'updated_at']

class IphoneDeviceAdmin(admin.ModelAdmin):
    list_display = ['model', 'serial_number', 'price', 'is_locked', 'customer']
    search_fields = ['serial_number', 'model']
    list_filter = ['model', 'is_locked']

class InstallmentPlanAdmin(admin.ModelAdmin):
    list_display = ['customer', 'device', 'total_price', 'remaining_balance', 'status', 'next_due_date']
    list_filter = ['status', 'frequency']
    readonly_fields = ['created_at']

class PaymentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'amount', 'payment_method', 'status', 'paid_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['transaction_id']

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'customer', 'created_at']
    list_filter = ['action']
    readonly_fields = ['created_at']

admin.site.register(Customer, CustomerAdmin)
admin.site.register(IphoneDevice, IphoneDeviceAdmin)
admin.site.register(InstallmentPlan, InstallmentPlanAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
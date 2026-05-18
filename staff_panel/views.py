from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from accounts.models import Customer, IphoneDevice, InstallmentPlan, Payment, AuditLog
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from decimal import Decimal

def is_staff_user(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_user)
def staff_dashboard(request):
    total_customers = Customer.objects.count()
    active_plans = InstallmentPlan.objects.filter(status='active').count()
    devices = IphoneDevice.objects.count()
    
    context = {
        'total_customers': total_customers,
        'active_plans': active_plans,
        'devices': devices,
    }
    return render(request, 'staff_panel/dashboard.html', context)

@login_required
@user_passes_test(is_staff_user)
def register_customer(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        occupation = request.POST.get('occupation')
        income_amount = request.POST.get('income_amount')
        region = request.POST.get('region')
        district = request.POST.get('district')
        location = request.POST.get('location')
        guarantor_name = request.POST.get('guarantor_name')
        guarantor_phone = request.POST.get('guarantor_phone')
        
        customer = Customer.objects.create(
            full_name=full_name,
            email=email,
            phone=phone,
            occupation=occupation,
            income_amount=income_amount,
            region=region,
            district=district,
            location=location,
            guarantor_name=guarantor_name,
            guarantor_phone=guarantor_phone,
            registered_by=request.user
        )
        
        username = phone
        password = f"customer{phone[-4:]}"
        user = User.objects.create_user(username=username, password=password, email=email)
        customer.user = user
        customer.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='customer_registration',
            customer=customer,
            details=f"Registered new customer: {full_name}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'Customer {full_name} registered successfully!')
        messages.info(request, f'Customer login: {username} | Password: {password}')
        
        return redirect('/staff/register-customer/')
    
    return render(request, 'staff_panel/register_customer.html')

@login_required
@user_passes_test(is_staff_user)
def create_installment_plan(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        device_model = request.POST.get('device_model')
        down_payment = Decimal(request.POST.get('down_payment'))
        frequency = request.POST.get('frequency')
        
        # Get iPhone price
        iphone_prices = {
            'iPhone 14': 8500,
            'iPhone 14 Pro': 11000,
            'iPhone 14 Pro Max': 12500,
            'iPhone 15': 10500,
            'iPhone 15 Pro': 14000,
            'iPhone 15 Pro Max': 16000,
            'iPhone 16': 18000,
        }
        
        total_price = iphone_prices.get(device_model, 0)
        remaining_balance = total_price - down_payment
        
        # Calculate installments
        if frequency == 'daily':
            total_installments = 180
            installment_amount = remaining_balance / 180
            days_to_add = 1
        elif frequency == 'weekly':
            total_installments = 26
            installment_amount = remaining_balance / 26
            days_to_add = 7
        else:  # monthly
            total_installments = 6
            installment_amount = remaining_balance / 6
            days_to_add = 30
        
        # Create device
        device = IphoneDevice.objects.create(
            model=device_model,
            serial_number=f"TRITECH-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            price=total_price,
            customer=customer,
            is_locked=False
        )
        
        # Create installment plan
        plan = InstallmentPlan.objects.create(
            customer=customer,
            device=device,
            total_price=total_price,
            down_payment=down_payment,
            remaining_balance=remaining_balance,
            frequency=frequency,
            installment_amount=installment_amount,
            total_installments=total_installments,
            payments_made=0,
            status='active',
            start_date=datetime.now().date(),
            next_due_date=datetime.now().date() + timedelta(days=days_to_add)
        )
        
        AuditLog.objects.create(
            user=request.user,
            action='plan_created',
            customer=customer,
            device=device,
            details=f"Created {frequency} installment plan for {device_model}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'Installment plan created for {customer.full_name}!')
        messages.info(request, f'Installment amount: GHS {installment_amount:.2f} per {frequency}')
        
        return redirect('/staff/customers/')
    
    context = {
        'customer': customer,
        'iphone_prices': {
            'iPhone 14': 8500,
            'iPhone 14 Pro': 11000,
            'iPhone 14 Pro Max': 12500,
            'iPhone 15': 10500,
            'iPhone 15 Pro': 14000,
            'iPhone 15 Pro Max': 16000,
            'iPhone 16': 18000,
        }
    }
    return render(request, 'staff_panel/create_plan.html', context)

@login_required
@user_passes_test(is_staff_user)
def customer_list(request):
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'staff_panel/customers.html', {'customers': customers})
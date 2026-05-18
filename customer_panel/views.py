from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Customer, InstallmentPlan, Payment
from datetime import datetime, timedelta

@login_required
def customer_dashboard(request):
    try:
        customer = request.user.customer
        plans = InstallmentPlan.objects.filter(customer=customer, status='active')
        payments = Payment.objects.filter(customer=customer).order_by('-paid_at')[:10]
        
        active_plan = plans.first()
        
        next_payment = None
        if active_plan:
            days_left = (active_plan.next_due_date - datetime.now().date()).days
            next_payment = {
                'due_date': active_plan.next_due_date,
                'amount': active_plan.installment_amount,
                'days_left': days_left
            }
        
        context = {
            'customer': customer,
            'active_plan': active_plan,
            'next_payment': next_payment,
            'payments': payments,
            'device': active_plan.device if active_plan else None,
        }
        return render(request, 'customer_panel/dashboard.html', context)
    except Customer.DoesNotExist:
        messages.error(request, 'Customer profile not found. Please contact support.')
        return redirect('/logout/')

@login_required
def payment_history(request):
    customer = request.user.customer
    payments = Payment.objects.filter(customer=customer).order_by('-paid_at')
    return render(request, 'customer_panel/payment_history.html', {'payments': payments})

@login_required
def make_payment(request, plan_id):
    plan = get_object_or_404(InstallmentPlan, id=plan_id, customer=request.user.customer)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'mobile_money')
        
        payment = Payment.objects.create(
            installment_plan=plan,
            customer=request.user.customer,
            amount=plan.installment_amount,
            payment_method=payment_method,
            status='completed',
            paid_at=datetime.now(),
            due_date=plan.next_due_date
        )
        
        plan.payments_made += 1
        plan.remaining_balance -= plan.installment_amount
        plan.last_payment_date = datetime.now().date()
        
        if plan.frequency == 'daily':
            plan.next_due_date += timedelta(days=1)
        elif plan.frequency == 'weekly':
            plan.next_due_date += timedelta(days=7)
        else:
            plan.next_due_date += timedelta(days=30)
        
        if plan.payments_made >= plan.total_installments:
            plan.status = 'completed'
        
        plan.save()
        
        messages.success(request, f'Payment of GHS {plan.installment_amount} successful!')
        return redirect('/customer/')
    
    context = {
        'plan': plan,
        'amount': plan.installment_amount,
        'due_date': plan.next_due_date,
    }
    return render(request, 'customer_panel/make_payment.html', context)
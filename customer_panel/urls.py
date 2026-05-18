from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_dashboard, name='customer_dashboard'),
    path('payment-history/', views.payment_history, name='payment_history'),
    path('make-payment/<int:plan_id>/', views.make_payment, name='make_payment'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.staff_dashboard, name='staff_dashboard'),
    path('register-customer/', views.register_customer, name='register_customer'),
    path('customers/', views.customer_list, name='customer_list'),
    path('create-plan/<int:customer_id>/', views.create_installment_plan, name='create_plan'),
]
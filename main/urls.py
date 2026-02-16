from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('bookings/', views.bookings, name='bookings'),
    path('services/', views.services, name='services'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('privacy-policy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('api/eligibility-submit/', views.eligibility_submit, name='eligibility_submit'),
]

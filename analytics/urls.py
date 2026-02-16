# analytics/urls.py
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard-data/', views.dashboard_data, name='dashboard_data'),
    path('traffic-stats/', views.traffic_stats, name='traffic_stats'),
    path('traffic-data/', views.traffic_data, name='traffic_data'),
    path('location-data/', views.location_data, name='location_data'),
    path('traffic-sources-detail/', views.traffic_sources_detail, name='traffic_sources_detail'),
]
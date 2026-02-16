from django.urls import path
from . import views

app_name = 'media_manager'

urlpatterns = [
    path('', views.media_library, name='media_library'),

]

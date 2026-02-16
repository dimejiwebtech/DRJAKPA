from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat, name='chat'),
    path('init/', views.initialize_session, name='chat_init'),
    path('send/', views.send_message, name='chat_send'),
    path('history/<uuid:session_id>/', views.get_chat_history, name='chat_history'),
]

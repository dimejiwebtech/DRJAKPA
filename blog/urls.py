from django.urls import path
from . import views

urlpatterns = [
    path('', views.blog, name='blog'),
    path('load-more/', views.load_more, name='load_more'),
    path('search/', views.search, name='search'),
    path('<slug:slug>/', views.posts_by_category_or_post, name='posts_by_category_or_post')
]
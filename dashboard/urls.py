from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    # Posts
    path('posts/', views.posts, name='posts'),
    path('posts/bulk-action/', views.bulk_action, name='bulk_action'),
    path('posts/add-post/', views.add_post, name='add_post'),
    path('posts/edit-post/<int:pk>/', views.edit_post, name='edit_post'),
    path('posts/delete-post/<int:pk>/', views.delete_post, name='delete_post'),
    path('posts/restore-post/<int:pk>/', views.restore_post, name='restore_post'),
    path('post-preview/<int:pk>/', views.preview_post, name='preview_post'),
    path('auto-save-post/', views.auto_save_post, name='auto_save_post'),
    path('generate-slug/', views.generate_slug_ajax, name='generate_slug'),
    path('remove-featured-image/', views.remove_featured_image, name='remove_featured_image'),

    # categories, add, edit, view & delete
    path('posts/categories/', views.categories, name='categories'),
    path('posts/categories/add/', views.add_category, name='add_category'),
    path('posts/categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('posts/categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    path('categories/<slug:slug>/', views.view_category, name='view_category'),
    # categories, add, edit, view & delete

    # comments
    path('comments/', views.comment, name='comments'),
    path('comments/bulk-action/', views.bulk_comment_action, name='bulk_comment_action'),
    path('comments/approve/<int:comment_id>/', views.comment_approve, name='comment_approve'),
    path('comments/unapprove/<int:comment_id>/', views.comment_unapprove, name='comment_unapprove'),
    path('comments/delete/<int:comment_id>/', views.comment_delete, name='comment_delete'),
    path('comments/edit/<int:comment_id>/', views.comment_edit, name='comment_edit'),
    path('comments/reply/<int:comment_id>/', views.comment_reply, name='comment_reply'),
    # comments


    # Media Library
    path('media/', views.media_library, name='media_library'),
    path('media/add-media/', views.add_media, name='add_media'),
    path('media/upload/', views.add_media, name='media_upload'), 
    path('media/<int:media_id>/', views.media_detail, name='media_detail'),
    path('media/<int:media_id>/update/', views.update_media, name='media_update'),
    path('media/<int:media_id>/delete/', views.delete_media, name='media_delete'),
    path('media/bulk-delete/', views.bulk_delete_media, name='media_bulk_delete'),
    
    # Booking Management
    path('bookings/', views.bookings_list, name='bookings_list'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/update/', views.booking_update, name='booking_update'),
    path('bookings/<int:booking_id>/status/', views.booking_update_status, name='booking_update_status'),
    path('bookings/<int:booking_id>/delete/', views.booking_delete, name='booking_delete'),
    
    # Session Management
    path('sessions/', views.sessions_list, name='sessions_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<int:session_id>/update/', views.session_update, name='session_update'),
    path('sessions/<int:session_id>/delete/', views.session_delete, name='session_delete'),

    # Users
    path('users/', views.user_list, name='users'),
    path('users/add-user/', views.add_user, name='add_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/profile/', views.profile, name='profile'),
    path('users/<int:user_id>/profile/', views.profile, name='profile'),
    
    # Users

    # Testimonials
    path('testimonials/', views.testimonials, name='testimonials'),
    path('testimonials/add/', views.add_testimonial, name='add_testimonial'),
    path('testimonials/<int:pk>/edit/', views.edit_testimonial, name='edit_testimonial'),
    path('testimonials/<int:pk>/delete/', views.delete_testimonial, name='delete_testimonial'),
    # Testimonials

    # Team
    path('team/', views.team_list, name='team_list'),
    path('team/add/', views.add_team_member, name='add_team_member'),
    path('team/<int:pk>/edit/', views.edit_team_member, name='edit_team_member'),
    path('team/<int:pk>/delete/', views.delete_team_member, name='delete_team_member'),
    # Team
]
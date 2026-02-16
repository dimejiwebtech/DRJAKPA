from django.contrib import admin
from .models import Post, Category, Comment, UserProfile
from django.utils.html import format_html
from django.utils import timezone


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    ordering = ['name'] 


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'is_featured', 'published_date', 'is_trashed']
    list_filter = ['status', 'is_featured', 'is_trashed', 'category', 'created_at']
    list_editable = ['status', 'is_featured']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['category']
    date_hierarchy = 'published_date'
    ordering = ['-published_date']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'content', 'excerpt', 'featured_image')
        }),
        ('Publishing', {
            'fields': ('author', 'status', 'published_date', 'is_featured')
        }),
        ('Categories', {
            'fields': ('category',)
        }),
        ('SEO', {
            'fields': ('seo_description', 'seo_keywords'),
            'classes': ('collapse',)
        }),
        ('Trash', {
            'fields': ('is_trashed', 'trashed_at', 'trashed_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['trashed_at', 'trashed_by']
    
    def get_queryset(self, request):
        # Show all posts in admin including trashed
        return Post.all_objects.all()
    
    actions = ['move_to_trash', 'restore_from_trash', 'mark_as_published', 'mark_as_draft']
    
    @admin.action(description='Move selected posts to trash')
    def move_to_trash(self, request, queryset):
        for post in queryset:
            post.move_to_trash(user=request.user)
        self.message_user(request, f'{queryset.count()} post(s) moved to trash.')
    
    @admin.action(description='Restore selected posts from trash')
    def restore_from_trash(self, request, queryset):
        for post in queryset:
            post.restore_from_trash()
        self.message_user(request, f'{queryset.count()} post(s) restored.')
    
    @admin.action(description='Mark selected as published')
    def mark_as_published(self, request, queryset):
        queryset.update(status='published')
        self.message_user(request, f'{queryset.count()} post(s) marked as published.')
    
    @admin.action(description='Mark selected as draft')
    def mark_as_draft(self, request, queryset):
        queryset.update(status='draft')
        self.message_user(request, f'{queryset.count()} post(s) marked as draft.')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'post', 'created_on', 'approved']
    list_filter = ['approved', 'created_on']
    list_editable = ['approved']
    search_fields = ['name', 'email', 'body']
    ordering = ['-created_on']
    
    actions = ['approve_comments', 'reject_comments']
    
    @admin.action(description='Approve selected comments')
    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
        self.message_user(request, f'{queryset.count()} comment(s) approved.')
    
    @admin.action(description='Reject selected comments')
    def reject_comments(self, request, queryset):
        queryset.update(approved=False)
        self.message_user(request, f'{queryset.count()} comment(s) rejected.')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'bio')
    search_fields = ('user__username', 'user__email', 'bio')
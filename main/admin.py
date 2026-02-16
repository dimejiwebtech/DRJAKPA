from django.contrib import admin
from .models import EligibilityAssessment, SessionTime, Booking, Testimonial, Faq


@admin.register(SessionTime)
class SessionTimeAdmin(admin.ModelAdmin):
    list_display = ['date', 'time', 'is_available', 'created_at']
    list_filter = ['is_available', 'date']
    list_editable = ['is_available']
    date_hierarchy = 'date'
    ordering = ['date', 'time']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'session_time', 'duration_hours', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'session_time__date']
    search_fields = ['full_name', 'email', 'whatsapp_number']
    readonly_fields = ['total_price', 'created_at', 'updated_at']
    list_editable = ['status']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('full_name', 'email', 'whatsapp_number')
        }),
        ('Booking Details', {
            'fields': ('session_time', 'duration_hours', 'total_price', 'status')
        }),
        ('Payment', {
            'fields': ('payment_screenshot',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EligibilityAssessment)
class EligibilityAssessmentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'category', 'score', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['full_name', 'email']
    readonly_fields = ['created_at']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_editable = ['is_active']
    list_display = ['name', 'location', 'is_active', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'location']
    readonly_fields = ['created_at']


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ['question', 'created_at']
    list_filter = ['created_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['created_at']
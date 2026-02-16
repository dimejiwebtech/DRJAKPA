# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.admin.views.main import ChangeList
from django.contrib import messages
from .models import MediaFile


class MediaFileChangeList(ChangeList):
    
    def get_filters_params(self, params=None):
        return super().get_filters_params(params)

class MediaTypeListFilter(admin.SimpleListFilter):
    title = 'Media Type'
    parameter_name = 'media_type'

    def lookups(self, request, model_admin):
        return [
            ('all', 'All Media'),
            ('image', 'Images'),
            ('document', 'Documents'),
            ('spreadsheet', 'Spreadsheets'),
            ('video', 'Videos'),
            ('audio', 'Audio'),
            ('other', 'Other'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'all' or self.value() is None:
            return queryset
        elif self.value() in ['image', 'document', 'spreadsheet', 'video', 'audio', 'other']:
            return queryset.filter(category=self.value())
        return queryset


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('file_preview', 'file_name', 'file_type_display', 'file_size_display', 'created_at')
    list_filter = (MediaTypeListFilter, 'created_at')
    search_fields = ('file', 'alt_text', 'description')
    list_per_page = 20
    actions = ['bulk_delete_files', 'bulk_download_files', 'bulk_change_category']
    
    # Custom fields for list display
    readonly_fields = ('file_preview_large', 'file_size_display', 'file_type_display')
    
    fieldsets = (
        ('File Information', {
            'fields': ('file', 'file_preview_large')
        }),
        ('Details', {
            'fields': ('alt_text', 'description', 'category')
        }),
        ('Metadata', {
            'fields': ('file_size_display', 'file_type_display',),
            'classes': ('collapse',)
        })
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('media-library/', self.admin_site.admin_view(self.media_library_view), name='media-library'),
        ]
        return custom_urls + urls

    def media_library_view(self, request):
        media_files = MediaFile.objects.all().order_by('-created_at')
        
        # Handle filtering
        media_type = request.GET.get('type', 'all')
        if media_type != 'all':
            media_files = media_files.filter(category=media_type)
        
        context = dict(
            self.admin_site.each_context(request),
            media_files=media_files,
            media_type=media_type,
        )
        return TemplateResponse(request, "admin/media_library.html", context)

    def file_preview(self, obj):
        if obj.file_type == 'image':
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.file.url
            )
        else:
            return format_html(
                '<div style="width: 50px; height: 50px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-size: 12px; font-weight: bold;">{}</div>',
                obj.file_extension or '📄'
            )
    file_preview.short_description = 'Preview'

    def file_preview_large(self, obj):
        if obj.file_type == 'image':
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; object-fit: contain;" />',
                obj.file.url
            )
        else:
            return format_html(
                '<div style="width: 200px; height: 200px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; font-size: 48px;">{}</div>',
                obj.file_extension or '📄'
            )
    file_preview_large.short_description = 'Preview'

    def file_name(self, obj):
        return format_html(
            '<a href="{}" target="_blank" title="View file">{}</a>',
            obj.file.url,
            obj.__str__()
        )
    file_name.short_description = 'File Name'

    def file_type_display(self, obj):
        type_icons = {
            'image': '🖼️',
            'document': '📄',
            'spreadsheet': '📊',
            'video': '🎥',
            'audio': '🎵',
            'other': '📁'
        }
        icon = type_icons.get(obj.file_type, '📁')
        return format_html('{} {}', icon, obj.file_type.title())
    file_type_display.short_description = 'Type'

    def file_size_display(self, obj):
        return obj.file_size
    file_size_display.short_description = 'Size'

    # Bulk Actions
    def bulk_delete_files(self, request, queryset):
        count = queryset.count()
        for obj in queryset:
            obj.delete()
        messages.success(request, f'Successfully deleted {count} files.')
    bulk_delete_files.short_description = "Delete selected files"
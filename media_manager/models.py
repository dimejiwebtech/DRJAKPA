from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import os
from django.utils.html import format_html

User = get_user_model()

ALLOWED_EXTENSIONS = [
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico',
    # Documents
    'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
    # Spreadsheets
    'xls', 'xlsx', 'csv', 'ods',
    # Presentations
    'ppt', 'pptx', 'odp',
    # Audio
    'mp3', 'wav', 'ogg', 'm4a', 'flac',
    # Video
    'mp4', 'mov', 'avi', 'mkv', 'wmv', 'webm',
]

class MediaFileManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter out records where files don't exist
        existing_files = []
        for obj in queryset:
            if obj.file and obj.file.storage.exists(obj.file.name):
                existing_files.append(obj.id)
            else:
                # Silently delete orphaned records
                obj.delete()
        return super().get_queryset().filter(id__in=existing_files)
    
    def all_including_missing(self):
        return super().get_queryset()


class MediaFile(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('document', 'Document'),
        ('spreadsheet', 'Spreadsheet'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other')
    ]
    
    file = models.FileField(
        upload_to='uploads/',
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS)]
    )
    alt_text = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=MEDIA_TYPES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = MediaFileManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Media File'
        verbose_name_plural = 'Media Library'

    def __str__(self):
        return os.path.basename(self.file.name) if self.file else 'File'

    def delete(self, *args, **kwargs):
        # Delete the file from storage
        if self.file and self.file.storage.exists(self.file.name):
            self.file.delete(save=False)
        super().delete(*args, **kwargs)

    @property
    def file_type(self):
        if not self.file:
            return 'other'
        
        name = self.file.name.lower()
        if name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp')):
            return 'image'
        elif name.endswith(('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv')):
            return 'video'
        elif name.endswith(('.mp3', '.wav', '.ogg', '.m4a', '.flac')):
            return 'audio'
        elif name.endswith(('.pdf', '.docx', '.pptx', '.doc', '.txt', '.rtf')):
            return 'document'
        elif name.endswith(('.xlsx', '.xls', '.csv', '.ods')):
            return 'spreadsheet'
        return 'other'

    @property
    def file_size(self):
        if not self.file:
            return "0 bytes"
        
        try:
            size = self.file.size
            for unit in ['bytes', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Unknown size"

    @property
    def file_extension(self):
        if not self.file:
            return ""
        return os.path.splitext(self.file.name)[1].upper().lstrip('.')

    def save(self, *args, **kwargs):
        # Auto-set category based on file type if not already set
        if not self.category or self.category == 'other':
            self.category = self.file_type
        super().save(*args, **kwargs)

    def get_thumbnail_url(self):
        if self.file_type == 'image':
            return self.file.url
        return None

    def get_preview_html(self):
        if self.file_type == 'image':
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; object-fit: cover;" />',
                self.file.url
            )
        else:
            return format_html(
                '<div style="width: 100px; height: 100px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; font-size: 24px;">{}</div>',
                self.file_extension or '📄'
            )
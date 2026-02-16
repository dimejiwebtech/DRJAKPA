from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from tinymce.models import HTMLField

class BaseContentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_trashed=False)
    
    def trashed(self):
        return self.filter(is_trashed=True)
    
    def published(self):
        return self.active().filter(status='published')


class PostManager(models.Manager):
    def get_queryset(self):
        return BaseContentQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def published(self):
        return self.get_queryset().published()


class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    
    # Basic Info
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    content = HTMLField()
    excerpt = models.TextField(blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    featured_image = models.ImageField(upload_to='blog/', null=True, blank=True)
    category = models.ManyToManyField('Category', blank=True, related_name='posts')
    is_featured = models.BooleanField(default=False)
    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_date = models.DateTimeField(default=timezone.now)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # SEO
    seo_description = models.TextField(max_length=160, null=True, blank=True)
    seo_keywords = models.CharField(max_length=255, blank=True, null=True)
    
    # Soft Delete
    is_trashed = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(null=True, blank=True)
    trashed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='trashed_%(class)s')
    read_time = models.PositiveIntegerField(default=0, help_text="Estimated reading time in minutes")

    objects = PostManager()
    all_objects = models.Manager()
    
    class Meta:
        ordering = ['-published_date']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def calculate_read_time(self):
        plain_text = strip_tags(self.content)
        word_count = len(plain_text.split())
        words_per_minute = 200
        return math.ceil(word_count / words_per_minute) if word_count > 0 else 0
    
    
    def move_to_trash(self, user=None):
        self.is_trashed = True
        self.trashed_at = timezone.now()
        self.trashed_by = user
        self.save(update_fields=['is_trashed', 'trashed_at', 'trashed_by'])
    
    def restore_from_trash(self):
        self.is_trashed = False
        self.trashed_at = None
        self.trashed_by = None
        self.save(update_fields=['is_trashed', 'trashed_at', 'trashed_by'])
    
    @property
    def days_in_trash(self):
        if self.is_trashed and self.trashed_at:
            return (timezone.now() - self.trashed_at).days
        return 0
    
    @property
    def can_auto_delete(self):
        return self.days_in_trash >= 30


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']  
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return f'Comment by {self.name} on {self.post}'
    
    @property
    def replies(self):
        return self.comment_replies.filter(approved=True)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='team/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update User model fields
        if self.first_name != self.user.first_name or self.last_name != self.user.last_name:
            User.objects.filter(pk=self.user.pk).update(
                first_name=self.first_name,
                last_name=self.last_name
            )

    def __str__(self):
        return f"{self.user.username}'s profile"

from django.db import models
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta

class PageView(models.Model):
    TRAFFIC_SOURCES = [
        ('direct', 'Direct'),
        ('social', 'Social'),
        ('search', 'Search Engine'),
        ('referral', 'Referral'),
    ]
    
    page_url = models.CharField(max_length=255)
    page_title = models.CharField(max_length=255, blank=True)
    traffic_source = models.CharField(max_length=20, choices=TRAFFIC_SOURCES, default='direct')
    referrer = models.URLField(blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)  
    region = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    referrer_domain = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['page_url', 'date']),
            models.Index(fields=['traffic_source', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.page_url} - {self.date}"

class AnalyticsManager:
    @staticmethod
    def get_views_by_period(queryset, period='today'):
        today = timezone.now().date()
        
        if period == 'today':
            return queryset.filter(date=today).count()
        elif period == 'week':
            start_week = today - timedelta(days=today.weekday())
            return queryset.filter(date__gte=start_week).count()
        elif period == 'month':
            start_month = today.replace(day=1)
            return queryset.filter(date__gte=start_month).count()
        elif period == 'year':
            start_year = today.replace(month=1, day=1)
            return queryset.filter(date__gte=start_year).count()
        
        return queryset.count()
    
    @staticmethod
    def get_traffic_sources(queryset, period='today'):
        today = timezone.now().date()
        
        if period == 'today':
            filtered = queryset.filter(date=today)
        elif period == 'week':
            start_week = today - timedelta(days=today.weekday())
            filtered = queryset.filter(date__gte=start_week)
        elif period == 'month':
            start_month = today.replace(day=1)
            filtered = queryset.filter(date__gte=start_month)
        elif period == 'year':
            start_year = today.replace(month=1, day=1)
            filtered = queryset.filter(date__gte=start_year)
        else:
            filtered = queryset
            
        return filtered.values('traffic_source').annotate(count=models.Count('id'))

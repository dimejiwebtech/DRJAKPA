# analytics/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.shortcuts import render
from django.db.models import Count

from analytics.models import PageView
from .services import AnalyticsService

@login_required
@require_GET
def dashboard_data(request):
    period = request.GET.get('period', 'week')
    
    if period not in ['today', 'week', 'month', 'year']:
        period = 'week'
    
    data = AnalyticsService.get_dashboard_data(period)
    return JsonResponse(data)

@login_required
def traffic_stats(request):

    return render(request, 'analytics/traffic_stats.html')

@login_required 
@require_GET
def traffic_data(request):

    period = request.GET.get('period', 'week')
    
    if period not in ['today', 'week', 'month', 'year']:
        period = 'week'
    
    dashboard_data = AnalyticsService.get_dashboard_data(period)
    blog_data = AnalyticsService.get_blog_analytics(period)
    chart_data = AnalyticsService.get_chart_data(period)
    
    return JsonResponse({
        **dashboard_data,
        'blog_analytics': blog_data,
        'chart_data': chart_data
    })

@login_required
@require_GET
def location_data(request):

    location_type = request.GET.get('type', 'countries')
    period = request.GET.get('period', 'week')
    
    if location_type not in ['countries', 'regions']:
        location_type = 'countries'
    
    if period not in ['today', 'week', 'month', 'year']:
        period = 'week'
    
    # Get location data from your service
    location_data = AnalyticsService.get_location_data(location_type, period)
    
    return JsonResponse({
        'locations': location_data
    })

@login_required
@require_GET
def traffic_sources_detail(request):

    source_type = request.GET.get('type', 'search')
    period = request.GET.get('period', 'week')
    
    page_views = AnalyticsService._filter_by_period(PageView.objects.all(), period)
    
    if source_type == 'direct':
        # For direct traffic, show page titles instead of domains
        sources = page_views.filter(traffic_source='direct').values('page_title').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return JsonResponse({
            'sources': [
                {
                    'domain': source['page_title'] or 'Homepage',
                    'count': source['count']
                } for source in sources
            ]
        })
    else:
        # For other sources, filter out null/empty domains
        sources = page_views.filter(
            traffic_source=source_type
        ).exclude(
            referrer_domain__isnull=True
        ).exclude(
            referrer_domain=''
        ).values('referrer_domain').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return JsonResponse({
            'sources': [
                {
                    'domain': source['referrer_domain'],
                    'count': source['count']
                } for source in sources
            ]
        })
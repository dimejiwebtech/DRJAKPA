# analytics/services.py
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import PageView, AnalyticsManager


class AnalyticsService:

    @staticmethod
    def get_dashboard_data(period='today'):
        page_views = PageView.objects.all()
        chart_data_result = AnalyticsService.get_chart_data(period)
        filtered = AnalyticsService._filter_by_period(page_views, period)

        unique_visitors = filtered.values('ip_address').distinct().count()

        location_data = AnalyticsService.get_location_data('countries', period)

        return {
            'total_views': AnalyticsManager.get_views_by_period(page_views, period),
            'unique_visitors': unique_visitors,
            'traffic_sources': list(AnalyticsManager.get_traffic_sources(page_views, period)),
            'top_pages': AnalyticsService.get_top_pages(period),
            'chart_data': chart_data_result,
            'labels': [item['label'] for item in chart_data_result],
            'top_referrers': AnalyticsService.get_top_referrers(period),
            'locations': location_data,
        }

    @staticmethod
    def get_top_pages(period='today', limit=10):
        page_views = PageView.objects.all()
        filtered_views = AnalyticsService._filter_by_period(page_views, period)
        return list(
            filtered_views
            .values('page_url', 'page_title')
            .annotate(views=Count('id'))
            .order_by('-views')[:limit]
        )

    @staticmethod
    def get_blog_analytics(period='today'):
        blog_views = PageView.objects.filter(page_url__startswith='/blog/')
        return {
            'total_blog_views': AnalyticsManager.get_views_by_period(blog_views, period),
            'blog_traffic_sources': list(AnalyticsManager.get_traffic_sources(blog_views, period)),
            'top_blog_posts': list(
                AnalyticsService._filter_by_period(blog_views, period)
                .values('page_url', 'page_title')
                .annotate(views=Count('id'))
                .order_by('-views')[:5]
            ),
        }

    @staticmethod
    def _filter_by_period(queryset, period):
        today = timezone.now().date()

        if period == 'today':
            return queryset.filter(date=today)
        elif period == 'week':
            start_week = today - timedelta(days=today.weekday())
            return queryset.filter(date__gte=start_week)
        elif period == 'month':
            start_month = today.replace(day=1)
            return queryset.filter(date__gte=start_month)
        elif period == 'year':
            start_year = today.replace(month=1, day=1)
            return queryset.filter(date__gte=start_year)

        return queryset

    @staticmethod
    def get_chart_data(period='week'):
        today = timezone.now().date()
        now = timezone.now()

        if period == 'today':
            # Hourly breakdown for today (0–23)
            data = []
            for hour in range(24):
                count = PageView.objects.filter(
                    date=today,
                    timestamp__hour=hour,
                ).count()
                # Format: 12am, 1am … 12pm, 1pm …
                if hour == 0:
                    label = '12am'
                elif hour < 12:
                    label = f'{hour}am'
                elif hour == 12:
                    label = '12pm'
                else:
                    label = f'{hour - 12}pm'
                data.append({'label': label, 'value': count})

        elif period == 'week':
            # Last 4 weeks Mon→Sun
            data = []
            for i in range(3, -1, -1):
                week_end = today - timedelta(days=i * 7)
                week_start = week_end - timedelta(days=6)
                count = PageView.objects.filter(
                    date__range=[week_start, week_end]
                ).count()
                data.append({
                    'label': f"{week_start.strftime('%b %d')}–{week_end.strftime('%d')}",
                    'value': count,
                })

        elif period == 'month':
            # Last 6 calendar months
            data = []
            for i in range(5, -1, -1):
                month_date = (today.replace(day=1) - timedelta(days=32 * i)).replace(day=1)
                next_month = (month_date + timedelta(days=32)).replace(day=1)
                count = PageView.objects.filter(
                    date__gte=month_date,
                    date__lt=next_month,
                ).count()
                data.append({
                    'label': month_date.strftime('%b %Y'),
                    'value': count,
                })

        else:  # year
            # Last 3 years
            data = []
            current_year = today.year
            for i in range(2, -1, -1):
                year = current_year - i
                count = PageView.objects.filter(date__year=year).count()
                data.append({'label': str(year), 'value': count})

        return data

    @staticmethod
    def get_location_data(location_type, period='week'):
        page_views = PageView.objects.all()
        filtered_views = AnalyticsService._filter_by_period(page_views, period)

        if location_type == 'countries':
            location_data = list(
                filtered_views
                .exclude(country__isnull=True)
                .exclude(country='')
                .exclude(country='Local')
                .values('country')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
            return [{'name': item['country'], 'count': item['count']} for item in location_data]

        else:
            location_data = list(
                filtered_views
                .exclude(city__isnull=True)
                .exclude(city='')
                .exclude(city='Local')
                .values('city', 'region')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
            return [
                {
                    'name': f"{item['city']}, {item['region']}" if item['region'] else item['city'],
                    'count': item['count'],
                }
                for item in location_data
            ]

    @staticmethod
    def get_top_referrers(period='today', limit=5):
        page_views = PageView.objects.all()
        filtered_views = AnalyticsService._filter_by_period(page_views, period)
        return list(
            filtered_views
            .exclude(traffic_source='direct')
            .exclude(referrer_domain__isnull=True)
            .exclude(referrer_domain='')
            .values('referrer_domain', 'traffic_source')
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]
        )
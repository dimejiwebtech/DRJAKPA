# analytics/middleware.py
import re
import time
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import PageView
from .utils import TrafficSourceDetector, TRACKED_PAGES

# UA patterns to skip
BOT_PATTERN = re.compile(
    r'(bot|crawler|spider|slurp|facebookexternalhit|Twitterbot|python-requests'
    r'|curl|wget|headless|chrome-lighthouse|lighthouse|prerender|Googlebot'
    r'|bingbot|YandexBot|DuckDuckBot)',
    re.IGNORECASE
)

# Simple in-process dedup cache: {(ip, path): last_recorded_timestamp}
_dedup_cache: dict = {}
DEDUP_WINDOW = 600  # 10 minutes in seconds


class AnalyticsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Only track GET requests with 200 status
        if request.method != 'GET' or response.status_code != 200:
            return response

        # Skip admin, static files, and API endpoints
        skip_prefixes = [
            '/admin/', '/static/', '/media/', '/api/',
            '/analytics/', '/dashboard/',
        ]
        if any(request.path.startswith(p) for p in skip_prefixes):
            return response

        # Skip authenticated staff, superusers, administrators, and authors
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return response
            if request.user.groups.filter(
                name__in=['Administrator', 'Author']
            ).exists():
                return response

        # Skip bots and crawlers
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent or BOT_PATTERN.search(user_agent):
            return response

        # Deduplicate: same IP + same page within 10 minutes = skip
        ip_address = self.get_client_ip(request)
        dedup_key = (ip_address, request.path)
        now = time.time()
        last_seen = _dedup_cache.get(dedup_key, 0)
        if now - last_seen < DEDUP_WINDOW:
            return response
        _dedup_cache[dedup_key] = now

        # Prune cache if it grows too large (keep memory bounded)
        if len(_dedup_cache) > 5000:
            cutoff = now - DEDUP_WINDOW
            expired = [k for k, v in _dedup_cache.items() if v < cutoff]
            for k in expired:
                _dedup_cache.pop(k, None)

        try:
            self.track_page_view(request, ip_address, user_agent)
        except Exception:
            pass

        return response

    def track_page_view(self, request, ip_address, user_agent):
        referrer = request.META.get('HTTP_REFERER', '')
        traffic_source = TrafficSourceDetector.detect_source(referrer)

        # Get page title
        page_title = TRACKED_PAGES.get(request.path, '')

        # Handle blog posts dynamically
        if request.path.startswith('/blog/') and not page_title:
            try:
                resolved = resolve(request.path)
                if hasattr(resolved, 'kwargs') and 'slug' in resolved.kwargs:
                    page_title = (
                        f"Blog: {resolved.kwargs['slug'].replace('-', ' ').title()}"
                    )
                else:
                    page_title = 'Blog Post'
            except Exception:
                page_title = 'Blog'

        # Skip if page not in tracking list and not a blog post
        if not page_title:
            return

        # Extract referrer domain
        referrer_domain = None
        if referrer and traffic_source != 'direct':
            try:
                from urllib.parse import urlparse
                parsed = urlparse(referrer)
                if parsed.netloc:
                    referrer_domain = parsed.netloc.lower().replace('www.', '')
            except Exception:
                pass

        location_data = self.get_location_from_ip(ip_address)

        PageView.objects.create(
            page_url=request.path,
            page_title=page_title,
            traffic_source=traffic_source,
            referrer=referrer if referrer else None,
            referrer_domain=referrer_domain,
            ip_address=ip_address,
            user_agent=user_agent[:500],
            country=location_data['country'],
            city=location_data['city'],
            region=location_data['region'],
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def get_location_from_ip(self, ip_address):
        try:
            if ip_address in ('127.0.0.1', 'localhost') or \
               ip_address.startswith(('192.168.', '10.', '172.')):
                return {'country': 'Local', 'city': 'Local', 'region': 'Local'}

            import requests as req
            response = req.get(
                f'http://ip-api.com/json/{ip_address}',
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country', ''),
                    'city': data.get('city', ''),
                    'region': data.get('regionName', ''),
                }
        except Exception:
            pass
        return {'country': '', 'city': '', 'region': ''}
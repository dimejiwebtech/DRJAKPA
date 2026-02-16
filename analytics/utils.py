# analytics/utils.py
import re
from urllib.parse import urlparse

class TrafficSourceDetector:
    SEARCH_ENGINES = [
        'google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com',
        'yandex.com', 'baidu.com', 'ask.com'
    ]
    
    SOCIAL_PLATFORMS = [
        'facebook.com', 'twitter.com', 'x.com', 'linkedin.com',
        'instagram.com', 'youtube.com', 'tiktok.com', 'pinterest.com',
        'reddit.com', 'telegram.org', 'whatsapp.com', 'medium.com', 'threads.com'
    ]
    
    @classmethod
    def detect_source(cls, referrer):
        if not referrer:
            return 'direct'
        
        try:
            domain = urlparse(referrer).netloc.lower()
            
            # Remove www prefix
            domain = re.sub(r'^www\.', '', domain)
            
            # Check if referrer is from same domain (internal navigation)
            if 'doclumina.org' in domain:
                return 'direct'
            
            if any(search in domain for search in cls.SEARCH_ENGINES):
                return 'search'
            elif any(social in domain for social in cls.SOCIAL_PLATFORMS):
                return 'social'
            else:
                return 'referral'
        except:
            return 'direct'

# Page tracking configuration
TRACKED_PAGES = {
    # Main app pages
    '/': 'Homepage',
    '/about/': 'About Us',
    '/contact/': 'Contact Us',
    '/bookings/': 'Book an Appointment',
    '/services/': 'Our Services',
    '/disclaimer/': 'Disclaimer',
    '/privacy-policy/': 'Privacy Policy',
    '/terms/': 'Terms and Conditions',
    
    # Blog pages 
    '/blog/': 'Blog',
}
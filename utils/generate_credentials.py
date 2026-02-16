from django.utils import timezone
import pytz
from main.models import GmailToken
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from django.conf import settings

class GmailCredentialsManager:
    """Centralized Gmail credentials management"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self):
        self.client_secret_path = settings.GMAIL_CLIENT_SECRET_PATH
    
    def get_credentials(self):
        """Get valid Gmail API credentials"""
        creds = self._load_credentials()
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                if self._refresh_credentials(creds):
                    return creds
            
            # If refresh fails or no refresh token, need new authorization
            raise Exception(
                "Gmail credentials are invalid or expired. "
                "Please run: python manage.py generate_gmail_token"
            )
        
        return creds
    
    def _load_credentials(self):
        """Load credentials from database"""
        try:
            token_obj = GmailToken.objects.first()
            if not token_obj:
                return None
                
            # Convert expiry to UTC naive datetime (what Google expects)
            expiry = None
            if token_obj.token_expiry:
                if token_obj.token_expiry.tzinfo is not None:
                    # Convert timezone-aware to UTC naive
                    expiry = token_obj.token_expiry.astimezone(pytz.UTC).replace(tzinfo=None)
                else:
                    expiry = token_obj.token_expiry
                    
            creds = Credentials(
                token=token_obj.access_token,
                refresh_token=token_obj.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GMAIL_CLIENT_ID,
                client_secret=settings.GMAIL_CLIENT_SECRET,
                expiry=expiry  # UTC naive datetime
            )
            return creds
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None
    
    def _refresh_credentials(self, creds):
        """Refresh expired credentials"""
        try:
            # Store refresh_token before refresh (Google sometimes nullifies it)
            refresh_token = creds.refresh_token
            creds.refresh(Request())
            
            # Restore refresh_token if it got nullified
            if not creds.refresh_token and refresh_token:
                creds.refresh_token = refresh_token
                
            self._save_credentials(creds)
            return True
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False
    
    def _save_credentials(self, creds):
        """Save credentials to database"""
        # Store expiry as timezone-aware UTC
        token_expiry = None
        if creds.expiry:
            if creds.expiry.tzinfo is None:
                # Assume UTC if naive
                token_expiry = timezone.make_aware(creds.expiry, pytz.UTC)
            else:
                token_expiry = creds.expiry.astimezone(pytz.UTC)
        
        GmailToken.objects.update_or_create(
            defaults={
                'access_token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_expiry': token_expiry
            }
        )
    
    def generate_new_token(self):
        """Generate new OAuth2 token (for management command)"""
        if not os.path.exists(self.client_secret_path):
            raise FileNotFoundError(
                f"Client secret file not found: {self.client_secret_path}"
            )
        
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secret_path, self.SCOPES
        )
        # Force offline access and consent to get refresh token
        creds = flow.run_local_server(
            port=8080, 
            access_type='offline', 
            prompt='consent'
        )
        self._save_credentials(creds)
        return creds
import base64
import logging
from googleapiclient.discovery import build
from django.core.mail.backends.base import BaseEmailBackend
from .generate_credentials import GmailCredentialsManager

logger = logging.getLogger(__name__)


class GmailAPIBackend(BaseEmailBackend):
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.credentials_manager = GmailCredentialsManager()
        self._service = None
    
    @property
    def service(self):
        
        if self._service is None:
            try:
                creds = self.credentials_manager.get_credentials()
                self._service = build('gmail', 'v1', credentials=creds)
            except Exception as e:
                if not self.fail_silently:
                    logger.error(f"Failed to initialize Gmail service: {e}")
                raise
        return self._service
    
    def send_messages(self, email_messages):
        """Send multiple email messages"""
        if not email_messages:
            return 0
        
        try:
            service = self.service
        except Exception:
            if self.fail_silently:
                return 0
            raise
        
        sent_count = 0
        for message in email_messages:
            if self._send_single_message(service, message):
                sent_count += 1
        
        return sent_count
    
    def _send_single_message(self, service, email_message):
        """Send a single email message"""
        try:
            raw_message = self._create_raw_message(email_message)
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully. Message ID: {result['id']}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to send email: {e}"
            if not self.fail_silently:
                logger.error(error_msg)
                raise
            return False
    
    def _create_raw_message(self, email_message):
        """Convert Django email message to Gmail API format"""
        mime_message = email_message.message()
        return base64.urlsafe_b64encode(mime_message.as_bytes()).decode('utf-8')
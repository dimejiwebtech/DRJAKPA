from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from utils.generate_credentials import GmailCredentialsManager


class Command(BaseCommand):
    help = 'Generate Gmail API OAuth2 token'
    
    def handle(self, *args, **options):
        credentials_manager = GmailCredentialsManager()
        
        try:
            self.stdout.write("Starting Gmail OAuth2 flow...")
            creds = credentials_manager.generate_new_token()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Gmail token generated successfully! "
                    f"Gmail token generated successfully and saved to database!"
                )
            )
            
        except FileNotFoundError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f"Failed to generate token: {e}")
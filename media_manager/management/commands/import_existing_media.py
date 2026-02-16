from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from media_manager.models import MediaFile

class Command(BaseCommand):
    help = "Sync existing media files into Media Manager"

    def handle(self, *args, **kwargs):
        media_root = Path(settings.MEDIA_ROOT)
        for path in media_root.rglob("*"):
            if path.is_file():
                relative_path = str(path.relative_to(media_root))
                if not MediaFile.objects.filter(file=relative_path).exists():
                    MediaFile.objects.create(
                        file=relative_path
                    )
                    self.stdout.write(self.style.SUCCESS(f"Added: {relative_path}"))
        self.stdout.write(self.style.SUCCESS("✅ All media synced successfully."))

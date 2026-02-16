from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import MediaFile



@login_required
def media_library(request):
    media_files = MediaFile.objects.all()
    context = {
        'media_files': media_files,
    }
    return render(request, 'media_manager/library.html', context)




from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def tinymce_upload(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    filename = default_storage.save(f'tinymce/{file.name}', file)
    file_url = default_storage.url(filename)
    
    return JsonResponse({'location': file_url})
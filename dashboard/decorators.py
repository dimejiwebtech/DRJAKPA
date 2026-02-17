from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def administrator_required(view_func):
    @wraps(view_func)
    @login_required(login_url='login')
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.groups.filter(name='Administrator').exists():
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def author_or_admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url='login')
    def _wrapped_view(request, *args, **kwargs):
        user_groups = request.user.groups.values_list('name', flat=True)
        if not any(group in user_groups for group in ['Author', 'Administrator']):
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
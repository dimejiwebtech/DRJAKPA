from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter
def has_group(user, group_name):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name__iexact=group_name).exists()

@register.simple_tag
def user_is_administrator(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name__iexact='administrator').exists()

@register.simple_tag 
def user_is_author(user):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name__iexact='author').exists()

@register.simple_tag
def get_user_groups(user):
    if not user.is_authenticated:
        return []
    return list(user.groups.values_list('name', flat=True))
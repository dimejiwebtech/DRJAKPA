from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'email', 'body']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Full Name',
                'class': 'w-full bg-white border border-slate-200 rounded-lg py-3 px-4 text-xs outline-none focus:border-royal transition-all'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email Address',
                'class': 'w-full bg-white border border-slate-200 rounded-lg py-3 px-4 text-xs outline-none focus:border-royal transition-all'
            }),
            'body': forms.Textarea(attrs={
                'rows': 5, 
                'placeholder': 'Provide your comment here...',
                'class': 'w-full bg-white border border-slate-200 rounded-lg py-4 px-4 text-xs outline-none focus:border-royal transition-all resize-none'
            }),
        }
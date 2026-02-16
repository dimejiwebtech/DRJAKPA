from django import forms
from django.utils import timezone
from django.utils.text import slugify
from blog.models import Post, Category
from tinymce.widgets import TinyMCE

class BaseContentForm(forms.ModelForm):
    
    # Institutional Title Style: Large, Bold, Royal
    TITLE_WIDGET = forms.TextInput(attrs={
        'class': 'w-full px-0 py-3 text-2xl md:text-3xl font-extrabold border-0 border-b border-slate-200 focus:border-royal focus:ring-0 focus:outline-none bg-transparent placeholder-slate-300 text-royal uppercase tracking-tighter transition-all',
        'placeholder': 'ENTER DOCUMENT TITLE...',
        'id': 'id_title'
    })
    
    # Minimalist Slug Style
    SLUG_WIDGET = forms.TextInput(attrs={
        'class': 'text-[10px] font-bold px-2 py-1 border-0 border-b border-dashed border-slate-200 focus:border-accent focus:ring-0 focus:outline-none bg-transparent text-slate-400 uppercase tracking-widest',
        'id': 'id_slug'
    })
    
    # High-Density Textarea
    TEXTAREA_WIDGET = forms.Textarea(attrs={
        'class': 'w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:border-royal focus:ring-0 outline-none transition-all placeholder-slate-400 leading-relaxed',
        'rows': 3,
    })
    
    # Standard Dashboard Input
    INPUT_WIDGET = forms.TextInput(attrs={
        'class': 'w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:border-royal focus:ring-0 outline-none transition-all placeholder-slate-400',
    })
    
    # Institutional DateTime Picker
    DATETIME_WIDGET = forms.DateTimeInput(attrs={
        'class': 'w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-[11px] font-bold text-royal uppercase focus:border-royal focus:ring-0 outline-none transition-all',
        'type': 'datetime-local',
        'id': 'id_published_date'
    })
    
    IMAGE_WIDGET = forms.FileInput(attrs={
        'accept': 'image/*',
        'id': 'id_featured_image',
        'style': 'display: none;'
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Keep internal logic: Make common fields optional
        self.fields['slug'].required = False
        self.fields['published_date'].required = False
        
        if 'featured_image' in self.fields:
            self.fields['featured_image'].required = False
            # Keeping the CharField for hidden ID if used by your media manager
            self.fields['featured_image_id'] = forms.CharField(required=False, widget=forms.HiddenInput())
        
        # Set initial datetime value for new content
        if not self.instance.pk and 'published_date' not in self.initial:
            self.initial['published_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        
        if not slug and title:
            slug = slugify(title)
        
        if slug:
            model = self.Meta.model
            queryset = model.objects.filter(slug=slug)
            
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                counter = 1
                original_slug = slug
                while model.objects.filter(slug=slug).exclude(pk=self.instance.pk if self.instance.pk else 0).exists():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
        return slug

    def clean_seo_description(self):
        seo_description = self.cleaned_data.get('seo_description', '')
        if len(seo_description) > 160:
            raise forms.ValidationError('Institutional SEO metadata should not exceed 160 characters.')
        return seo_description

    def get_tinymce_widget(self):
        return TinyMCE(attrs={
            'class': 'django-tinymce',
            'id': 'id_content'
        })


class PostForm(BaseContentForm):
    class Meta:
        model = Post
        fields = [
            'title', 'slug', 'content', 'excerpt', 
            'featured_image', 'category', 'seo_description', 
            'seo_keywords', 'published_date'
        ]
        widgets = {
            'title': BaseContentForm.TITLE_WIDGET,
            'slug': BaseContentForm.SLUG_WIDGET,
            'excerpt': forms.Textarea(attrs={
                **BaseContentForm.TEXTAREA_WIDGET.attrs,
                'placeholder': 'Brief clinical summary for the journal archive...',
                'id': 'id_excerpt'
            }),
            'seo_description': forms.Textarea(attrs={
                **BaseContentForm.TEXTAREA_WIDGET.attrs,
                'placeholder': 'Meta description for Google indexing...',
                'maxlength': '160',
                'id': 'id_seo_description'
            }),
            'seo_keywords': forms.TextInput(attrs={
                **BaseContentForm.INPUT_WIDGET.attrs,
                'placeholder': 'licensing, approbation, document-audit',
                'id': 'id_seo_keywords'
            }),
            'published_date': BaseContentForm.DATETIME_WIDGET,
            'featured_image': BaseContentForm.IMAGE_WIDGET,
            # Ensure category matches the dashboard density
            'category': forms.SelectMultiple(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-lg text-xs py-2 px-3 focus:border-royal outline-none'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget = self.get_tinymce_widget()
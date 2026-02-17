from django import forms
from django.utils import timezone
from django.utils.text import slugify
from blog.models import Post, Category
from tinymce.widgets import TinyMCE
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from blog.models import UserProfile


def set_user_permissions_by_role(user, role_name):
    if role_name == 'Administrator':
        user.is_staff = True
        user.is_superuser = True
    elif role_name == 'Author':
        user.is_staff = True
        user.is_superuser = False
    else:
        user.is_staff = False
        user.is_superuser = False
    user.save()

class BaseContentForm(forms.ModelForm):
    
    
    TITLE_WIDGET = forms.TextInput(attrs={
        'class': 'w-full px-0 py-3 text-2xl md:text-3xl font-extrabold border-0 border-b border-slate-200 focus:border-royal focus:ring-0 focus:outline-none bg-transparent placeholder-slate-300 text-royal uppercase tracking-tighter transition-all',
        'placeholder': 'ENTER DOCUMENT TITLE...',
        'id': 'id_title'
    })
    
    
    SLUG_WIDGET = forms.TextInput(attrs={
        'class': 'text-[10px] font-bold px-2 py-1 border-0 border-b border-dashed border-slate-200 focus:border-accent focus:ring-0 focus:outline-none bg-transparent text-slate-400 uppercase tracking-widest',
        'id': 'id_slug'
    })
    
    
    TEXTAREA_WIDGET = forms.Textarea(attrs={
        'class': 'w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:border-royal focus:ring-0 outline-none transition-all placeholder-slate-400 leading-relaxed',
        'rows': 3,
    })
    
    INPUT_WIDGET = forms.TextInput(attrs={
        'class': 'w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:border-royal focus:ring-0 outline-none transition-all placeholder-slate-400',
    })
    
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
        
        self.fields['slug'].required = False
        self.fields['published_date'].required = False
        
        if 'featured_image' in self.fields:
            self.fields['featured_image'].required = False
            self.fields['featured_image_id'] = forms.CharField(required=False, widget=forms.HiddenInput())
        
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
            'category': forms.SelectMultiple(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-lg text-xs py-2 px-3 focus:border-royal outline-none'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget = self.get_tinymce_widget()


class StyledWidget:
    # Standard input, select, and textarea styling
    BASE_CLASSES = (
        "w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl "
        "text-xs font-bold text-royal focus:border-royal focus:bg-white "
        "outline-none transition-all placeholder-slate-300 shadow-inner"
    )
    
    # Modern file input styling
    FILE_CLASSES = (
        "block w-full text-[10px] text-slate-500 font-bold "
        "file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 "
        "file:text-[10px] file:font-black file:bg-royal/10 file:text-royal "
        "hover:file:bg-royal/20 transition-all cursor-pointer"
    )
    
    # Select/Dropdown specific
    SELECT_CLASSES = BASE_CLASSES + " cursor-pointer"



class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': StyledWidget.BASE_CLASSES, 'rows': 3, 'style': 'resize:none;'}), required=False)
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': StyledWidget.SELECT_CLASSES})
    )
    profile_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': StyledWidget.FILE_CLASSES}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply style to password fields while keeping UserCreationForm logic
        self.fields['password1'].widget.attrs.update({'class': StyledWidget.BASE_CLASSES})
        self.fields['password2'].widget.attrs.update({'class': StyledWidget.BASE_CLASSES})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            role = self.cleaned_data.get('role')
            if role:
                user.groups.add(role)
                set_user_permissions_by_role(user, role.name)  
            
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.first_name = self.cleaned_data['first_name']
            profile.last_name = self.cleaned_data['last_name']
            profile.bio = self.cleaned_data['bio']
            if self.cleaned_data['profile_image']:
                profile.profile_image = self.cleaned_data['profile_image']
            profile.save()
            
        return user


class UserEditForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': StyledWidget.SELECT_CLASSES})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}),
            'first_name': forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}),
            'last_name': forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        show_role = kwargs.pop('show_role', False)
        super().__init__(*args, **kwargs)
        
        if not show_role:
            del self.fields['role']
        elif self.instance.pk:
            user_group = self.instance.groups.first()
            if user_group:
                self.fields['role'].initial = user_group


class UserProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES})
    )

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'bio', 'profile_image')
        widgets = {
            'bio': forms.Textarea(attrs={'class': StyledWidget.BASE_CLASSES, 'rows': 3, 'style': 'resize:none;'}),
            'profile_image': forms.FileInput(attrs={'class': StyledWidget.FILE_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            User.objects.filter(pk=profile.user.pk).update(
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name']
            )
        return profile


class BulkActionForm(forms.Form):
    action = forms.ChoiceField(choices=[
        ('', 'Bulk actions'),
        ('delete', 'Delete permanently'),
        ('change_role_administrator', 'Promote to Administrator'),
        ('change_role_author', 'Set to Author'),
    ], widget=forms.Select(attrs={
        'class': (
            "px-4 py-2.5 bg-white border border-slate-200 rounded-lg "
            "text-[10px] font-black uppercase tracking-widest text-royal "
            "focus:ring-2 focus:ring-royal outline-none transition-all"
        )
    }))
    selected_users = forms.CharField(widget=forms.HiddenInput())
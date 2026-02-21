from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from dashboard.forms import PostForm
from blog.models import Post, Category, Comment
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.text import slugify
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET, require_http_methods
import json
import os
from media_manager.models import MediaFile
from main.models import Booking, SessionTime, Testimonial, TeamMember
from datetime import timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from .decorators import administrator_required, author_or_admin_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from blog.models import UserProfile
from .forms import UserCreateForm, UserEditForm, UserProfileEditForm, BulkActionForm, set_user_permissions_by_role


@login_required(login_url='login')
def dashboard(request):
    # Post Statistics
    total_posts = Post.objects.count()
    published_posts = Post.objects.filter(status='published').count()
    draft_posts = Post.objects.filter(status='draft').count()
    scheduled_posts = Post.objects.filter(status='scheduled').count()
    
    # Comment Statistics
    total_comments = Comment.objects.count()
    pending_comments = Comment.objects.filter(approved=False).count()
    approved_comments = Comment.objects.filter(approved=True).count()
    
    # Booking Statistics
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    ongoing_bookings = Booking.objects.filter(status='ongoing').count()
    completed_bookings = Booking.objects.filter(status='completed').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    
    # Calculate total revenue from completed bookings
    total_revenue = Booking.objects.filter(status='completed').aggregate(
        total=Sum('total_price')
    )['total'] or 0
    
    # Session Statistics
    total_sessions = SessionTime.objects.count()
    available_sessions = SessionTime.objects.filter(is_available=True).count()
    
    # Category Statistics
    total_categories = Category.objects.count()
    categories_with_posts = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0).count()
    
    # Recent Posts (last 5 published)
    recent_posts = Post.objects.filter(
        status='published'
    ).prefetch_related('category').order_by('-published_date')[:5]
    
    # Recent Comments (last 5)
    recent_comments = Comment.objects.select_related(
        'post'
    ).order_by('-created_on')[:5]
    
    # Recent Bookings (last 5 pending/ongoing)
    recent_bookings = Booking.objects.filter(
        Q(status='pending') | Q(status='ongoing')
    ).select_related('session_time').order_by('-created_at')[:5]
    
    # Top Categories by post count
    top_categories = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0).order_by('-post_count')[:5]
    
    context = {
        # Post stats
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'scheduled_posts': scheduled_posts,
        
        # Comment stats
        'total_comments': total_comments,
        'pending_comments': pending_comments,
        'approved_comments': approved_comments,
        
        # Booking stats
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'ongoing_bookings': ongoing_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_revenue': total_revenue,
        
        # Session stats
        'total_sessions': total_sessions,
        'available_sessions': available_sessions,
        
        # Category stats
        'total_categories': total_categories,
        'categories_with_posts': categories_with_posts,
        
        # Recent data
        'recent_posts': recent_posts,
        'recent_comments': recent_comments,
        'recent_bookings': recent_bookings,
        'top_categories': top_categories,
    }
    
    return render(request, 'dashboard/dashboard.html', context)



def posts(request):
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')
    date_filter = request.GET.get('date', 'all')
    search_query = request.GET.get('search', '').strip()
    
    
    posts_queryset = Post.objects.select_related('author').prefetch_related('category').annotate(
    comment_count=Count('comments', filter=Q(comments__approved=True))
)
    # Filter by trash status
    if status_filter == 'trash':
        posts_queryset = posts_queryset.filter(is_trashed=True)
    else:
        posts_queryset = posts_queryset.filter(is_trashed=False)
    
    
    if search_query:
        posts_queryset = posts_queryset.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query)
        )
    
    if status_filter == 'mine':
        posts_queryset = posts_queryset.filter(author=request.user)
    elif status_filter == 'published':
        posts_queryset = posts_queryset.filter(status='published')
    elif status_filter == 'draft':
        posts_queryset = posts_queryset.filter(status='draft')
    
    # Category filtering
    if category_filter != 'all':
        try:
            posts_queryset = posts_queryset.filter(category__id=int(category_filter))
        except (ValueError, TypeError):
            pass
    
    # Date filtering
    if date_filter != 'all':
        try:
            year, month = date_filter.split('-')
            posts_queryset = posts_queryset.filter(
                published_date__year=int(year),
                published_date__month=int(month)
            )
        except (ValueError, IndexError):
            pass
    
    posts_queryset = posts_queryset.order_by('-created_at')
    
    # Get counts for tabs
    def get_tab_counts(user):
        base_posts = Post.objects.select_related('author')
        return {
            'all': base_posts.filter(is_trashed=False).count(),
            'mine': base_posts.filter(is_trashed=False, author=user).count(),
            'published': base_posts.filter(is_trashed=False, status='published').count(),
            'draft': base_posts.filter(is_trashed=False, status='draft').count(),
            'trash': base_posts.filter(is_trashed=True).count(),
        }

    tab_counts = get_tab_counts(request.user)

    categories = Category.objects.all().order_by('name')
    
    # Pagination
    paginator = Paginator(posts_queryset, 20)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)
    
    
    # Generate date options (last 12 months)
    def get_date_options():
        date_options = []
        current_date = timezone.now()
        for i in range(12):
            if current_date.month - i <= 0:
                month = current_date.month - i + 12
                year = current_date.year - 1
            else:
                month = current_date.month - i
                year = current_date.year
            
            date = current_date.replace(year=year, month=month, day=1)
            date_options.append({
                'value': date.strftime('%Y-%m'),
                'label': date.strftime('%B %Y')
            })
        return date_options
    
    context = {
        'posts': posts_page,
        'categories': categories,
        'tab_counts': tab_counts,
        'current_status': status_filter,
        'current_category': category_filter,
        'date_options': date_filter,
        'search_query': search_query,
        'total_items': paginator.count,
        'current_page': posts_page.number,
        'total_pages': paginator.num_pages,
        'has_previous': posts_page.has_previous(),
        'has_next': posts_page.has_next(),
        'previous_page': posts_page.previous_page_number() if posts_page.has_previous() else None,
        'next_page': posts_page.next_page_number() if posts_page.has_next() else None,
    }
    
    return render(request, 'dashboard/posts.html', context)



def bulk_action(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        post_ids = request.POST.getlist('post_ids')
        
        # Get current filter parameters to preserve state
        status_filter = request.GET.get('status', 'all')
        category_filter = request.GET.get('category', 'all')
        date_filter = request.GET.get('date', 'all')
        search_query = request.GET.get('search', '').strip()
        page = request.GET.get('page', '1')
        
        if not post_ids:
            messages.error(request, 'No posts selected.')
            redirect_url = reverse('posts') + f'?status={status_filter}&category={category_filter}&date={date_filter}&search={search_query}&page={page}'
            return redirect(redirect_url)
        
        posts_to_update = Post.objects.filter(id__in=post_ids)
        
        if action == 'trash':
            posts_to_update.update(
                is_trashed=True,
                trashed_at=timezone.now(),
                trashed_by=request.user,
                status='trashed'  
            )
            messages.success(request, f'{len(post_ids)} posts moved to trash.')
            
        elif action == 'restore':
            posts_to_update.update(
                is_trashed=False,
                trashed_at=None,
                trashed_by=None,
                status='draft' 
            )
            messages.success(request, f'{len(post_ids)} posts restored as drafts.')
            
        elif action == 'delete':
            posts_to_update.delete()
            messages.success(request, f'{len(post_ids)} posts permanently deleted.')
            
        elif action == 'publish':
            posts_to_update = posts_to_update.exclude(status='published')
            posts_to_update.update(status='published', published_date=timezone.now())
            messages.success(request, f'{len(post_ids)} posts published.')
            
        elif action == 'draft':
            posts_to_update.update(status='draft')
            messages.success(request, f'{len(post_ids)} posts moved to draft.')
        
        # Build redirect URL with preserved parameters
        redirect_url = reverse('posts') + f'?status={status_filter}&category={category_filter}&date={date_filter}&search={search_query}&page={page}'
        return redirect(redirect_url)
    
    return redirect('posts')



def trash_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        post.is_trashed = True
        post.trashed_at = timezone.now()
        post.trashed_by = request.user
        post.status = 'trashed'  
        post.save()
        
        messages.success(request, f'Post "{post.title}" moved to trash.')
        
    
    # Preserve current filters
    status = request.GET.get('status', 'all')
    category = request.GET.get('category', 'all')
    date = request.GET.get('date', 'all')
    search = request.GET.get('search', '')
    page = request.GET.get('page', '1')
    
    redirect_url = reverse('posts') + f'?status={status}&category={category}&date={date}&search={search}&page={page}'
    return redirect(redirect_url)
    


def restore_post(request, pk):
    post = get_object_or_404(Post, id=pk, is_trashed=True)
    
    if request.method == 'POST':
        post.is_trashed = False
        post.trashed_at = None
        post.trashed_by = None
        post.status = 'draft'  
        post.save()
        
        messages.success(request, f'Post "{post.title}" restored as draft.')
    
    # Preserve current filters
    status = request.GET.get('status', 'all')
    category = request.GET.get('category', 'all')
    date = request.GET.get('date', 'all')
    search = request.GET.get('search', '')
    page = request.GET.get('page', '1')
    
    redirect_url = reverse('posts') + f'?status={status}&category={category}&date={date}&search={search}&page={page}'
    return redirect(redirect_url)



def add_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    from media_manager.models import MediaFile  
                    media_obj = MediaFile.objects.get(id=featured_image_id)
                    post = form.save(commit=False)
                    post.featured_image = media_obj.file 
                except MediaFile.DoesNotExist:
                    pass
            else:
                post = form.save(commit=False)
            post.author = request.user
            
            # Handle status
            if 'save_draft' in request.POST:
                post.status = 'draft'
            elif 'publish' in request.POST:
                post.status = 'published'
                if not post.published_date:
                    post.published_date = timezone.now()
            
            # Generate slug if not provided
            if not post.slug and post.title:
                post.slug = generate_unique_slug(post.title)
            
            post.save()
            
            # Handle categories - get selected category IDs from POST data
            selected_categories = request.POST.getlist('category')
            if selected_categories:
                post.category.set(selected_categories)
            
            if post.status == 'published':
                messages.success(request, 'Post published successfully!')
            else:
                messages.success(request, 'Post saved as draft!')
                
            return redirect('edit_post', pk=post.pk)
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm()
    
    all_categories = Category.objects.all()
    return render(request, 'dashboard/add_posts.html', {
        'form': form,
        'all_categories': all_categories,
    })



def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user owns the post or is superuser
    if post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    from media_manager.models import MediaFile 
                    media_obj = MediaFile.objects.get(id=featured_image_id)
                    post = form.save(commit=False)
                    post.featured_image = media_obj.file  
                except MediaFile.DoesNotExist:
                    pass
            else:
                post = form.save(commit=False)
            post = form.save(commit=False)
            
            # Handle status
            if 'save_draft' in request.POST:
                post.status = 'draft'
            elif 'publish' in request.POST:
                post.status = 'published'
                if not post.published_date:
                    post.published_date = timezone.now()
            
            # Generate slug if not provided
            if not post.slug and post.title:
                post.slug = generate_unique_slug(post.title, exclude_id=post.id)
            
            post.save()
            
            # Handle categories - get selected category IDs from POST data
            selected_categories = request.POST.getlist('category')
            post.category.set(selected_categories)
            
            if post.status == 'published':
                messages.success(request, 'Post updated and published!')
            else:
                messages.success(request, 'Post updated and saved as draft!')
                
            return redirect('edit_post', pk=post.pk)
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm(instance=post)
    
    all_categories = Category.objects.all()
    return render(request, 'dashboard/add_posts.html', {
        'form': form,
        'post': post,
        'all_categories': all_categories,
    })

def post_form_view(request, pk=None):
    post = get_object_or_404(Post, pk=pk) if pk else None
    
    # Check permissions for editing
    if post and post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    from media_manager.models import MediaFile  
                    media_obj = MediaFile.objects.get(id=featured_image_id)
                    post = form.save(commit=False)
                    post.featured_image = media_obj.file  
                except MediaFile.DoesNotExist:
                    pass
            else:
                post = form.save(commit=False)
            post_obj = form.save(commit=False)
            
            if not post:  # New post
                post_obj.author = request.user
            
            # Handle status and publish date
            if 'save_draft' in request.POST:
                post_obj.status = 'draft'
            elif 'publish' in request.POST:
                post_obj.status = 'published'
                if not post_obj.published_date:
                    post_obj.published_date = timezone.now()
            
            # Auto-generate slug if needed
            if not post_obj.slug and post_obj.title:
                post_obj.slug = generate_unique_slug(post_obj.title, exclude_id=post_obj.id if post else None)
            
            post_obj.save()
            
            # Handle category (multiple selection)
            selected_categories = request.POST.getlist('category')
            post_obj.save()
            if selected_categories:
                post_obj.category.set(selected_categories)
            else:
                post_obj.category.clear()
            
            success_msg = f"Post {'updated' if post else 'created'} and {'published' if post_obj.status == 'published' else 'saved as draft'}!"
            messages.success(request, success_msg)
            
            return redirect('edit_post', pk=post_obj.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm(instance=post)
    
    return render(request, 'dashboard/add_posts.html', {
        'form': form,
        'post': post,
        'all_categories': Category.objects.all(),
    })

def generate_unique_slug(title, exclude_id=None):
    base_slug = slugify(title) or 'post'
    slug = base_slug
    counter = 1
    
    while True:
        queryset = Post.objects.filter(slug=slug)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        if not queryset.exists():
            return slug
            
        slug = f"{base_slug}-{counter}"
        counter += 1

@require_POST
def auto_save_post(request):
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        
        saveable_fields = ['title', 'content', 'excerpt', 'seo_description', 'seo_keywords', 'slug']
        
        if post_id:
            # Update existing post
            post = get_object_or_404(Post, pk=post_id, author=request.user)
            
            # Update basic fields
            for field in saveable_fields:
                if field in data and data[field] is not None:
                    setattr(post, field, data[field])
            
            # Auto-generate slug if title changed and no custom slug
            if data.get('title') and not data.get('slug'):
                post.slug = generate_unique_slug(data['title'], exclude_id=post.id)
            elif not post.slug:  # Add this line
                post.slug = generate_unique_slug(post.title or 'untitled', exclude_id=post.id)
            
            post.status = 'draft'
            post.save()
            
            # Handle category after saving
            category_ids = data.get('category', [])
            if category_ids:
                try:
                    valid_categories = Category.objects.filter(pk__in=category_ids)
                    post.category.set(valid_categories)
                except (ValueError, TypeError):
                    pass
            else:
                post.category.clear()
            
        else:
            # Create new post
            post_data = {field: data.get(field, '') for field in saveable_fields}
            post_data.update({
                'author': request.user,
                'status': 'draft'
            })
            
            if post_data['title'] and not post_data['slug']:
                post_data['slug'] = generate_unique_slug(post_data['title'])
            elif not post_data['slug']:  
                post_data['slug'] = generate_unique_slug('untitled')  
            
            post = Post.objects.create(**post_data)
            
            # Handle category for new post
            category_id = data.get('category')
            if category_id and category_id != '':
                try:
                    category = Category.objects.get(pk=int(category_id))
                    post.category = category
                    post.save()
                except (Category.DoesNotExist, ValueError, TypeError):
                    pass
        
        return JsonResponse({
            'success': True,
            'post_id': post.pk,
            'slug': post.slug,
            'message': 'Auto-saved'
        })
        
    except Exception as e:
        print(f"Auto-save error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


def generate_slug_ajax(request):
    title = request.GET.get('title', '')
    post_id = request.GET.get('post_id')
    
    if not title:
        return JsonResponse({'slug': '', 'error': 'No title provided'})
    
    exclude_id = int(post_id) if post_id and post_id.isdigit() else None
    slug = generate_unique_slug(title, exclude_id=exclude_id)
    
    return JsonResponse({'slug': slug})

@require_POST
def remove_featured_image(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        
        if not post_id:
            return JsonResponse({'success': False, 'error': 'No post ID provided'})
        
        post = get_object_or_404(Post, pk=post_id, author=request.user)
        
        if post.featured_image:
            # Remove file from storage
            if os.path.exists(post.featured_image.path):
                os.remove(post.featured_image.path)
            
            post.featured_image = None
            post.save()
        
        return JsonResponse({'success': True, 'message': 'Featured image removed successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
  
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        post.is_trashed = True
        post.trashed_at = timezone.now()
        post.trashed_by = request.user
        post.status = 'trashed'
        post.save()
        
        messages.success(request, f'Post "{post.title}" moved to trash.')
    
    return redirect('posts')


def restore_post(request, pk):
    post = get_object_or_404(Post, pk=pk, is_trashed=True)
    
    if request.method == 'POST':
        post.is_trashed = False
        post.trashed_at = None
        post.trashed_by = None
        post.status = 'draft'  
        post.save()
        
        messages.success(request, f'Post "{post.title}" restored as draft.')
    return redirect('posts')
   
def preview_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user owns the post or is superuser
    if post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only preview your own posts.')
        return redirect('dashboard')
    
    
    if post.status == 'published':
        return redirect('posts_by_category_or_post', slug=post.slug)
    
    
    if post.status == 'draft':
        context = {
            'single_post': post,  
            'is_preview': True,
            'preview_notice': 'This is a preview of your draft post.',
            'comments': [], 

        }
        return render(request, 'blog/preview_single_blog.html', context)
    
    # Fallback for other statuses
    return redirect('dashboard')


def categories(request):
    search_query = request.GET.get('search', '')
    categories_list = Category.objects.annotate(
        posts_count=Count('posts', filter=Q(posts__status='published'))
    ).order_by('name')
    
    if search_query:
        categories_list = categories_list.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(slug__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(categories_list, 20) 
    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)
    
    context = {
        'categories': categories,
        'search_query': search_query,
    }
    return render(request, 'dashboard/categories.html', context)


def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not category_name:
            messages.error(request, 'Category name is required', extra_tags='category')
            return redirect('categories')
        
        if not slug:
            slug = slugify(category_name)
        else:
            slug = slugify(slug)
        
        if Category.objects.filter(name__iexact=category_name).exists():
            messages.error(request, 'Category with this name already exists', extra_tags='category')
            return redirect('categories')
        
        if Category.objects.filter(slug=slug).exists():
            messages.error(request, 'Category with this slug already exists', extra_tags='category')
            return redirect('categories')
        
        try:
            Category.objects.create(
                name=category_name,
                slug=slug,
                description=description if description else ''
            )
            messages.success(request, f'Category "{category_name}" added successfully', extra_tags='category')
        except Exception as e:
            messages.error(request, f'Error adding category: {str(e)}', extra_tags='category')
    
    return redirect('categories')


def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not category_name:
            messages.error(request, 'Category name is required', extra_tags='category')
            return redirect('categories')
        
        if not slug:
            slug = slugify(category_name)
        else:
            slug = slugify(slug)
        
        # Check for duplicates 
        if Category.objects.filter(name__iexact=category_name).exclude(id=category_id).exists():
            messages.error(request, 'Category with this name already exists', extra_tags='category')
            return redirect('categories')
        
        if Category.objects.filter(slug=slug).exclude(id=category_id).exists():
            messages.error(request, 'Category with this slug already exists', extra_tags='category')
            return redirect('categories')
        
        try:
            category.name = category_name
            category.slug = slug
            category.description = description if description else ''
            category.save()
            messages.success(request, f'Category "{category_name}" updated successfully', extra_tags='category')
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}', extra_tags='category')
    
    return redirect('categories')


def delete_category(request, pk):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=pk)
        category_name = category.name
        
        # Check if category has posts
        post_count = category.posts.count()
        if post_count > 0:
            messages.error(request, f'Cannot delete category "{category_name}" because it has {post_count} post(s) assigned to it', extra_tags='category')
            return redirect('categories')
        
        try:
            category.delete()
            messages.success(request, f'Category "{category_name}" deleted successfully', extra_tags='category')
        except Exception as e:
            messages.error(request, f'Error deleting category: {str(e)}', extra_tags='category')
    
    return redirect('categories')


def view_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    
    posts = Post.objects.filter(status='published', category=category).order_by('-published_date')
    paginator = Paginator(posts, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/posts_by_category.html', context)


def comment(request):
    # Get filter parameters
    status = request.GET.get('status', 'all')
    page = request.GET.get('page', 1)
    
    # Base queryset
    comments = Comment.objects.select_related('post').order_by('-created_on')
    
    # Apply status filters
    if status == 'mine':
        comments = comments.filter(post__author=request.user)
    elif status == 'pending':
        comments = comments.filter(approved=False)
    elif status == 'approved':
        comments = comments.filter(approved=True)
    
    # Count for each status
    all_count = Comment.objects.count()
    mine_count = Comment.objects.filter(post__author=request.user).count()
    pending_count = Comment.objects.filter(approved=False).count()
    approved_count = Comment.objects.filter(approved=True).count()
    
    # Pagination
    paginator = Paginator(comments, 10)
    page_obj = paginator.get_page(page)
    
    context = {
        'comments': page_obj,
        'current_status': status,
        'all_count': all_count,
        'mine_count': mine_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'paginator': paginator,
        'page_obj': page_obj,
    }
    
    return render(request, 'dashboard/comments.html', context)


def bulk_comment_action(request):
    if request.method == 'POST':
        action = request.POST.get('bulk_action')
        comment_ids = request.POST.getlist('comment_ids')
        
        if comment_ids:
            comments = Comment.objects.filter(id__in=comment_ids)
            
            if action == 'approve':
                comments.update(approved=True)
            elif action == 'unapprove':
                comments.update(approved=False)
            elif action == 'delete':
                comments.delete()
    
    return redirect('comments')


def comment_approve(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.approved = True
    comment.save()
    return redirect('comments')


def comment_unapprove(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.approved = False
    comment.save()
    return redirect('comments')


def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    return redirect('comments')


def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        new_body = request.POST.get('comment_body')
        if new_body:
            comment.body = new_body
            comment.save()
    return redirect('comments')


def comment_reply(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        reply_text = request.POST.get('reply_text')
        if reply_text:
            Comment.objects.create(
                post=comment.post,
                parent=comment,
                name=request.user.get_full_name() or request.user.username,
                email=request.user.email,
                body=reply_text,
                approved=True
            )
    return redirect('comments')



# Media Library

def media_library(request):
    
    # Get filter parameters
    media_type = request.GET.get('type', 'all')
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('date', 'all')
    
    # Base queryset
    media_files = MediaFile.objects.all()
    
    # Apply filters
    if media_type != 'all':
        media_files = media_files.filter(category=media_type)
    
    if search_query:
        media_files = media_files.filter(
            Q(file__icontains=search_query) |
            Q(alt_text__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Date filtering (simplified)
    if date_filter != 'all':
        pass
    
    
    paginator = Paginator(media_files, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # AJAX request for load more
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Check if this is NOT a request from the post editor
        if 'post-editor' in request.GET:
            # Return JSON for post editor modal
            media_data = []
            for media in page_obj:
                media_data.append({
                    'id': media.id,
                    'url': media.file.url,
                    'name': os.path.basename(media.file.name),
                    'type': media.file_type,
                    'size': media.file_size,
                    'alt_text': media.alt_text,
                    'description': media.description,
                    'created_at': media.created_at.strftime('%B %d, %Y'),
                    'file_extension': media.file_extension,
                    'thumbnail_url': media.get_thumbnail_url(),
                })
            
            return JsonResponse({
                'media_files': media_data,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            })
        elif request.GET.get('page'):  # load more 
            media_data = []
            for media in page_obj:
                media_data.append({
                    'id': media.id,
                    'url': media.file.url,
                    'name': os.path.basename(media.file.name),
                    'type': media.file_type,
                    'size': media.file_size,
                    'alt_text': media.alt_text,
                    'description': media.description,
                    'created_at': media.created_at.strftime('%B %d, %Y'),
                    'file_extension': media.file_extension,
                    'thumbnail_url': media.get_thumbnail_url(),
                })
            
            return JsonResponse({
                'media_files': media_data,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            })
    
    # Get media type counts for filter buttons
    media_counts = {
        'all': MediaFile.objects.count(),
        'image': MediaFile.objects.filter(category='image').count(),
        'document': MediaFile.objects.filter(category='document').count(),
        'video': MediaFile.objects.filter(category='video').count(),
        'audio': MediaFile.objects.filter(category='audio').count(),
        'other': MediaFile.objects.filter(category='other').count(),
    }
    
    context = {
        'media_files': page_obj,
        'media_type': media_type,
        'search_query': search_query,
        'date_filter': date_filter,
        'media_counts': media_counts,
        'has_next': page_obj.has_next(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    }
    
    return render(request, 'dashboard/media.html', context)


def add_media(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        uploaded_files = []
        
        for file in files:
            # Create MediaFile instance
            media_file = MediaFile(file=file)
            
            # Set alt_text to filename without extension
            media_file.alt_text = os.path.splitext(file.name)[0]
            
            media_file.save()
            uploaded_files.append(media_file)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX response - check if request came from media library
            referer = request.META.get('HTTP_REFERER', '')
            
            files_data = []
            for media in uploaded_files:
                files_data.append({
                    'id': media.id,
                    'name': os.path.basename(media.file.name),
                    'url': media.file.url,
                    'type': media.file_type,
                    'size': media.file_size,
                })
            
            response_data = {
                'success': True,
                'files': files_data,
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)'
            }
            
            # If not from media library page, redirect to media library
            if 'media/' not in referer or 'add-media' in referer:
                response_data['redirect'] = '/dashboard/media/' 
            
            return JsonResponse(response_data)
        else:
            messages.success(request, f'Successfully uploaded {len(uploaded_files)} file(s)')
            return redirect('/dashboard/media/')  
    
    return render(request, 'dashboard/add_media.html')

def media_detail(request, media_id):
    media_file = get_object_or_404(MediaFile, id=media_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': media_file.id,
            'url': media_file.file.url,
            'name': os.path.basename(media_file.file.name),
            'type': media_file.file_type,
            'size': media_file.file_size,
            'alt_text': media_file.alt_text,
            'description': media_file.description,
            'created_at': media_file.created_at.strftime('%B %d, %Y'),
            'file_extension': media_file.file_extension,
            'thumbnail_url': media_file.get_thumbnail_url(),
            'dimensions': getattr(media_file, 'dimensions', None),  
        }
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def update_media(request, media_id):
    media_file = get_object_or_404(MediaFile, id=media_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        
        # Update fields
        media_file.alt_text = data.get('alt_text', media_file.alt_text)
        media_file.description = data.get('description', media_file.description)
        media_file.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Media updated successfully'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def delete_media(request, media_id):
    media_file = get_object_or_404(MediaFile, id=media_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        media_file.delete() 
        
        return JsonResponse({
            'success': True,
            'message': 'Media deleted successfully'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def bulk_delete_media(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        media_ids = data.get('media_ids', [])
        
        if media_ids:
            deleted_count = 0
            for media_id in media_ids:
                try:
                    media_file = MediaFile.objects.get(id=media_id)
                    media_file.delete()
                    deleted_count += 1
                except MediaFile.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted {deleted_count} file(s)'
            })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# Booking Management
def bookings_list(request):
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    bookings = Booking.objects.select_related('session_time').all()
    
    # Apply status filter
    if status_filter != 'all':
        bookings = bookings.filter(status=status_filter)
    
    # Apply search
    if search_query:
        bookings = bookings.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(whatsapp_number__icontains=search_query)
        )
    
    # Get counts for each status
    all_count = Booking.objects.count()
    pending_count = Booking.objects.filter(status='pending').count()
    ongoing_count = Booking.objects.filter(status='ongoing').count()
    completed_count = Booking.objects.filter(status='completed').count()
    cancelled_count = Booking.objects.filter(status='cancelled').count()
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'bookings': page_obj,
        'current_status': status_filter,
        'search_query': search_query,
        'all_count': all_count,
        'pending_count': pending_count,
        'ongoing_count': ongoing_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'page_obj': page_obj,
    }
    
    return render(request, 'dashboard/bookings.html', context)

@require_http_methods(["GET"])
def booking_detail(request, booking_id):
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        booking = get_object_or_404(Booking, id=booking_id)
        
        data = {
            'id': booking.id,
            'full_name': booking.full_name,
            'email': booking.email,
            'whatsapp_number': booking.whatsapp_number,
            'session_time': str(booking.session_time),
            'session_date': booking.session_time.date.strftime('%Y-%m-%d'),
            'session_time_display': booking.session_time.time.strftime('%H:%M'),
            'duration_hours': booking.duration_hours,
            'total_price': str(booking.total_price),
            'status': booking.status,
            'payment_screenshot_url': booking.payment_screenshot.url if booking.payment_screenshot else None,
            'created_at': booking.created_at.strftime('%B %d, %Y at %I:%M %p'),
        }
        
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def booking_update(request, booking_id):    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        booking = get_object_or_404(Booking, id=booking_id)
        data = json.loads(request.body)
        
        # Update allowed fields only (NOT payment_screenshot)
        booking.full_name = data.get('full_name', booking.full_name)
        booking.email = data.get('email', booking.email)
        booking.whatsapp_number = data.get('whatsapp_number', booking.whatsapp_number)
        booking.duration_hours = int(data.get('duration_hours', booking.duration_hours))
        
        booking.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking updated successfully'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def booking_update_status(request, booking_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        booking = get_object_or_404(Booking, id=booking_id)
        data = json.loads(request.body)
        
        new_status = data.get('status')
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Booking status updated to {booking.get_status_display()}'
            })
        
        return JsonResponse({'error': 'Invalid status'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def booking_delete(request, booking_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        booking = get_object_or_404(Booking, id=booking_id)
        booking.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking deleted successfully'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# Session Management

def sessions_list(request):
    
    search_query = request.GET.get('search', '')
    availability_filter = request.GET.get('availability', 'all')
    
    # Base queryset
    sessions = SessionTime.objects.annotate(
        bookings_count=Count('bookings')
    ).all()
    
    # Apply availability filter
    if availability_filter == 'available':
        sessions = sessions.filter(is_available=True)
    elif availability_filter == 'unavailable':
        sessions = sessions.filter(is_available=False)
    
    # Apply search
    if search_query:
        sessions = sessions.filter(
            Q(date__icontains=search_query) |
            Q(time__icontains=search_query)
        )
    
    # Get counts
    all_count = SessionTime.objects.count()
    available_count = SessionTime.objects.filter(is_available=True).count()
    unavailable_count = SessionTime.objects.filter(is_available=False).count()
    
    # Pagination
    paginator = Paginator(sessions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sessions': page_obj,
        'search_query': search_query,
        'availability_filter': availability_filter,
        'all_count': all_count,
        'available_count': available_count,
        'unavailable_count': unavailable_count,
        'page_obj': page_obj,
    }
    
    return render(request, 'dashboard/sessions.html', context)


@require_http_methods(["POST"])
def session_create(request):
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        
        date_str = data.get('date')
        time_str = data.get('time')
        
        # Parse date and time
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.strptime(time_str, '%H:%M').time()
        
        # Check if session already exists
        if SessionTime.objects.filter(date=date, time=time).exists():
            return JsonResponse({
                'success': False,
                'error': 'Session time already exists'
            }, status=400)
        
        # Create session
        session = SessionTime.objects.create(
            date=date,
            time=time,
            is_available=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Session created successfully',
            'session': {
                'id': session.id,
                'date': session.date.strftime('%Y-%m-%d'),
                'time': session.time.strftime('%H:%M'),
                'is_available': session.is_available,
            }
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["GET"])
def session_detail(request, session_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        session = get_object_or_404(SessionTime, id=session_id)
        
        data = {
            'id': session.id,
            'date': session.date.strftime('%Y-%m-%d'),
            'time': session.time.strftime('%H:%M'),
            'is_available': session.is_available,
        }
        
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def session_update(request, session_id):
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        session = get_object_or_404(SessionTime, id=session_id)
        data = json.loads(request.body)
        
        date_str = data.get('date')
        time_str = data.get('time')
        is_available = data.get('is_available', session.is_available)
        
        # Parse date and time
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.strptime(time_str, '%H:%M').time()
        
        # Check if another session exists with these details
        if SessionTime.objects.filter(date=date, time=time).exclude(id=session_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Session time already exists'
            }, status=400)
        
        # Update session
        session.date = date
        session.time = time
        session.is_available = is_available
        session.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Session updated successfully'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def session_delete(request, session_id):
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        session = get_object_or_404(SessionTime, id=session_id)
        
        # Check if session has bookings
        if session.bookings.exists():
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete session with existing bookings'
            }, status=400)
        
        session.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Session deleted successfully'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@administrator_required
@login_required(login_url='login')
def testimonials(request):
    testimonials = Testimonial.objects.all().order_by('-created_at')
    paginator = Paginator(testimonials, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/testimonials.html', {
        'page_obj': page_obj,
        'testimonials': page_obj.object_list,
    })

@administrator_required
@login_required(login_url='login')
@require_http_methods(["POST"])
def add_testimonial(request):
    try:
        testimonial = Testimonial.objects.create(
            name=request.POST.get('name', '').strip(),
            location=request.POST.get('location', '').strip(),
            image=request.FILES.get('image'),
            testimony=request.POST.get('testimony', '').strip(),
            is_active=request.POST.get('is_active') == 'on'
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@administrator_required    
@login_required(login_url='login')
def edit_testimonial(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': testimonial.id,
            'name': testimonial.name,
            'location': testimonial.location,
            'image': testimonial.image.url if testimonial.image else '',
            'testimony': testimonial.testimony,
            'is_active': testimonial.is_active,
        })
    
    elif request.method == 'POST':
        try:
            testimonial.name = request.POST.get('name', '').strip()
            testimonial.location = request.POST.get('location', '').strip()
            
            if request.FILES.get('image'):
                testimonial.image = request.FILES['image']
            
            testimonial.testimony = request.POST.get('testimony', '').strip()
            testimonial.is_active = request.POST.get('is_active') == 'on'
            testimonial.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url='login')
@administrator_required
@require_http_methods(["DELETE"])
def delete_testimonial(request, pk):
    try:
        testimonial = get_object_or_404(Testimonial, pk=pk)
        testimonial.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ─── Team Management ─────────────────────────────────────────────────

@administrator_required
@login_required(login_url='login')
def team_list(request):
    members = TeamMember.objects.all()
    paginator = Paginator(members, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/team.html', {
        'page_obj': page_obj,
        'members': page_obj.object_list,
    })


@administrator_required
@login_required(login_url='login')
@require_http_methods(["POST"])
def add_team_member(request):
    try:
        member = TeamMember.objects.create(
            name=request.POST.get('name', '').strip(),
            role=request.POST.get('role', '').strip(),
            bio=request.POST.get('bio', '').strip(),
            linkedin_url=request.POST.get('linkedin_url', '').strip(),
            twitter_url=request.POST.get('twitter_url', '').strip(),
            order=int(request.POST.get('order', 0) or 0),
            is_active=request.POST.get('is_active') == 'on',
        )
        if request.FILES.get('image'):
            member.image = request.FILES['image']
            member.save()
        return JsonResponse({'success': True, 'id': member.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@administrator_required
@login_required(login_url='login')
def edit_team_member(request, pk):
    member = get_object_or_404(TeamMember, pk=pk)

    if request.method == 'GET':
        return JsonResponse({
            'id': member.id,
            'name': member.name,
            'role': member.role,
            'bio': member.bio,
            'linkedin_url': member.linkedin_url,
            'twitter_url': member.twitter_url,
            'order': member.order,
            'is_active': member.is_active,
            'image': member.image.url if member.image else '',
        })

    elif request.method == 'POST':
        try:
            member.name = request.POST.get('name', '').strip()
            member.role = request.POST.get('role', '').strip()
            member.bio = request.POST.get('bio', '').strip()
            member.linkedin_url = request.POST.get('linkedin_url', '').strip()
            member.twitter_url = request.POST.get('twitter_url', '').strip()
            member.order = int(request.POST.get('order', 0) or 0)
            member.is_active = request.POST.get('is_active') == 'on'
            if request.FILES.get('image'):
                member.image = request.FILES['image']
            member.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@administrator_required
@login_required(login_url='login')
@require_http_methods(["DELETE"])
def delete_team_member(request, pk):
    try:
        get_object_or_404(TeamMember, pk=pk).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def is_admin(user):
    return user.groups.filter(name='Administrator').exists()


@administrator_required
def user_list(request):
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')

    users = User.objects.select_related('profile').annotate(
        post_count=Count('posts', distinct=True)
    ).order_by('-date_joined')
    
    users = User.objects.select_related('profile').prefetch_related('groups')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if role_filter:
        users = users.filter(groups__name=role_filter)
    
    # Get user counts
    all_count = User.objects.count()
    admin_count = User.objects.filter(groups__name='Administrator').count()
    author_count = User.objects.filter(groups__name='Author').count()
    
    # Pagination
    paginator = Paginator(users, 10)
    page = request.GET.get('page')
    users = paginator.get_page(page)

    
    # Handle bulk actions
    if request.method == 'POST':
        form = BulkActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            selected_ids = json.loads(form.cleaned_data['selected_users'])
            
            if action == 'delete':
                User.objects.filter(id__in=selected_ids).exclude(id=request.user.id).delete()
                messages.success(request, f'Successfully deleted {len(selected_ids)} users.')
            elif action.startswith('change_role_'):
                role_name = action.split('_')[-1].title()
                try:
                    group = Group.objects.get(name=role_name)
                    for user_id in selected_ids:
                        user = User.objects.get(id=user_id)
                        user.groups.clear()
                        user.groups.add(group)
                        set_user_permissions_by_role(user, role_name)  # NEW: Set admin flags
                    messages.success(request, f'Successfully changed role for {len(selected_ids)} users.')
                except Group.DoesNotExist:
                    messages.error(request, f'Role {role_name} does not exist.')
            
            return redirect('users')
    
    bulk_form = BulkActionForm(initial={'selected_users': '[]'})
    
    context = {
        'users': users,
        'search': search,
        'role_filter': role_filter,
        'all_count': all_count,
        'admin_count': admin_count,
        'author_count': author_count,
        'bulk_form': bulk_form,
    }
    return render(request, 'dashboard/users.html', context)

@administrator_required
@login_required(login_url='login')
@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" has been created successfully.')
            return redirect('users')
    else:
        form = UserCreateForm()
    
    return render(request, 'dashboard/add_user.html', {'form': form})

@administrator_required
@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.user.id == user.id:
        return JsonResponse({'success': False, 'message': 'You cannot delete your own account'})
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        return JsonResponse({'success': True, 'message': f'User "{username}" has been deleted successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required(login_url='login')
def profile(request, user_id):
    # Check if user is editing themselves or if they're admin
    if user_id == request.user.id:
        target_user = request.user
        is_admin_editing = False

    else:
        # Must be admin to edit others
        if not (request.user.is_staff or request.user.groups.filter(name='Administrator').exists()):
            messages.error(request, 'You do not have permission to edit other users.')
            return redirect('profile', user_id=request.user.id)
        target_user = get_object_or_404(User, id=user_id)
        is_admin_editing = True
    
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    
    if request.method == 'POST':
        return handle_profile_update(request, target_user, profile, is_admin_editing)
    
    # GET request
    user_form = UserEditForm(instance=target_user, show_role=is_admin_editing)
    profile_form = UserProfileEditForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'target_user': target_user,
        'is_admin_editing': is_admin_editing,
        'can_edit_role': is_admin_editing,
    }
    
    return render(request, 'dashboard/profile.html', context)


@login_required(login_url='login')
def current_user_profile(request):
    """Wrapper view to redirect /users/profile/ to current user's profile"""
    return profile(request, user_id=request.user.id)


def handle_profile_update(request, target_user, profile, is_admin_editing):
    user_form = UserEditForm(request.POST, instance=target_user, show_role=is_admin_editing)
    profile_form = UserProfileEditForm(request.POST, request.FILES, instance=profile)
    
    if not (user_form.is_valid() and profile_form.is_valid()):
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'dashboard/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
            'target_user': target_user,
            'is_admin_editing': is_admin_editing,
            'can_edit_role': is_admin_editing,
        })
    
    try:
        with transaction.atomic():
            profile_form.save()
            user = user_form.save()
            
            if is_admin_editing and 'role' in user_form.cleaned_data:
                role = user_form.cleaned_data.get('role')
                if role:
                    user.groups.set([role])
                    set_user_permissions_by_role(user, role.name)
        
        success_msg = f'{"User" if is_admin_editing else "Profile"} updated successfully.'
        messages.success(request, success_msg, extra_tags='profile_only')
        
        # Fix the redirect
        if is_admin_editing:
            return redirect('profile', user_id=target_user.id)
        
    except Exception as e:
        messages.error(request, 'Error updating profile. Please try again.')
        return render(request, 'dashboard/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
            'target_user': target_user,
            'is_admin_editing': is_admin_editing,
            'can_edit_role': is_admin_editing,
        })


def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    storage = messages.get_messages(request)
    for _ in storage:
        pass
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            
            # Handle the 'next' parameter for redirect after login
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard') 
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'dashboard/login.html')

def logout(request):
    auth_logout(request)
    return redirect('login')


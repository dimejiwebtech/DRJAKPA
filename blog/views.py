from django.shortcuts import render, get_object_or_404
from .models import Post, Category, Comment
from .forms import CommentForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string

def blog(request):
    # Get featured posts - try featured first, then fall back to latest
    featured_posts = list(Post.objects.filter(
        status='published', 
        is_trashed=False, 
        is_featured=True
    ).select_related('author').prefetch_related('category')[:3])
    
    # If not enough featured, fill with latest posts
    if len(featured_posts) < 3:
        existing_ids = [p.id for p in featured_posts]
        additional = Post.objects.filter(
            status='published', 
            is_trashed=False
        ).exclude(id__in=existing_ids).select_related('author').prefetch_related('category')[:3 - len(featured_posts)]
        featured_posts.extend(list(additional))
    
    # Get all categories
    categories = Category.objects.all()
    
    # Get all published posts with pagination (4 per page)
    posts_list = Post.objects.filter(
        status='published', 
        is_trashed=False
    ).select_related('author').prefetch_related('category').order_by('-published_date')
    paginator = Paginator(posts_list, 4)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    context = {
        'featured_posts': featured_posts,
        'categories': categories,
        'posts': posts,
    }
    return render(request, 'blog/blog.html', context)


def posts_by_category_or_post(request, slug):
    # Check if it's a category
    category = Category.objects.filter(slug=slug).first()
    if category:
        posts = Post.objects.filter(
            status='published', 
            is_trashed=False,
            category=category
        ).select_related('author').prefetch_related('category').order_by('-published_date')
        paginator = Paginator(posts, 6)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'category': category,
            'categories': Category.objects.all(),
        }
        return render(request, 'blog/posts_by_category.html', context)

    # Otherwise treat as single post
    single_post = get_object_or_404(Post, slug=slug, status='published', is_trashed=False)
    
    # Related posts by category (fetch 5)
    post_categories = single_post.category.all()
    related_posts = Post.objects.filter(
        category__in=post_categories,
        status='published',
        is_trashed=False
    ).exclude(id=single_post.id).distinct()[:5]

    # Comment handling
    comment_form = CommentForm()
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        parent_id = request.POST.get('parent_id')
        
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = single_post
            
            # Auto-approve if user is superuser
            if request.user.is_authenticated and request.user.is_superuser:
                comment.approved = True
            
            if parent_id:
                comment.parent = Comment.objects.get(id=parent_id)
            
            comment.save()
            
            # Show different message based on approval status
            if comment.approved:
                messages.success(request, 'Your comment has been posted successfully!')
            else:
                messages.success(request, 'Your comment is awaiting approval.')
            
            from django.shortcuts import redirect
            return redirect('posts_by_category_or_post', slug=slug)

    # Get approved comments (with load more support)
    show_all = request.GET.get('show_all_comments')
    if show_all:
        comments = single_post.comments.filter(approved=True, parent=None).prefetch_related('replies').order_by('-created_on')
    else:
        comments = single_post.comments.filter(approved=True, parent=None).prefetch_related('replies').order_by('-created_on')[:10]
    total_comments = single_post.comments.filter(approved=True).count()

    context = {
        'single_post': single_post,
        'related_posts': related_posts,
        'categories': Category.objects.all(),
        'comment_form': comment_form,
        'comments': comments,
        'total_comments': total_comments,
        'has_more_comments': total_comments > 10 and not show_all,
    }
    return render(request, 'blog/single_blog.html', context)


def load_more(request):    
    page_number = request.GET.get('page', 2)
    posts_list = Post.objects.filter(
        status='published', 
        is_trashed=False
    ).select_related('author').prefetch_related('category').order_by('-published_date')
    
    paginator = Paginator(posts_list, 4)
    page_obj = paginator.get_page(page_number)
    
    # Render posts HTML
    html = render_to_string('blog/partials/post_cards.html', {'posts': page_obj})
    
    return JsonResponse({
        'success': True,
        'html': html,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None
    })


def search(request):    
    query = request.GET.get('q', '')
    
    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) | 
            Q(excerpt__icontains=query),
            status='published',
            is_trashed=False
        ).select_related('author').prefetch_related('category').order_by('-published_date')
    else:
        posts = Post.objects.none()
    
    paginator = Paginator(posts, 12)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    
    context = {
        'query': query,
        'posts': page_obj,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/search_results.html', context)


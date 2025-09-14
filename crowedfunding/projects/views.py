from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Project, ProjectPicture, Donation, Comment, Rating, Report, Category, Tag
from .forms import ProjectForm, ProjectPictureForm, CommentForm, RatingForm, ReportForm, DonationForm

def project_list(request):
    projects = (Project.objects.filter(is_cancelled=False, end_time__gt=timezone.now())
                .select_related('category', 'creator')
                .prefetch_related('tags', 'pictures'))
    
    category_id = request.GET.get('category')
    if category_id:
        projects = projects.filter(category_id=category_id)
    
    search_query = request.GET.get('q')
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) | 
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    return render(request, 'projects/project_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None,
        'search_query': search_query or ''
    })

@login_required
def dashboard(request):
    user = request.user
    user_projects = (Project.objects.filter(creator=user)
                     .select_related('category')
                     .prefetch_related('pictures', 'tags'))
    user_donations = (Donation.objects.filter(user=user)
                      .select_related('project', 'project__creator')
                      .order_by('-donated_at'))
    return render(request, 'projects/dashboard.html', {
        'user_projects': user_projects,
        'user_donations': user_donations
    })

def project_detail(request, slug):
    project = get_object_or_404(
        Project.objects.select_related('category', 'creator')
               .prefetch_related(
                    'tags',
                    'pictures',
                    'comments__user',           # top-level comment authors
                    'comments__replies__user',  # reply authors to avoid N+1
                    'donations__user',
                    'ratings'
                ),
        slug=slug
    )
    donations = project.donations.select_related('user').order_by('-donated_at')[:5]
    comments = project.comments.select_related('user').filter(parent=None).order_by('-created_at')
    user_rating = None
    donation_form = DonationForm()
    
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(project=project, user=request.user)
        except Rating.DoesNotExist:
            pass
    
    similar_projects = (Project.objects.filter(
        tags__in=project.tags.all(),
        is_cancelled=False,
        end_time__gt=timezone.now()
    ).exclude(id=project.id)
     .select_related('category', 'creator')
     .prefetch_related('tags', 'pictures')
     .distinct()[:4])
    
    return render(request, 'projects/project_detail.html', {
        'project': project,
        'donations': donations,
        'comments': comments,
        'user_rating': user_rating,
        'similar_projects': similar_projects,
    'donation_form': donation_form,
    })

@login_required
def create_project(request):
    if request.method == 'POST':
        project_form = ProjectForm(request.POST)
        picture_form = ProjectPictureForm(request.POST, request.FILES)
        
        if project_form.is_valid():
            project = project_form.save(commit=False)
            project.creator = request.user
            project.save()
            
            tags = project_form.cleaned_data['tags']
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                for tag_name in tag_list:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    project.tags.add(tag)
            
            pictures = request.FILES.getlist('images')
            for picture in pictures:
                ProjectPicture.objects.create(project=project, image=picture)
            
            messages.success(request, 'Project created successfully.')
            return redirect('project_detail', slug=project.slug)
    else:
        project_form = ProjectForm()
        picture_form = ProjectPictureForm()
    
    return render(request, 'projects/create_project.html', {
        'project_form': project_form,
        'picture_form': picture_form
    })

@login_required
def edit_project(request, slug):
    project = get_object_or_404(Project, slug=slug, creator=request.user)
    if project.donations.exists():
        messages.error(request, 'Cannot edit a project after donations have been made.')
        return redirect('project_detail', slug=project.slug)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            updated = form.save(commit=False)
            # retain creator
            updated.creator = project.creator
            updated.save()
            # update tags
            tags = form.cleaned_data['tags']
            project.tags.clear()
            if tags:
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
                for tag_name in tag_list:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    project.tags.add(tag)
            messages.success(request, 'Project updated successfully.')
            return redirect('project_detail', slug=project.slug)
    else:
        # populate tags field with comma-separated names
        initial = {'tags': ', '.join(project.tags.values_list('name', flat=True))}
        form = ProjectForm(instance=project, initial=initial)
    return render(request, 'projects/edit_project.html', {'form': form, 'project': project})

@login_required
def donate(request, slug):
    project = get_object_or_404(Project, slug=slug)
    # Block donations if project cancelled or expired
    now = timezone.now()
    if project.is_cancelled or project.end_time <= now:
        messages.error(request, 'Donations are closed for this project.')
    return redirect('project_detail', slug=project.slug)
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.project = project
            donation.user = request.user
            donation.save()
            messages.success(request, 'Thank you for your donation!')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('project_detail', project_id=project.id)

@login_required
def add_comment(request, slug):
    project = get_object_or_404(Project, slug=slug)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.project = project
            comment.user = request.user
            
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass
            
            comment.save()
            messages.success(request, 'Comment added successfully.')
    
    return redirect('project_detail', slug=project.slug)

@login_required
def rate_project(request, slug):
    project = get_object_or_404(Project, slug=slug)
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            if project.creator_id == request.user.id:
                messages.error(request, 'You cannot rate your own project.')
                return redirect('project_detail', slug=project.slug)
            rating_value = form.cleaned_data['value']
            
            rating, created = Rating.objects.update_or_create(
                project=project,
                user=request.user,
                defaults={'value': rating_value}
            )
            
            messages.success(request, 'Rating submitted successfully.')
    
    return redirect('project_detail', slug=project.slug)

@login_required
def report_content(request, content_type, content_id):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.report_type = content_type
            
            if content_type == 'project':
                report.project = get_object_or_404(Project, id=content_id)
            else:
                report.comment = get_object_or_404(Comment, id=content_id)
            
            report.save()
            messages.success(request, 'Report submitted successfully. Thank you for helping us keep the platform safe.')
    
    if content_type == 'project':
        project = get_object_or_404(Project, id=content_id)
        return redirect('project_detail', slug=project.slug)
    else:
        comment = get_object_or_404(Comment, id=content_id)
        return redirect('project_detail', slug=comment.project.slug)

@login_required
def cancel_project(request, slug):
    project = get_object_or_404(Project, slug=slug, creator=request.user)
    if request.method != 'POST':
        messages.error(request, 'Cancellation must be performed via POST request.')
        return redirect('project_detail', slug=project.slug)
    if project.is_cancelled:
        messages.info(request, 'Project already cancelled.')
        return redirect('project_detail', slug=project.slug)
    percentage = project.donation_percentage
    if percentage < 25:
        project.is_cancelled = True
        project.save(update_fields=['is_cancelled'])
        messages.success(request, 'Project cancelled successfully.')
    else:
        messages.error(request, 'Cannot cancel project. Donations have reached or exceeded 25% of the target.')

    return redirect('project_detail', slug=project.slug)
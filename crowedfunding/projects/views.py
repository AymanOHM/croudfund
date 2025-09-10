from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Project, ProjectPicture, Donation, Comment, Rating, Report, Category, Tag
from .forms import ProjectForm, ProjectPictureForm, CommentForm, RatingForm, ReportForm

def project_list(request):
    projects = Project.objects.filter(is_cancelled=False, end_time__gt=timezone.now())
    
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

def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    donations = project.donations.order_by('-donated_at')[:5]
    comments = project.comments.filter(parent=None).order_by('-created_at')
    user_rating = None
    
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(project=project, user=request.user)
        except Rating.DoesNotExist:
            pass
    
    similar_projects = Project.objects.filter(
        tags__in=project.tags.all(), 
        is_cancelled=False,
        end_time__gt=timezone.now()
    ).exclude(id=project.id).distinct()[:4]
    
    return render(request, 'projects/project_detail.html', {
        'project': project,
        'donations': donations,
        'comments': comments,
        'user_rating': user_rating,
        'similar_projects': similar_projects,
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
            return redirect('project_detail', project_id=project.id)
    else:
        project_form = ProjectForm()
        picture_form = ProjectPictureForm()
    
    return render(request, 'projects/create_project.html', {
        'project_form': project_form,
        'picture_form': picture_form
    })

@login_required
def donate(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                messages.error(request, 'Donation amount must be positive.')
                return redirect('project_detail', project_id=project.id)
            
            Donation.objects.create(
                project=project,
                user=request.user,
                amount=amount
            )
            
            messages.success(request, 'Thank you for your donation!')
            return redirect('project_detail', project_id=project.id)
        except ValueError:
            messages.error(request, 'Invalid donation amount.')
    
    return redirect('project_detail', project_id=project.id)

@login_required
def add_comment(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
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
    
    return redirect('project_detail', project_id=project.id)

@login_required
def rate_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating_value = form.cleaned_data['value']
            
            rating, created = Rating.objects.update_or_create(
                project=project,
                user=request.user,
                defaults={'value': rating_value}
            )
            
            messages.success(request, 'Rating submitted successfully.')
    
    return redirect('project_detail', project_id=project.id)

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
        return redirect('project_detail', project_id=content_id)
    else:
        comment = get_object_or_404(Comment, id=content_id)
        return redirect('project_detail', project_id=comment.project.id)

@login_required
def cancel_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, creator=request.user)
    
    if project.donation_percentage < 25:
        project.is_cancelled = True
        project.save()
        messages.success(request, 'Project cancelled successfully.')
    else:
        messages.error(request, 'Cannot cancel project. Donations have exceeded 25% of the target.')
    
    return redirect('project_detail', project_id=project.id)
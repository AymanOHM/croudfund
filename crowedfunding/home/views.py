from django.shortcuts import render
from projects.models import Project, Category
from django.utils import timezone
from django.db.models import Avg, Count

def home(request):
    highest_rated = Project.objects.filter(
        is_cancelled=False, 
        end_time__gt=timezone.now()
    ).annotate(
        avg_rating=Avg('ratings__value')
    ).order_by('-avg_rating')[:5]
    
    latest_projects = Project.objects.filter(
        is_cancelled=False, 
        end_time__gt=timezone.now()
    ).order_by('-created_at')[:5]
    
    featured_projects = Project.objects.filter(
        is_featured=True, 
        is_cancelled=False, 
        end_time__gt=timezone.now()
    ).order_by('-created_at')[:5]
    
    categories = Category.objects.annotate(project_count=Count('project'))
    
    return render(request, 'home/home.html', {
        'highest_rated': highest_rated,
        'latest_projects': latest_projects,
        'featured_projects': featured_projects,
        'categories': categories,
    })
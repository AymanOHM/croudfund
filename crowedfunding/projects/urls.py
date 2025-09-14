from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('<slug:slug>/', views.project_detail, name='project_detail'),
    path('create/', views.create_project, name='create_project'),
    path('<slug:slug>/edit/', views.edit_project, name='edit_project'),
    path('<slug:slug>/donate/', views.donate, name='donate'),
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('<slug:slug>/rate/', views.rate_project, name='rate_project'),
    path('report/<str:content_type>/<int:content_id>/', views.report_content, name='report_content'),
    path('<slug:slug>/cancel/', views.cancel_project, name='cancel_project'),
]
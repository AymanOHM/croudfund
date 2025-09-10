from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('create/', views.create_project, name='create_project'),
    path('<int:project_id>/donate/', views.donate, name='donate'),
    path('<int:project_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:project_id>/rate/', views.rate_project, name='rate_project'),
    path('report/<str:content_type>/<int:content_id>/', views.report_content, name='report_content'),
    path('<int:project_id>/cancel/', views.cancel_project, name='cancel_project'),
]
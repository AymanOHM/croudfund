from django import forms
from .models import Project, ProjectPicture, Comment, Rating, Report

class ProjectForm(forms.ModelForm):
    tags = forms.CharField(required=False, help_text="Enter tags separated by commas")
    
    class Meta:
        model = Project
        fields = ['title', 'details', 'category', 'total_target', 'start_time', 'end_time', 'tags']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ProjectPictureForm(forms.ModelForm):
    class Meta:
        model = ProjectPicture
        fields = ['image']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['value']

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
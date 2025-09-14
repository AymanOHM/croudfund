from django import forms
from .models import Project, ProjectPicture, Comment, Rating, Report, Donation

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

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['amount']

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError('Donation amount must be positive.')
        return amount
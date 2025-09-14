from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()

class Category(models.Model):
    # Indexed for faster filtering/grouping by category name in listings & admin
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class Project(models.Model):
    title = models.CharField(max_length=200)
    details = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    total_target = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    tags = models.ManyToManyField(Tag)
    is_featured = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    
    def __str__(self):
        return self.title
    
    @property
    def total_donations(self):
        return self.donations.aggregate(total=models.Sum('amount'))['total'] or 0
    
    @property
    def donation_percentage(self):
        if self.total_target > 0:
            return (self.total_donations / self.total_target) * 100
        return 0
    
    @property
    def average_rating(self):
        avg = self.ratings.aggregate(avg_rating=models.Avg('value'))['avg_rating']
        return avg if avg else 0

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'End time must be later than start time.'})

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        base_slug = slugify(self.title)[:200]
        if not self.slug or Project.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='project_end_after_start'
            )
        ]
        indexes = [
            # Speeds up queries filtering active/cancelled and ordering or filtering by end_time
            models.Index(fields=['is_cancelled', 'end_time'], name='project_cancel_end_idx')
        ]

class ProjectPicture(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pictures')
    image = models.ImageField(upload_to='project_pictures/')
    
    def __str__(self):
        return f"Picture for {self.project.title}"

class Donation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='donations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])
    donated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} donated {self.amount} to {self.project.title}"

class Comment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.project.title}"

class Rating(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    value = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    
    class Meta:
        unique_together = ('project', 'user')
    
    def __str__(self):
        return f"{self.user.email} rated {self.project.title} as {self.value}"

class Report(models.Model):
    REPORT_CHOICES = [
        ('project', 'Project'),
        ('comment', 'Comment'),
    ]
    
    report_type = models.CharField(max_length=10, choices=REPORT_CHOICES)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.report_type == 'project':
            return f"Report on {self.project.title} by {self.user.email}"
        else:
            return f"Report on comment by {self.user.email}"
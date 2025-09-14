from django.contrib import admin
from .models import Category, Tag, Project, ProjectPicture, Donation, Comment, Rating, Report

class ProjectPictureInline(admin.TabularInline):
    model = ProjectPicture
    extra = 1

class DonationInline(admin.TabularInline):
    model = Donation
    extra = 0
    readonly_fields = ('user', 'amount', 'donated_at')

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('user', 'content', 'created_at')

class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0
    readonly_fields = ('user', 'value')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'category', 'total_target', 'start_time', 'end_time', 'is_featured', 'is_cancelled')
    list_filter = ('category', 'is_featured', 'is_cancelled', 'start_time', 'end_time')
    search_fields = ('title', 'creator__email', 'creator__first_name', 'creator__last_name')
    date_hierarchy = 'start_time'
    ordering = ('-created_at',)
    autocomplete_fields = ('creator', 'category', 'tags')
    inlines = [ProjectPictureInline, DonationInline, CommentInline, RatingInline]
    readonly_fields = ('created_at', 'slug')

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'amount', 'donated_at')
    list_filter = ('donated_at',)
    search_fields = ('user__email', 'project__title')
    date_hierarchy = 'donated_at'
    autocomplete_fields = ('user', 'project')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'project__title', 'content')
    date_hierarchy = 'created_at'
    autocomplete_fields = ('user', 'project', 'parent')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'value')
    list_filter = ('value',)
    search_fields = ('user__email', 'project__title')
    autocomplete_fields = ('user', 'project')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'report_type', 'project', 'comment', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('user__email', 'reason')
    date_hierarchy = 'created_at'
    autocomplete_fields = ('user', 'project', 'comment')
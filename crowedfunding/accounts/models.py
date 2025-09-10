from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    phone_regex = RegexValidator(regex=r'^01[0-2,5]{1}[0-9]{8}$', message="Egyptian phone number is required")
    mobile_phone = models.CharField(validators=[phone_regex], max_length=11, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default.png')
    birthdate = models.DateField(null=True, blank=True)
    facebook_profile = models.URLField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    activation_token = models.CharField(max_length=100, blank=True)
    activation_token_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email
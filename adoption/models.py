# adoption/models.py
# Make sure this file has your actual models

from django.db import models
from django.contrib.auth.models import User
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.utils import timezone
import pytz
import datetime
import numpy as np
import json

class AdminManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not username:
            raise ValueError('Users must have a username')
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(
            username,
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class Admin(AbstractBaseUser):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('moderator', 'Moderator'),
    ]
    role = models.CharField(max_length=255, choices=ROLE_CHOICES)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=255, choices=STATUS_CHOICES)
    is_admin = models.BooleanField(default=False)

    objects = AdminManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

class PetAdoptionRequestTable(models.Model):
    pet = models.ForeignKey('PendingPetForAdoption', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    adopter_type = models.CharField(max_length=20, choices=[
        ('Individual', 'Individual'),
        ('Family', 'Family'),
        ('Organization', 'Organization')
    ])
    living_situation = models.CharField(max_length=20, choices=[
        ('Apartment', 'Apartment'),
        ('House', 'House'),
        ('Condo', 'Condo')
    ])
    previous_pet_experience = models.TextField()
    owns_other_pets = models.CharField(max_length=100)
    adoption_request_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')

    def __str__(self):
        return f"Adoption Request for {self.pet.name} by {self.user.username}"

class PetAdoptionTable(models.Model):
    pet = models.ForeignKey('PendingPetForAdoption', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    contact_number = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    request_date = models.DateTimeField(null=True, blank=True)
    approval_date_time = models.DateTimeField(null=True, blank=True)
    adopter_type = models.CharField(max_length=20, choices=[
        ('Individual', 'Individual'),
        ('Family', 'Family'),
        ('Organization', 'Organization')
    ])
    living_situation = models.CharField(max_length=20, choices=[
        ('Apartment', 'Apartment'),
        ('House', 'House'),
        ('Condo', 'Condo')
    ])
    previous_pet_experience = models.TextField()
    owns_other_pets = models.CharField(max_length=100)
    facebook_profile_link = models.URLField(max_length=200, blank=True, null=True)
    adoption_request_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('review', 'Review'),
        ('adopted', 'Adopted'),
        ('pet_is_adopted', 'Pet_is_adopted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')

    id_type = models.CharField(max_length=100, choices=[
        ('e-Card / UMID', 'e-Card / UMID'),
        ('Employee ID / Office ID', 'Employee ID / Office ID'),
        ('Driver License', 'Driver License'),
        ('Professional Regulation Commission (PRC) ID', 'Professional Regulation Commission (PRC) ID'),
        ('Passport', 'Passport'),
        ('Senior Citizen ID', 'Senior Citizen ID'),
        ('SSS ID', 'SSS ID'),
        ('COMELEC / Voter ID / COMELEC Registration Form', 'COMELEC / Voter ID / COMELEC Registration Form'),
        ('Philippine Identification (PhilID / ePhilID)', 'Philippine Identification (PhilID / ePhilID)'),
        ('NBI Clearance', 'NBI Clearance'),
        ('Integrated Bar of the Philippines (IBP) ID', 'Integrated Bar of the Philippines (IBP) ID'),
        ('Firearms License', 'Firearms License'),
        ('AFPSLAI ID', 'AFPSLAI ID'),
        ('PVAO ID', 'PVAO ID'),
        ('AFP Beneficiary ID', 'AFP Beneficiary ID'),
        ('BIR (TIN)', 'BIR (TIN)'),
        ('Pag-ibig ID', 'Pag-ibig ID'),
        ('Person With Disability (PWD) ID', 'Person With Disability (PWD) ID'),
        ('Solo Parent ID', 'Solo Parent ID'),
        ('Pantawid Pamilya Pilipino Program (4Ps) ID', 'Pantawid Pamilya Pilipino Program (4Ps) ID'),
        ('Barangay ID', 'Barangay ID'),
        ('Philippine Postal ID', 'Philippine Postal ID'),
        ('Phil-health ID', 'Phil-health ID'),
        ('School ID', 'School ID'),
        ('Other valid government-issued IDs or Documents with picture and signature', 'Other valid government-issued IDs or Documents with picture and signature'),
    ], blank=True, null=True)

    id_number = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Adoption Request for {self.pet.name} by {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.request_date:
            philippines_time = timezone.now().astimezone(pytz.timezone('Asia/Manila'))
            self.request_date = philippines_time
        super().save(*args, **kwargs)

class PendingPetForAdoption(models.Model):
    name = models.CharField(max_length=100)
    animal_type = models.CharField(max_length=50)
    breed = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    gender = models.CharField(max_length=10)
    age = models.CharField(max_length=30)
    location = models.CharField(max_length=100)
    additional_details = models.TextField()
    img = models.ImageField(upload_to='pics')
    author = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    adoption_status = models.CharField(max_length=20, default='pending')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image_features = models.TextField(null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.author = self.user.username
        super(PendingPetForAdoption, self).save(*args, **kwargs)

    def get_image_features_array(self):
        if self.image_features:
            try:
                return np.array(json.loads(self.image_features))
            except json.JSONDecodeError:
                print(f"Invalid JSON data for pet {self.name}: {self.image_features}")
                return None
        return None

class TrackUpdateTable(models.Model):
    pet_adoption_request = models.ForeignKey(PetAdoptionTable, on_delete=models.CASCADE)
    followup_date = models.DateField()
    LIVING_SITUATION_CHOICES = [
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('both', 'Both'),
    ]
    housing_type_choices = [
        ('cage', 'Cage'),
        ('free_roaming', 'Free Roaming'),
    ]
    
    living_situation = models.CharField(max_length=10, choices=LIVING_SITUATION_CHOICES)
    housing_type = models.CharField(max_length=15, choices=housing_type_choices)
    behavioral_changes = models.TextField(blank=True)
    health_issues = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    photos = models.ImageField(upload_to='track_updates_photos/', blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Update for {self.pet_adoption_request.pet.name} on {self.followup_date}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

class AdminUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_super_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class PageView(models.Model):
    page_name = models.CharField(max_length=100, default='landing')
    views = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.page_name} - {self.views} views"

    class Meta:
        verbose_name_plural = "Page Views"
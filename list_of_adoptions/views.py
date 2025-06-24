# views.py - Add this to your adoption app views
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import PendingPetForAdoption
import json

@require_http_methods(["GET"])
def get_pets_locations(request):
    """
    API endpoint to get all pets with their locations for the map
    """
    try:
        # Query all pending pets that have location data
        pets = PendingPetForAdoption.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            status='pending'  # Only show available pets
        ).select_related('user')  # Optimize database queries
        
        pets_data = []
        for pet in pets:
            # Build image URL
            image_url = pet.image.url if pet.image else None
            
            # Determine pet type (you may need to adjust field names)
            pet_type = getattr(pet, 'pet_type', 'other').lower()
            
            pets_data.append({
                'id': pet.id,
                'name': pet.name,
                'type': pet_type,
                'breed': getattr(pet, 'breed', ''),
                'age': getattr(pet, 'age', None),
                'lat': float(pet.latitude),
                'lng': float(pet.longitude),
                'description': getattr(pet, 'description', ''),
                'image_url': image_url,
                'owner_contact': getattr(pet.user, 'phone', '') if pet.user else '',
                'location_name': getattr(pet, 'location', ''),
                'created_date': pet.created_at.isoformat() if hasattr(pet, 'created_at') else None,
            })
        
        return JsonResponse(pets_data, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def search_pets_by_location(request):
    """
    API endpoint to search pets by location and radius
    """
    try:
        data = json.loads(request.body)
        
        center_lat = float(data.get('lat'))
        center_lng = float(data.get('lng'))
        radius_km = float(data.get('radius', 5))
        pet_type = data.get('pet_type', 'all')
        
        # Get all pets
        pets_query = PendingPetForAdoption.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            status='pending'
        )
        
        # Filter by pet type if specified
        if pet_type != 'all':
            pets_query = pets_query.filter(pet_type__icontains=pet_type)
        
        pets_data = []
        for pet in pets_query:
            # Calculate distance using Haversine formula
            distance = calculate_distance(
                center_lat, center_lng,
                float(pet.latitude), float(pet.longitude)
            )
            
            if distance <= radius_km:
                image_url = pet.image.url if pet.image else None
                
                pets_data.append({
                    'id': pet.id,
                    'name': pet.name,
                    'type': getattr(pet, 'pet_type', 'other').lower(),
                    'breed': getattr(pet, 'breed', ''),
                    'age': getattr(pet, 'age', None),
                    'lat': float(pet.latitude),
                    'lng': float(pet.longitude),
                    'description': getattr(pet, 'description', ''),
                    'image_url': image_url,
                    'distance': round(distance, 2),
                    'owner_contact': getattr(pet.user, 'phone', '') if pet.user else '',
                })
        
        return JsonResponse({
            'pets': pets_data,
            'count': len(pets_data),
            'search_params': {
                'lat': center_lat,
                'lng': center_lng,
                'radius': radius_km,
                'pet_type': pet_type
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points using Haversine formula
    Returns distance in kilometers
    """
    import math
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r


# urls.py - Add these URLs to your adoption app urls
from django.urls import path
from . import views

urlpatterns = [
    # ... your existing URLs
    path('api/pets/locations/', views.get_pets_locations, name='pets_locations_api'),
    path('api/pets/search/', views.search_pets_by_location, name='pets_search_api'),
]


# models.py - Make sure your PendingPetForAdoption model has these fields
from django.db import models
from django.contrib.auth.models import User

class PendingPetForAdoption(models.Model):
    PET_TYPES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('rabbit', 'Rabbit'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('adopted', 'Adopted'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    pet_type = models.CharField(max_length=20, choices=PET_TYPES, default='other')
    breed = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='pets/', blank=True, null=True)
    
    # Location fields - ADD THESE IF NOT PRESENT
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)  # Human-readable location
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.pet_type}"
    
    class Meta:
        ordering = ['-created_at']


# If you need to add the location fields to existing model, create a migration:
# python manage.py makemigrations
# python manage.py migrate
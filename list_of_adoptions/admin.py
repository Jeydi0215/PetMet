# admin.py - Enhanced admin interface for managing pet locations
from django.contrib import admin
from django.utils.html import format_html
from .models import PendingPetForAdoption

@admin.register(PendingPetForAdoption)
class PendingPetForAdoptionAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'pet_type', 'breed', 'age', 'status', 
        'has_location', 'location_display', 'created_at'
    ]
    list_filter = ['pet_type', 'status', 'created_at']
    search_fields = ['name', 'breed', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'location_map_link']
    
    fieldsets = (
        ('Pet Information', {
            'fields': ('name', 'pet_type', 'breed', 'age', 'description', 'image')
        }),
        ('Owner Information', {
            'fields': ('user',)
        }),
        ('Location Information', {
            'fields': ('latitude', 'longitude', 'location', 'location_map_link'),
            'description': 'Add coordinates to show this pet on the proximity map'
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_location(self, obj):
        """Show if pet has location coordinates"""
        if obj.latitude and obj.longitude:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    has_location.short_description = 'Has Location'
    has_location.admin_order_field = 'latitude'
    
    def location_display(self, obj):
        """Display location in a readable format"""
        if obj.latitude and obj.longitude:
            return f"{obj.latitude}, {obj.longitude}"
        return "No location set"
    location_display.short_description = 'Coordinates'
    
    def location_map_link(self, obj):
        """Provide a link to view location on Google Maps"""
        if obj.latitude and obj.longitude:
            google_maps_url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html(
                '<a href="{}" target="_blank">View on Google Maps</a>',
                google_maps_url
            )
        return "No location available"
    location_map_link.short_description = 'Map Link'
    
    def get_queryset(self, request):
        """Optimize queries by selecting related user data"""
        return super().get_queryset(request).select_related('user')


# management/commands/geocode_pets.py - Command to add coordinates to existing pets
# Create this file: your_app/management/commands/geocode_pets.py
import requests
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from adoption.models import PendingPetForAdoption

class Command(BaseCommand):
    help = 'Geocode pet locations that don\'t have coordinates'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
    
    def handle(self, *args, **options):
        pets_without_coords = PendingPetForAdoption.objects.filter(
            latitude__isnull=True,
            longitude__isnull=True
        ).exclude(location='')
        
        self.stdout.write(f"Found {pets_without_coords.count()} pets without coordinates")
        
        for pet in pets_without_coords:
            if pet.location:
                self.stdout.write(f"Geocoding {pet.name} at {pet.location}")
                
                if not options['dry_run']:
                    coords = self.geocode_location(pet.location)
                    if coords:
                        pet.latitude = coords['lat']
                        pet.longitude = coords['lng']
                        pet.save()
                        self.stdout.write(
                            self.style.SUCCESS(f"Updated {pet.name}: {coords}")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"Failed to geocode {pet.location}")
                        )
                    
                    # Rate limiting to avoid API limits
                    time.sleep(1)
    
    def geocode_location(self, location):
        """Geocode a location string to coordinates"""
        try:
            # Using Nominatim (free) - replace with your preferred geocoding service
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': location,
                'format': 'json',
                'limit': 1
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data:
                return {
                    'lat': float(data[0]['lat']),
                    'lng': float(data[0]['lon'])
                }
            
        except Exception as e:
            self.stdout.write(f"Geocoding error: {e}")
        
        return None


# forms.py - Form for adding/editing pets with location
from django import forms
from .models import PendingPetForAdoption

class PetAdoptionForm(forms.ModelForm):
    class Meta:
        model = PendingPetForAdoption
        fields = [
            'name', 'pet_type', 'breed', 'age', 'description', 
            'image', 'latitude', 'longitude', 'location'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'location': forms.TextInput(attrs={
                'placeholder': 'Click on map to set location or enter address'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        self.fields['pet_type'].widget.attrs.update({'class': 'form-control'})
        self.fields['breed'].widget.attrs.update({'class': 'form-control'})
        self.fields['age'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['location'].widget.attrs.update({'class': 'form-control'})


# To run the geocoding command:
# python manage.py geocode_pets --dry-run  # Test first
# python manage.py geocode_pets            # Actually update
# adoption/urls.py
# Updated URLs with cache management for fixing disappearing pets

from django.urls import path
from . import views

urlpatterns = [
    # ... your existing URL patterns ...
    
    # ===== EXISTING NLP SEARCH URLS =====
    path('search/', views.search_results, name='search_results'),
    path('api/search/suggestions/', views.search_suggestions_api, name='search_suggestions_api'),
    path('api/analyze-query/', views.analyze_query_api, name='analyze_query_api'),
    path('api/smart-search/', views.smart_search_api, name='smart_search_api'),
    
    # ===== EXISTING WEB SEARCH URL =====
    path('api/search/web/', views.search_pets_web, name='search_pets_web'),
    
    # ===== EXISTING MAP URLS =====
    path('api/pets/locations/', views.get_pets_locations, name='get_pets_locations'),
    path('api/search/location/', views.search_pets_by_location, name='search_pets_by_location'),
    path('api/debug/model/', views.debug_model_fields, name='debug_model_fields'),
    
    # ===== NEW CACHE MANAGEMENT URL (to fix disappearing pets) =====
    path('api/cache/clear-pets/', views.clear_pets_cache, name='clear_pets_cache'),
]

# If you don't have these existing URLs, here's the complete set:
"""
Complete URL configuration for your adoption app:

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),  # Your homepage
    path('search/', views.search_results, name='search_results'),
    
    # NLP Search APIs
    path('api/search/suggestions/', views.search_suggestions_api, name='search_suggestions_api'),
    path('api/analyze-query/', views.analyze_query_api, name='analyze_query_api'),
    path('api/smart-search/', views.smart_search_api, name='smart_search_api'),
    
    # Web Search API
    path('api/search/web/', views.search_pets_web, name='search_pets_web'),
    
    # Map APIs (Enhanced with caching)
    path('api/pets/locations/', views.get_pets_locations, name='get_pets_locations'),
    path('api/search/location/', views.search_pets_by_location, name='search_pets_by_location'),
    
    # Cache Management (NEW - fixes disappearing pets)
    path('api/cache/clear-pets/', views.clear_pets_cache, name='clear_pets_cache'),
    
    # Debug
    path('api/debug/model/', views.debug_model_fields, name='debug_model_fields'),
]
"""
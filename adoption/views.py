# adoption/views.py
# Complete views file with NLP search integration + Web Search

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json
import math
import requests
import time
from bs4 import BeautifulSoup
import re

# Import models directly from this app
from .models import PendingPetForAdoption

# Import NLP functionality
from .utils.search_helpers import perform_smart_search, get_search_suggestions, analyze_search_query, build_search_filters
from .utils.nlp_search import PetSearchNLP

# ==================== NEW WEB SEARCH CLASS ====================

class SimplePetWebSearch:
    """Simple web search for pets by name"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_pets_by_name(self, pet_name, max_results=10):
        """Search for pets by name across multiple sources"""
        all_results = []
        
        # Search Petfinder
        petfinder_results = self.search_petfinder_by_name(pet_name)
        all_results.extend(petfinder_results[:5])
        
        # Search Adopt-a-Pet
        adopt_pet_results = self.search_adopt_a_pet_by_name(pet_name)
        all_results.extend(adopt_pet_results[:5])
        
        return all_results[:max_results]
    
    def search_petfinder_by_name(self, pet_name):
        """Search Petfinder website for pets by name"""
        results = []
        try:
            # Search Petfinder website directly
            search_url = f"https://www.petfinder.com/search/pets-for-adoption/?name={pet_name}&type%5B%5D=cats&type%5B%5D=dogs"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find pet cards (adjust selectors based on actual Petfinder HTML)
                pet_cards = soup.find_all('div', class_='petCard-body') or soup.find_all('div', {'data-testid': 'pet-card'})
                
                for card in pet_cards[:5]:
                    try:
                        pet_data = self.extract_petfinder_data(card, pet_name)
                        if pet_data:
                            results.append(pet_data)
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Petfinder search error: {e}")
        
        return results
    
    def extract_petfinder_data(self, card, search_name):
        """Extract pet data from Petfinder card"""
        try:
            # Find pet name
            name_elem = (card.find('h3') or 
                        card.find('h2') or 
                        card.find(class_='petCard-name') or
                        card.find(attrs={'data-testid': 'pet-name'}))
            
            if not name_elem:
                return None
                
            pet_name = name_elem.get_text(strip=True)
            
            # Check if name matches (case insensitive)
            if search_name.lower() not in pet_name.lower():
                return None
            
            # Find image
            img_elem = card.find('img')
            image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
            
            # Find link
            link_elem = card.find('a') or card.find_parent('a')
            pet_url = link_elem.get('href') if link_elem else None
            if pet_url and pet_url.startswith('/'):
                pet_url = 'https://www.petfinder.com' + pet_url
            
            # Extract additional info
            info_text = card.get_text()
            
            return {
                'id': f"pf_{hash(pet_name + str(time.time()))}",
                'name': pet_name,
                'animal_type': self.extract_animal_type(info_text),
                'breed': self.extract_breed(info_text),
                'color': self.extract_color(info_text),
                'age': self.extract_age(info_text),
                'location': self.extract_location(info_text),
                'image_url': image_url,
                'source': 'Petfinder',
                'source_url': pet_url,
                'description': self.clean_text(info_text)[:200] + '...' if len(info_text) > 200 else self.clean_text(info_text)
            }
            
        except Exception as e:
            return None
    
    def search_adopt_a_pet_by_name(self, pet_name):
        """Search Adopt-a-Pet website"""
        results = []
        try:
            search_url = f"https://www.adoptapet.com/s/adopt-a-pet?pet_name={pet_name}"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find pet listings
                pet_cards = (soup.find_all('div', class_='search-result') or 
                           soup.find_all('div', class_='pet-item') or
                           soup.find_all('article'))
                
                for card in pet_cards[:5]:
                    try:
                        pet_data = self.extract_adopt_a_pet_data(card, pet_name)
                        if pet_data:
                            results.append(pet_data)
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Adopt-a-Pet search error: {e}")
        
        return results
    
    def extract_adopt_a_pet_data(self, card, search_name):
        """Extract data from Adopt-a-Pet card"""
        try:
            # Find pet name
            name_elem = (card.find('h3') or 
                        card.find('h2') or 
                        card.find(class_='pet-name'))
            
            if not name_elem:
                return None
                
            pet_name = name_elem.get_text(strip=True)
            
            # Check if name matches
            if search_name.lower() not in pet_name.lower():
                return None
            
            # Find image
            img_elem = card.find('img')
            image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
            
            # Find link
            link_elem = card.find('a') or card.find_parent('a')
            pet_url = link_elem.get('href') if link_elem else None
            if pet_url and pet_url.startswith('/'):
                pet_url = 'https://www.adoptapet.com' + pet_url
            
            # Extract info
            info_text = card.get_text()
            
            return {
                'id': f"aap_{hash(pet_name + str(time.time()))}",
                'name': pet_name,
                'animal_type': self.extract_animal_type(info_text),
                'breed': self.extract_breed(info_text),
                'color': self.extract_color(info_text),
                'age': self.extract_age(info_text),
                'location': self.extract_location(info_text),
                'image_url': image_url,
                'source': 'Adopt-a-Pet',
                'source_url': pet_url,
                'description': self.clean_text(info_text)[:200] + '...' if len(info_text) > 200 else self.clean_text(info_text)
            }
            
        except Exception as e:
            return None
    
    def extract_animal_type(self, text):
        """Extract animal type from text"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['dog', 'puppy', 'canine']):
            return 'Dog'
        elif any(word in text_lower for word in ['cat', 'kitten', 'feline']):
            return 'Cat'
        elif 'bird' in text_lower:
            return 'Bird'
        elif 'rabbit' in text_lower:
            return 'Rabbit'
        return 'Unknown'
    
    def extract_breed(self, text):
        """Extract breed from text"""
        # Common dog breeds
        dog_breeds = ['labrador', 'golden retriever', 'german shepherd', 'bulldog', 'poodle', 
                     'beagle', 'rottweiler', 'husky', 'chihuahua', 'dachshund', 'border collie']
        
        # Common cat breeds  
        cat_breeds = ['persian', 'siamese', 'maine coon', 'ragdoll', 'british shorthair', 
                     'abyssinian', 'bengal', 'russian blue']
        
        text_lower = text.lower()
        
        for breed in dog_breeds + cat_breeds:
            if breed in text_lower:
                return breed.title()
        
        # Look for "mix" or "mixed"
        if 'mix' in text_lower:
            return 'Mixed Breed'
        
        return 'Unknown'
    
    def extract_color(self, text):
        """Extract color from text"""
        colors = ['black', 'white', 'brown', 'golden', 'gray', 'orange', 'tabby', 
                 'calico', 'tortoiseshell', 'cream', 'red', 'blue', 'silver']
        
        text_lower = text.lower()
        for color in colors:
            if color in text_lower:
                return color.title()
        
        return 'Unknown'
    
    def extract_age(self, text):
        """Extract age from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['puppy', 'kitten', 'young']):
            return 'Young'
        elif any(word in text_lower for word in ['senior', 'old', 'elderly']):
            return 'Senior'
        elif 'adult' in text_lower:
            return 'Adult'
        
        # Look for specific age patterns
        age_patterns = [
            r'(\d+)\s*(?:year|yr)s?\s*old',
            r'(\d+)\s*(?:month|mo)s?\s*old',
            r'age\s*:?\s*(\d+)'
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return f"{match.group(1)} years old"
        
        return 'Unknown'
    
    def extract_location(self, text):
        """Extract location from text"""
        # Look for city, state pattern
        location_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})'
        match = re.search(location_pattern, text)
        
        if match:
            return f"{match.group(1)}, {match.group(2)}"
        
        # Look for just state
        state_pattern = r'\b([A-Z]{2})\b'
        match = re.search(state_pattern, text)
        if match:
            return match.group(1)
        
        return 'Unknown'
    
    def clean_text(self, text):
        """Clean and format text"""
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', text).strip()
        # Remove special characters but keep basic punctuation
        cleaned = re.sub(r'[^\w\s.,!?-]', '', cleaned)
        return cleaned

# ==================== NEW WEB SEARCH VIEW ====================

@require_http_methods(["GET"])
def search_pets_web(request):
    """Search for pets by name on the web"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'web_pets': [], 'message': 'Query too short'})
    
    try:
        # Initialize web search
        web_search = SimplePetWebSearch()
        
        # Search for pets by name
        web_pets = web_search.search_pets_by_name(query, max_results=15)
        
        return JsonResponse({
            'web_pets': web_pets,
            'total_found': len(web_pets),
            'query': query,
            'message': f'Found {len(web_pets)} pets named "{query}" on the web' if web_pets else f'No pets named "{query}" found on the web'
        })
        
    except Exception as e:
        return JsonResponse({
            'web_pets': [],
            'error': str(e),
            'message': 'Error searching web for pets'
        })

# ==================== EXISTING NLP SEARCH VIEWS ====================

def search_results(request):
    """
    Enhanced search view with NLP processing for pet adoption listings
    """
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'relevance')
    
    # Initialize variables
    adoption_listings = []
    entities = None
    suggestions = []
    active_filters = []
    
    if query:
        # Perform NLP-enhanced search
        adoption_listings, entities = perform_smart_search(query, PendingPetForAdoption)
        
        # Only show approved and pending pets in search results
        adoption_listings = adoption_listings.filter(adoption_status__in=['approved', 'pending'])
        
        # Generate suggestions for improving the search
        suggestions = get_search_suggestions(query)
        
        # Build user-friendly filter descriptions
        if entities:
            active_filters = build_search_filters(entities)
        
        # Apply sorting
        if sort_by == 'recent':
            adoption_listings = adoption_listings.order_by('-created_at')
        elif sort_by == 'relevance':
            # You can implement custom relevance scoring here
            # For now, we'll order by creation date
            adoption_listings = adoption_listings.order_by('-created_at')
        elif sort_by == 'name':
            adoption_listings = adoption_listings.order_by('name')
            
    else:
        # Show all approved and pending pets when no query
        adoption_listings = PendingPetForAdoption.objects.filter(
            adoption_status__in=['approved', 'pending']
        ).order_by('-created_at')
    
    # Prepare context for template
    context = {
        'query': query,
        'adoption_listings': adoption_listings,
        'pets': [],  # Keep this for template compatibility
        'entities': entities,  # Pass entities for debugging/display
        'suggestions': suggestions,
        'active_filters': active_filters,
        'sort_by': sort_by,
        'total_results': adoption_listings.count(),
    }
    
    return render(request, 'search_results.html', context)

@require_http_methods(["GET"])
def search_suggestions_api(request):
    """
    API endpoint for real-time search suggestions (AJAX)
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    try:
        # Get suggestions from NLP processor
        suggestions = get_search_suggestions(query)
        
        # Analyze the current query
        entities = analyze_search_query(query)
        
        return JsonResponse({
            'suggestions': suggestions,
            'entities': entities,
            'query_analysis': {
                'pet_type': entities.get('pet_type'),
                'colors': entities.get('colors', []),
                'traits': entities.get('traits', []),
                'size': entities.get('size'),
                'age': entities.get('age'),
            }
        })
    except Exception as e:
        print(f"Error in search suggestions: {e}")
        return JsonResponse({'suggestions': [], 'error': str(e)})

@require_http_methods(["GET"])
def analyze_query_api(request):
    """
    API endpoint to analyze search queries and return entities
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'entities': {}})
    
    try:
        entities = analyze_search_query(query)
        active_filters = build_search_filters(entities)
        
        return JsonResponse({
            'entities': entities,
            'active_filters': active_filters,
            'query': query
        })
    except Exception as e:
        print(f"Error analyzing query: {e}")
        return JsonResponse({'entities': {}, 'error': str(e)})

@require_http_methods(["POST"])
@csrf_exempt
def smart_search_api(request):
    """
    API endpoint for smart search with filters
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        filters = data.get('filters', {})
        sort_by = data.get('sort', 'relevance')
        limit = int(data.get('limit', 20))
        
        if query:
            # Use NLP search
            results, entities = perform_smart_search(query, PendingPetForAdoption)
        else:
            # Start with all pets
            results = PendingPetForAdoption.objects.all()
            entities = None
        
        # Apply additional filters from the request
        if filters.get('pet_type'):
            results = results.filter(animal_type__icontains=filters['pet_type'])
        
        if filters.get('location'):
            results = results.filter(location__icontains=filters['location'])
        
        if filters.get('age_min'):
            results = results.filter(age__gte=filters['age_min'])
        
        if filters.get('age_max'):
            results = results.filter(age__lte=filters['age_max'])
        
        # Only show approved and pending pets
        results = results.filter(adoption_status__in=['approved', 'pending'])
        
        # Apply sorting
        if sort_by == 'recent':
            results = results.order_by('-created_at')
        elif sort_by == 'name':
            results = results.order_by('name')
        elif sort_by == 'age':
            results = results.order_by('age')
        
        # Limit results
        results = results[:limit]
        
        # Serialize results
        pets_data = []
        for pet in results:
            pet_data = {
                'id': pet.id,
                'name': pet.name,
                'animal_type': pet.animal_type,
                'breed': pet.breed,
                'age': pet.age,
                'gender': pet.gender,
                'color': pet.color,
                'location': pet.location,
                'description': pet.additional_details,
                'adoption_status': pet.adoption_status,
                'created_at': pet.created_at.isoformat() if pet.created_at else None,
            }
            
            # Handle image
            if pet.img:
                try:
                    pet_data['image_url'] = pet.img.url
                except:
                    pet_data['image_url'] = None
            else:
                pet_data['image_url'] = None
            
            # Handle owner info
            if pet.user:
                pet_data['owner'] = f"{pet.user.first_name} {pet.user.last_name}".strip() or pet.user.username
            else:
                pet_data['owner'] = pet.author if pet.author else 'Unknown'
            
            pets_data.append(pet_data)
        
        return JsonResponse({
            'pets': pets_data,
            'total': len(pets_data),
            'entities': entities,
            'query': query,
            'filters_applied': filters,
            'sort_by': sort_by
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ==================== EXISTING MAP VIEWS (UNCHANGED) ====================

@require_http_methods(["GET"])
def get_pets_locations(request):
    """
    API endpoint to get all pets with their locations for the map
    """
    try:
        print("🔍 API called: get_pets_locations")
        
        # Get all pets that have a location field and are approved or pending
        pets = PendingPetForAdoption.objects.filter(
            location__isnull=False,
            adoption_status__in=['approved', 'pending']  # Show only approved and pending pets
        ).exclude(location='')
        
        print(f"📊 Found {pets.count()} pets with location data")
        
        pets_data = []
        for pet in pets:
            try:
                # Get coordinates from location name
                coordinates = geocode_location(pet.location)
                
                if coordinates:
                    pet_data = {
                        'id': pet.id,
                        'name': pet.name,
                        'type': pet.animal_type.lower() if pet.animal_type else 'other',
                        'breed': pet.breed if pet.breed else 'Mixed',
                        'age': pet.age if pet.age else 'Unknown',
                        'lat': coordinates['lat'],
                        'lng': coordinates['lng'],
                        'description': pet.additional_details if pet.additional_details else '',
                        'location_name': pet.location,
                        'gender': pet.gender if pet.gender else 'Unknown',
                        'color': pet.color if pet.color else 'Unknown',
                        'adoption_status': pet.adoption_status,
                        'created_at': pet.created_at.isoformat() if pet.created_at else None,
                    }
                    
                    # Handle image URL
                    if pet.img:
                        try:
                            pet_data['image_url'] = pet.img.url
                        except:
                            pet_data['image_url'] = None
                    else:
                        pet_data['image_url'] = None
                    
                    # Handle owner contact (from the user who posted)
                    if pet.user:
                        pet_data['owner_contact'] = f"{pet.user.first_name} {pet.user.last_name}".strip()
                        if not pet_data['owner_contact']:
                            pet_data['owner_contact'] = pet.user.username
                        pet_data['owner_email'] = pet.user.email
                    else:
                        pet_data['owner_contact'] = pet.author if pet.author else 'Unknown'
                        pet_data['owner_email'] = ''
                    
                    pets_data.append(pet_data)
                    print(f"✅ Added pet: {pet_data['name']} at {pet_data['lat']}, {pet_data['lng']}")
                
                # Add delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error processing pet {pet.id}: {e}")
                continue
        
        print(f"🎯 Returning {len(pets_data)} pets")
        return JsonResponse(pets_data, safe=False)
        
    except Exception as e:
        print(f"🚨 API Error: {e}")
        return JsonResponse({'error': str(e), 'pets': []}, status=500)


def geocode_location(location_name):
    """
    Convert location name to coordinates using Nominatim geocoding
    """
    try:
        # Use Nominatim (OpenStreetMap) geocoding service
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': f"{location_name}, Philippines",
            'format': 'json',
            'limit': 1,
            'countrycodes': 'PH'
        }
        
        headers = {
            'User-Agent': 'PetAdoptionMap/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        if data and len(data) > 0:
            return {
                'lat': float(data[0]['lat']),
                'lng': float(data[0]['lon'])
            }
        else:
            # Fallback coordinates for common Philippine cities
            fallback_coords = get_fallback_coordinates(location_name)
            if fallback_coords:
                return fallback_coords
                
    except Exception as e:
        print(f"Geocoding error for {location_name}: {e}")
        fallback_coords = get_fallback_coordinates(location_name)
        if fallback_coords:
            return fallback_coords
    
    return None


def get_fallback_coordinates(location_name):
    """
    Fallback coordinates for common Philippine locations
    """
    fallback_locations = {
        'olongapo': {'lat': 14.8267, 'lng': 120.2823},
        'olongapo city': {'lat': 14.8267, 'lng': 120.2823},
        'subic': {'lat': 14.8833, 'lng': 120.2333},
        'manila': {'lat': 14.5995, 'lng': 120.9842},
        'quezon city': {'lat': 14.6760, 'lng': 121.0437},
        'makati': {'lat': 14.5547, 'lng': 121.0244},
        'pasig': {'lat': 14.5764, 'lng': 121.0851},
        'taguig': {'lat': 14.5176, 'lng': 121.0509},
        'baguio': {'lat': 16.4023, 'lng': 120.5960},
        'cebu': {'lat': 10.3157, 'lng': 123.8854},
        'davao': {'lat': 7.1907, 'lng': 125.4553},
        'santa rita': {'lat': 14.8267, 'lng': 120.2823},
        'sierra bullones': {'lat': 9.9167, 'lng': 124.2833},
    }
    
    location_lower = location_name.lower().strip()
    
    if location_lower in fallback_locations:
        return fallback_locations[location_lower]
    
    for key, coords in fallback_locations.items():
        if key in location_lower or location_lower in key:
            return coords
    
    return {'lat': 14.8267, 'lng': 120.2823}


@csrf_exempt
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
        
        pets_query = PendingPetForAdoption.objects.filter(
            location__isnull=False,
            adoption_status__in=['approved', 'pending']  # Show only approved and pending pets
        ).exclude(location='')
        
        if pet_type != 'all':
            pets_query = pets_query.filter(animal_type__icontains=pet_type)
        
        pets_data = []
        for pet in pets_query:
            try:
                coordinates = geocode_location(pet.location)
                
                if coordinates:
                    distance = calculate_distance(
                        center_lat, center_lng,
                        coordinates['lat'], coordinates['lng']
                    )
                    
                    if distance <= radius_km:
                        pet_data = {
                            'id': pet.id,
                            'name': pet.name,
                            'type': pet.animal_type.lower() if pet.animal_type else 'other',
                            'breed': pet.breed if pet.breed else 'Mixed',
                            'age': pet.age if pet.age else 'Unknown',
                            'lat': coordinates['lat'],
                            'lng': coordinates['lng'],
                            'description': pet.additional_details if pet.additional_details else '',
                            'distance': round(distance, 2),
                            'location_name': pet.location,
                            'gender': pet.gender if pet.gender else 'Unknown',
                            'color': pet.color if pet.color else 'Unknown',
                            'adoption_status': pet.adoption_status,
                        }
                        
                        if pet.img:
                            try:
                                pet_data['image_url'] = pet.img.url
                            except:
                                pet_data['image_url'] = None
                        else:
                            pet_data['image_url'] = None
                        
                        pets_data.append(pet_data)
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing pet {pet.id}: {e}")
                continue
        
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
    Calculate distance between two points using Haversine formula
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Earth radius in kilometers
    
    return c * r


def debug_model_fields(request):
    """Debug view to check your database structure"""
    try:
        model_fields = [f.name for f in PendingPetForAdoption._meta.fields]
        total_pets = PendingPetForAdoption.objects.count()
        pets_with_location = PendingPetForAdoption.objects.filter(
            location__isnull=False
        ).exclude(location='').count()
        approved_pending_pets = PendingPetForAdoption.objects.filter(adoption_status__in=['approved', 'pending']).count()
        
        sample_pet = None
        if total_pets > 0:
            first_pet = PendingPetForAdoption.objects.first()
            sample_pet = {
                'id': first_pet.id,
                'name': first_pet.name,
                'animal_type': first_pet.animal_type,
                'breed': first_pet.breed,
                'location': first_pet.location,
                'age': first_pet.age,
                'gender': first_pet.gender,
                'color': first_pet.color,
                'adoption_status': first_pet.adoption_status,
                'author': first_pet.author,
                'has_image': bool(first_pet.img),
                'user': first_pet.user.username if first_pet.user else None,
            }
        
        return JsonResponse({
            'model_name': PendingPetForAdoption.__name__,
            'table_name': PendingPetForAdoption._meta.db_table,
            'total_fields': len(model_fields),
            'all_fields': model_fields,
            'total_pets': total_pets,
            'pets_with_location': pets_with_location,
            'approved_pending_pets': approved_pending_pets,
            'sample_pet': sample_pet,
            'location_examples': list(PendingPetForAdoption.objects.exclude(location='').values_list('location', flat=True)[:5]),
            'animal_types': list(PendingPetForAdoption.objects.values_list('animal_type', flat=True).distinct()),
            'adoption_statuses': list(PendingPetForAdoption.objects.values_list('adoption_status', flat=True).distinct())
        }, indent=2)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
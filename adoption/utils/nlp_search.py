# adoption/utils/nlp_search.py
import re
from django.db.models import Q

# Try to import spacy, but don't fail if it's not installed
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except (ImportError, OSError):
    nlp = None
    print("spaCy not available. Install with: pip install spacy && python -m spacy download en_core_web_sm")

class PetSearchNLP:
    """
    Natural Language Processing for pet search queries
    """
    def __init__(self):
        # Define pet-specific entities and synonyms
        self.pet_types = {
            'dog': ['dog', 'puppy', 'canine', 'pup', 'doggy', 'lab', 'retriever', 
                   'shepherd', 'terrier', 'bulldog', 'poodle', 'beagle', 'husky'],
            'cat': ['cat', 'kitten', 'feline', 'kitty', 'persian', 'siamese', 
                   'tabby', 'calico', 'maine coon'],
            'bird': ['bird', 'parrot', 'cockatiel', 'budgie', 'canary', 'finch', 
                    'parakeet', 'lovebird'],
            'rabbit': ['rabbit', 'bunny', 'hare'],
            'hamster': ['hamster', 'gerbil', 'guinea pig', 'chinchilla']
        }
        
        self.colors = [
            'black', 'white', 'brown', 'gray', 'grey', 'orange', 'red', 
            'yellow', 'golden', 'tan', 'cream', 'silver', 'blue', 'blonde'
        ]
        
        self.sizes = {
            'small': ['small', 'tiny', 'little', 'mini', 'petite', 'compact'],
            'medium': ['medium', 'average', 'normal', 'moderate'],
            'large': ['large', 'big', 'huge', 'giant', 'massive', 'xl']
        }
        
        self.traits = {
            'friendly': ['friendly', 'social', 'outgoing', 'gregarious', 'sociable'],
            'playful': ['playful', 'energetic', 'active', 'lively', 'spirited'],
            'calm': ['calm', 'quiet', 'peaceful', 'gentle', 'docile', 'mellow'],
            'smart': ['smart', 'intelligent', 'clever', 'bright', 'trainable'],
            'loyal': ['loyal', 'devoted', 'faithful', 'dedicated'],
            'cuddly': ['cuddly', 'affectionate', 'loving', 'snuggly', 'sweet']
        }
        
        self.age_terms = {
            'young': ['young', 'baby', 'puppy', 'kitten', 'juvenile', 'infant'],
            'adult': ['adult', 'mature', 'grown', 'grown-up'],
            'senior': ['senior', 'old', 'elderly', 'aged', 'elder']
        }

    def extract_entities(self, query):
        """Extract structured information from search query"""
        if not query:
            return self._empty_entities()
            
        query_lower = query.lower().strip()
        entities = self._empty_entities()
        
        # Extract pet type
        entities['pet_type'] = self._extract_pet_type(query_lower)
        
        # Extract colors
        entities['colors'] = self._extract_colors(query_lower)
        
        # Extract size
        entities['size'] = self._extract_size(query_lower)
        
        # Extract traits
        entities['traits'] = self._extract_traits(query_lower)
        
        # Extract age
        entities['age'] = self._extract_age(query_lower)
        
        # Extract breed using spaCy if available
        entities['breed'] = self._extract_breed(query)
        
        # Extract remaining keywords
        entities['keywords'] = self._extract_keywords(query_lower, entities)
        
        return entities

    def _empty_entities(self):
        return {
            'pet_type': None,
            'colors': [],
            'size': None,
            'traits': [],
            'age': None,
            'breed': None,
            'keywords': []
        }

    def _extract_pet_type(self, query_lower):
        for pet_type, synonyms in self.pet_types.items():
            if any(synonym in query_lower for synonym in synonyms):
                return pet_type
        return None

    def _extract_colors(self, query_lower):
        return [color for color in self.colors if color in query_lower]

    def _extract_size(self, query_lower):
        for size, synonyms in self.sizes.items():
            if any(synonym in query_lower for synonym in synonyms):
                return size
        return None

    def _extract_traits(self, query_lower):
        traits = []
        for trait, synonyms in self.traits.items():
            if any(synonym in query_lower for synonym in synonyms):
                traits.append(trait)
        return traits

    def _extract_age(self, query_lower):
        for age, synonyms in self.age_terms.items():
            if any(synonym in query_lower for synonym in synonyms):
                return age
        return None

    def _extract_breed(self, query):
        if nlp:
            try:
                doc = nlp(query)
                for ent in doc.ents:
                    if ent.label_ in ['PERSON', 'ORG']:  # Might be breed names
                        return ent.text
            except:
                pass
        return None

    def _extract_keywords(self, query_lower, entities):
        words = re.findall(r'\b\w+\b', query_lower)
        used_words = set()
        
        # Collect all used words from entities
        for pet_type, synonyms in self.pet_types.items():
            used_words.update(synonyms)
        used_words.update(self.colors)
        for size, synonyms in self.sizes.items():
            used_words.update(synonyms)
        for trait, synonyms in self.traits.items():
            used_words.update(synonyms)
        for age, synonyms in self.age_terms.items():
            used_words.update(synonyms)
        
        # Common words to exclude
        stop_words = {'for', 'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'with'}
        used_words.update(stop_words)
        
        return [word for word in words if word not in used_words and len(word) > 2]

    def build_query(self, entities, model_class):
        """Build Django Q objects based on extracted entities"""
        q_objects = Q()
        
        # Search by pet type (using animal_type field)
        if entities['pet_type']:
            q_objects &= Q(animal_type__icontains=entities['pet_type'])
        
        # Search by colors
        for color in entities['colors']:
            q_objects &= Q(color__icontains=color)
        
        # Search by size (search in additional_details since no dedicated size field)
        if entities['size']:
            q_objects &= Q(additional_details__icontains=entities['size'])
        
        # Search by traits (using your actual model fields)
        for trait in entities['traits']:
            q_objects &= (
                Q(additional_details__icontains=trait) | 
                Q(breed__icontains=trait) |
                Q(animal_type__icontains=trait)
            )
        
        # Search by age
        if entities['age']:
            if entities['age'] == 'young':
                q_objects &= Q(age__lt=2)  # Less than 2 years
            elif entities['age'] == 'senior':
                q_objects &= Q(age__gt=7)  # More than 7 years
            else:
                q_objects &= Q(age__gte=2, age__lte=7)  # Adult
        
        # Search by breed
        if entities['breed']:
            q_objects &= Q(breed__icontains=entities['breed'])
        
        # Search by remaining keywords in multiple fields
        for keyword in entities['keywords']:
            q_objects &= (
                Q(name__icontains=keyword) |
                Q(additional_details__icontains=keyword) |
                Q(breed__icontains=keyword) |
                Q(animal_type__icontains=keyword) |
                Q(color__icontains=keyword)
            )
        
        return q_objects

    def get_search_suggestions(self, query):
        """Generate smart search suggestions"""
        if not query or len(query) < 2:
            return []
            
        suggestions = []
        query_lower = query.lower()
        
        # If they mentioned a trait but no pet type
        trait_mentioned = any(trait in query_lower for traits in self.traits.values() for trait in traits)
        pet_mentioned = any(pet in query_lower for pets in self.pet_types.values() for pet in pets)
        
        if trait_mentioned and not pet_mentioned:
            suggestions.extend([
                f"{query} dog",
                f"{query} cat"
            ])
        
        # If they mentioned a color but no pet type
        color_mentioned = any(color in query_lower for color in self.colors)
        if color_mentioned and not pet_mentioned:
            suggestions.extend([
                f"{query} puppy",
                f"{query} kitten"
            ])
        
        # If they only typed a pet type, suggest adding traits
        if pet_mentioned and not trait_mentioned and not color_mentioned:
            suggestions.extend([
                f"{query} friendly",
                f"{query} playful",
                f"{query} calm"
            ])
        
        return suggestions[:5]  # Limit to 5 suggestions
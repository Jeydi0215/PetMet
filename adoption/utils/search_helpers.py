# adoption/utils/search_helpers.py
from django.db.models import Q
from .nlp_search import PetSearchNLP

def perform_smart_search(query, model_class):
    """
    Helper function to perform NLP-enhanced search
    
    Args:
        query (str): The search query from user
        model_class: Django model class to search (e.g., AdoptionListing)
    
    Returns:
        tuple: (queryset, entities_dict)
    """
    if not query:
        return model_class.objects.all(), None
    
    nlp_processor = PetSearchNLP()
    entities = nlp_processor.extract_entities(query)
    
    # Check if we extracted meaningful entities
    has_entities = (
        entities['pet_type'] or 
        entities['colors'] or 
        entities['traits'] or 
        entities['size'] or
        entities['age'] or
        entities['breed'] or
        entities['keywords']
    )
    
    if has_entities:
        # Use NLP-enhanced search
        try:
            q_objects = nlp_processor.build_query(entities, model_class)
            results = model_class.objects.filter(q_objects).distinct()
        except Exception as e:
            # Fallback to simple search if NLP search fails
            print(f"NLP search failed: {e}")
            results = _simple_text_search(query, model_class)
    else:
        # Fallback to simple text search
        results = _simple_text_search(query, model_class)
    
    return results, entities

def _simple_text_search(query, model_class):
    """
    Fallback simple text search across common fields
    """
    return model_class.objects.filter(
        Q(name__icontains=query) |
        Q(additional_details__icontains=query) |
        Q(breed__icontains=query) |
        Q(animal_type__icontains=query) |
        Q(color__icontains=query)
    )

def get_search_suggestions(query):
    """
    Get search suggestions based on the current query
    
    Args:
        query (str): Current search query
    
    Returns:
        list: List of suggested search terms
    """
    if not query or len(query) < 2:
        return []
    
    nlp_processor = PetSearchNLP()
    return nlp_processor.get_search_suggestions(query)

def analyze_search_query(query):
    """
    Analyze a search query and return the extracted entities
    
    Args:
        query (str): Search query to analyze
    
    Returns:
        dict: Dictionary of extracted entities
    """
    if not query:
        return {}
    
    nlp_processor = PetSearchNLP()
    return nlp_processor.extract_entities(query)

def build_search_filters(entities):
    """
    Convert extracted entities into user-friendly filter descriptions
    
    Args:
        entities (dict): Entities extracted from search query
    
    Returns:
        list: List of filter descriptions
    """
    filters = []
    
    if entities.get('pet_type'):
        filters.append(f"Type: {entities['pet_type'].title()}")
    
    if entities.get('colors'):
        colors_str = ", ".join(entities['colors'])
        filters.append(f"Color: {colors_str.title()}")
    
    if entities.get('size'):
        filters.append(f"Size: {entities['size'].title()}")
    
    if entities.get('traits'):
        traits_str = ", ".join(entities['traits'])
        filters.append(f"Traits: {traits_str.title()}")
    
    if entities.get('age'):
        filters.append(f"Age: {entities['age'].title()}")
    
    if entities.get('breed'):
        filters.append(f"Breed: {entities['breed'].title()}")
    
    return filters
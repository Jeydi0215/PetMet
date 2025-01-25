from django import template
import calendar

register = template.Library()

@register.filter
def range_list(value):
    """Return a list of integers from 0 to value - 1."""
    return list(range(value))  # Convert to list

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary or return an empty list if the key doesn't exist."""
    return dictionary.get(key)  # Return an empty list if key is not found

@register.filter
def range_filter(value):
    """Return a range object for iteration."""
    return range(value)

@register.filter
def month_name(month_number):
    """Return the full month name for a given month number."""
    try:
        # Convert month_number to an integer
        month_number = int(month_number)
        if 1 <= month_number <= 12:
            return calendar.month_name[month_number]  # Returns full month name
    except (ValueError, TypeError):
        pass  # Handle cases where conversion to int fails
    return ""  # Return an empty string for invalid month numbers
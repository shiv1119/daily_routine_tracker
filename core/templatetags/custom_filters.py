from django import template
from datetime import date

register = template.Library()
@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if total == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_rank_color(rank):
    """Get color for rank"""
    colors = {
        'E': '#6c757d',
        'D': '#cd7f32',
        'C': '#28a745',
        'B': '#007bff',
        'A': '#6f42c1',
        'S': '#ff8c00'
    }
    return colors.get(rank, '#6c757d')

@register.filter
def get_rank_icon(rank):
    """Get icon for rank"""
    icons = {
        'E': 'fa-bug',
        'D': 'fa-shield-alt',
        'C': 'fa-crosshairs',
        'B': 'fa-bow-arrow',
        'A': 'fa-trophy',
        'S': 'fa-crown'
    }
    return icons.get(rank, 'fa-star')

@register.filter
def format_date(value):
    """Format date nicely"""
    if isinstance(value, date):
        return value.strftime('%b %d, %Y')
    return value

@register.filter
def truncate_words(value, arg):
    """Truncate text to specified number of words"""
    try:
        words = value.split()
        if len(words) > int(arg):
            return ' '.join(words[:int(arg)]) + '...'
    except:
        pass
    return value
    
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    if dictionary is None:
        return None
    try:
        return dictionary.get(key)
    except AttributeError:
        return None

@register.filter
def get_nested_item(dictionary, key1, key2=None):
    """Get nested item from dictionary"""
    if dictionary is None:
        return None
    if key2 is not None:
        # Handle two keys (category_id and date)
        first_level = dictionary.get(key1, {})
        if isinstance(first_level, dict):
            return first_level.get(key2)
        return None
    return dictionary.get(key1)
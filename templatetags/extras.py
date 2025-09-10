# results/templatetags/extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get a dictionary item by key in templates"""
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return None

# chargen/templatetags/form_tags.py
from django import template

register = template.Library() # YOU NEED THIS LINE

# Define the custom 'get_item' filter
@register.filter
def get_item(value, arg):
    """
    Returns the item from a dictionary-like object using a key (arg).
    Example: {{ form|get_item:"name" }}
    """
    try:
        return value[arg]
    except KeyError:
        return None

@register.filter # YOU NEED THIS DECORATOR
def as_hidden(bound_field):
    """ Renders a form field as a hidden input """
    if bound_field:
        try:
            # Ensure it looks like a BoundField before calling as_hidden
            if hasattr(bound_field, 'as_hidden'):
                 return bound_field.as_hidden()
        except Exception:
            # Handle cases where it might not be a valid field gracefully
            pass
    return '' # Return empty string if not a valid field or input is None
from django import template

register = template.Library()


@register.filter
def dict_key(d, key):
    """Accède à une clé d'un dictionnaire dans un template."""
    if isinstance(d, dict):
        return d.get(key, '')
    return ''

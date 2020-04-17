from django import template
import json

register = template.Library()


@register.filter
def to_jason(arg):
    return json.dumps(arg)

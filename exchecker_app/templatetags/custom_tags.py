from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='split_and_last')
@stringfilter
def split_and_last(str, delimiter=""):
    return str.split(delimiter)[-1]

@register.filter(name='range')
def range(n):
    n = int(n)
    return range(n)
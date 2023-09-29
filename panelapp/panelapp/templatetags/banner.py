from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("banner.html")
def banner():
    return {"message": settings.BANNER}

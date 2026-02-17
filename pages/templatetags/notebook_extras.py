from django import template

register = template.Library()

@register.filter
def ensure_list(value):
    """
    Your schema uses JSONField(default=list). This filter guards against
    accidental None/string values so templates don't explode.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    # allow comma-separated strings if they ever appear
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return []

@register.simple_tag
def querystring(request, **kwargs):
    """
    Preserve existing GET params while overriding a subset.
    Usage: ?{% querystring request page=2 %}
    """
    q = request.GET.copy()
    for k, v in kwargs.items():
        if v is None:
            q.pop(k, None)
        else:
            q[k] = str(v)
    return q.urlencode()

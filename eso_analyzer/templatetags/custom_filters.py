import os
from django import template


register = template.Library()

@register.filter(name="add_place_holder")
def add_place_holder(field, place_holder=None):
    if place_holder is None:
        return field
    else:
        field.field.widget.attrs.update({'placeholder': place_holder})
        return field


@register.filter(name='add_class')
def add_class(field, css_class=None):
    if css_class is None:
        return field
    else:
        existing_classes = field.field.widget.attrs.get('class', '')
        if existing_classes:
            if css_class not in existing_classes:
                field.field.widget.attrs['class'] = f'{existing_classes} {css_class}'
        else:
            field.field.widget.attrs['class'] = css_class
        return field


@register.filter
def filename(value):
    return os.path.basename(value.file.name)

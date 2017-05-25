# -*- coding: utf-8 -*-
from django.core.validators import _lazy_re_compile, RegexValidator
from django.db.models.fields import *  # NOQA
from django.db.models import fields
from django.utils.translation import ugettext as _
from ..forms import widgets

__all__ = fields.__all__ + ['CurrencyField', ]
del fields

slug_re = _lazy_re_compile(r'^(?=.*[-a-zA-Z_])[-a-zA-Z0-9_]+\Z')
validate_slug = RegexValidator(
    slug_re,
    _("Enter a valid 'slug' consisting of letters, numbers, underscores or "
      "hyphens, ensuring at least one character is not a number."),
    'invalid'
)


class SlugField(SlugField):
    """
    Custom SlugField ensures at least one non-number to allow for URLs to
    reliably discern slugs from pks.
    """

    default_validators = [validate_slug]


class CurrencyField(FloatField):

    def formfield(self, **kwargs):
        defaults = {
            'widget': widgets.CurrencyInput,
        }
        defaults.update(kwargs)
        return super(CurrencyField, self).formfield(**defaults)

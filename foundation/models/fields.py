# -*- coding: utf-8 -*-
from django.core.validators import _lazy_re_compile, RegexValidator
from django.db.models.fields import *  # NOQA
from django.utils.translation import ugettext as _


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

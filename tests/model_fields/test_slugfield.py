from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import BigS, UnicodeSlugField


class SlugFieldTests(TestCase):

    def test_slugfield_min_length(self):
        """
        SlugField empty not allowed.
        """
        self.assertRaises(ValidationError, BigS.objects.create, s='')

    def test_slugfield_not_numbers_only(self):
        """
        SlugField must have a non-number.
        """
        self.assertRaises(ValidationError, BigS.objects.create, s='123')

    def test_slugfield_max_length(self):
        """
        SlugField honors max_length.
        """
        bs = BigS.objects.create(s='slug' * 50)
        bs = BigS.objects.get(pk=bs.pk)
        self.assertEqual(bs.s, 'slug' * 50)

    def test_slugfield_unicode_max_length(self):
        """
        SlugField with allow_unicode=True honors max_length.
        """
        bs = UnicodeSlugField.objects.create(s='你好你好' * 50)
        bs = UnicodeSlugField.objects.get(pk=bs.pk)
        self.assertEqual(bs.s, '你好你好' * 50)

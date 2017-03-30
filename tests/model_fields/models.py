from foundation import models


class BigS(models.Model):
    s = models.SlugField(max_length=255)


class UnicodeSlugField(models.Model):
    s = models.SlugField(max_length=255, allow_unicode=True)

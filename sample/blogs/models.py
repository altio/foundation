# -*- coding: utf-8 -*-
from django.contrib.auth import models as auth_models
from django.template.defaultfilters import slugify
from django.utils import lorem_ipsum
from foundation import models


class User(models.ActiveSuperuserMixin, auth_models.AbstractUser):
    """ Treat as superusers only if is_superuser and "acting" flag set. """


class Blog(models.Model):

    owner = models.ForeignKey(
        User,
        related_name='blogs',
    )

    slug = models.SlugField(
        max_length=25,
        unique=True,
        editable=False,
    )

    title = models.CharField(max_length=200)

    @property
    def description(self):
        return '\n'.join(lorem_ipsum.paragraphs(3))

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)[0:25]
        super(Blog, self).save(*args, **kwargs)


class Post(models.Model):

    blog = models.ForeignKey(
        to=Blog,
        on_delete=models.CASCADE,
        related_name='blog_entries',
    )

    slug = models.SlugField(
        max_length=50,
        unique=True,
        editable=False,
    )

    title = models.CharField(max_length=200)
    body = models.TextField()
    publish = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)[0:50]
        super(Post, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Blog Entry"
        verbose_name_plural = "Blog Entries"
        ordering = ["-created"]

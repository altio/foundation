from django.contrib.admin import register, ModelAdmin, TabularInline
from django.contrib.auth import admin as auth_admin

from . import models


class PostInline(TabularInline):
    model = models.Post
    extra = 1


@register(models.Blog)
class BlogAdmin(ModelAdmin):
    inlines = [PostInline]
    list_display = ('owner', 'title', 'description')
    fields = ('owner', 'title')  # , 'description')


@register(models.User)
class UserAdmin(auth_admin.UserAdmin):
    pass
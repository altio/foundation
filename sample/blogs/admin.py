from django.contrib.admin import register, ModelAdmin, TabularInline

from . import models


class PostInline(TabularInline):
    model = models.Post
    extra = 1


@register(models.Blog)
class BlogAdmin(ModelAdmin):
    inlines = [PostInline]
    list_display = ('owner', 'title', 'description')
    fields = ('owner', 'title')  # , 'description')

# blog/admin.py
from django.contrib import admin

from blog.models import Category, Location, Post

admin.site.empty_value_display = 'Не задано'


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('is_published',)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')
    list_filter = ('is_published',)


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_published', 'pub_date')
    list_filter = ('is_published', 'category', 'author')
    search_fields = ('title', 'text')


# Регистрируем модели с настройками админки
admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Post, PostAdmin)

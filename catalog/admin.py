from django.contrib import admin

# Register your models here.

from .models import Author, Genre, Book, BookInstance, Language, Option

"""Minimal registration of Models.
admin.site.register(Book)
admin.site.register(Author)
admin.site.register(BookInstance)
admin.site.register(Genre)
admin.site.register(Language)
"""



admin.site.register(Option)



@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Administration object for Author models.
    Defines:
     - fields to be displayed in list view (list_display)
     - orders fields in detail view (fields),
       grouping the date fields horizontally
     - adds inline addition of books in author view (inlines)
    """
    list_display = ('first_card',
                    'second_card','bb')
    fields = ['first_card', 'second_card', 'bb']



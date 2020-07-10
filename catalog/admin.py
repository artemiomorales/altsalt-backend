from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, Listing, Image

class UserProfileAdmin(admin.ModelAdmin):
    pass
    # fieldsets = [
    #     (None,  {'fields': ['question_text']}),
    #     ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    # ]
    # inlines = [ChoiceInLine]
    # list_display = ('question_text', 'pub_date', 'was_published_recently')
    # list_filter = ['pub_date']
    # search_fields = ['question_text']


# class ImageInLine(admin.TabularInline):
#     model = Image


class ImageAdmin(admin.ModelAdmin):
    pass


class ListingAdmin(admin.ModelAdmin):
    # inlines = [ImageInLine]
    pass


admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Image, ImageAdmin)
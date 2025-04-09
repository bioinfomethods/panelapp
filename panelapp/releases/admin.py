from django.contrib import admin

from releases.models import Release


class ReleaseAdmin(admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Release, ReleaseAdmin)

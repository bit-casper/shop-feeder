from django.contrib import admin
from .models import Shop, Feed, SyncLog

admin.site.register(Shop)
admin.site.register(Feed)
admin.site.register(SyncLog)
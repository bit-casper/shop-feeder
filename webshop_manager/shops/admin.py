from django.contrib import admin
from .models import Client, Shop, Feed, SyncLog

admin.site.register(Client)
admin.site.register(Shop)
admin.site.register(Feed)
admin.site.register(SyncLog)
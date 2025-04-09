from django.contrib import admin
from .models import Client, Shop, Product, Feed, SyncLog

admin.site.register(Client)
admin.site.register(Shop)
admin.site.register(Product)
admin.site.register(Feed)
admin.site.register(SyncLog)
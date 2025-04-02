from rest_framework import serializers
from .models import Client, Shop, Feed



class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['client_name']

class FeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feed
        fields = ['id', 'source_type', 'feed_product_tag', 'sku_prefix', 'ftp_host', 'ftp_user', 'ftp_pass', 'url', 'file_pattern',
                  'format_type', 'mapping', 'last_sync', 'sync_status']

class ShopSerializer(serializers.ModelSerializer):
    feeds = FeedSerializer(many=True, read_only=True)

    class Meta:
        model = Shop
        fields = ['id', 'name', 'shop_type', 'api_endpoint', 'api_key', 'api_secret',
                  'is_active', 'sync_interval', 'feeds']
from django.db import models
from encrypted_model_fields.fields import EncryptedCharField

class Shop(models.Model):
    SHOP_TYPES = (
        ('shopify', 'Shopify'),
        ('woocommerce', 'WooCommerce'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=100, unique=True)
    shop_type = models.CharField(max_length=20, choices=SHOP_TYPES, default='other')
    api_endpoint = models.URLField()
    api_key = EncryptedCharField(max_length=255)
    api_secret = EncryptedCharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sync_interval = models.CharField(max_length=50, default='daily', help_text="e.g., hourly, daily")

    def __str__(self):
        return f"{self.name} ({self.shop_type})"

class Feed(models.Model):
    SOURCE_TYPES = (
        ('ftp', 'FTP'),
        ('url', 'URL'),
    )
    FORMAT_TYPES = (
        ('xml', 'XML'),
        ('csv', 'CSV'),
    )
    
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='feeds')
    source_type = models.CharField(max_length=10, choices=SOURCE_TYPES, default='ftp')
    ftp_host = models.CharField(max_length=100, blank=True, null=True)
    ftp_user = EncryptedCharField(max_length=100, blank=True, null=True)
    ftp_pass = EncryptedCharField(max_length=100, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    file_pattern = models.CharField(max_length=100, default='products.xml', help_text="e.g., products*.xml")
    format_type = models.CharField(max_length=10, choices=FORMAT_TYPES, default='xml')
    mapping = models.JSONField(default=dict, help_text="e.g., {'name': 'product_title', 'price': 'product_price'}")
    last_sync = models.DateTimeField(blank=True, null=True)
    sync_status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"{self.source_type.upper()} Feed for {self.shop.name}"
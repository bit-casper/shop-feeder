from django.db import models

class Shop(models.Model):
    SHOP_TYPES = (('shopify', 'Shopify'), ('uniconta', 'Uniconta'))
    shop_name = models.CharField(max_length=100)
    shop_type = models.CharField(max_length=20, choices=SHOP_TYPES)
    api_endpoint = models.URLField()
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255, null=True, blank=True)
    api_access_token = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sync_interval = models.PositiveIntegerField(default=1440)

    def __str__(self):
        return self.shop_name

class Feed(models.Model):
    SOURCE_TYPES = (('ftp', 'FTP'), ('url', 'URL'), ('local', 'LOCAL'))
    FORMAT_TYPES = (('xml', 'XML'),)
    shops = models.ManyToManyField(Shop, related_name='feeds')
    name = models.CharField(max_length=100, blank=True, null=True)
    source_type = models.CharField(max_length=10, choices=SOURCE_TYPES)
    source_path = models.CharField(max_length=30, default='test_xml.xml')
    ftp_host = models.CharField(max_length=255, null=True, blank=True)
    ftp_user = models.CharField(max_length=255, null=True, blank=True)
    ftp_pass = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    file_pattern = models.CharField(max_length=255, default='products.xml')
    format_type = models.CharField(max_length=10, choices=FORMAT_TYPES)
    mapping = models.JSONField(blank=True, null=True, default=dict)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return self.name or f"{self.url or self.ftp_host or self.source_path} ({self.get_source_type_display()})"

class SyncLog(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True)  # Made nullable
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    message = models.TextField()

    def __str__(self):
        return f"{self.feed} - {self.shop or 'No Shop'} - {self.timestamp}"
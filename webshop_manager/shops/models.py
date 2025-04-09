from django.db import models



class Client(models.Model):
    client_name = models.CharField(max_length=100, blank=False)

    def __str__(self):
        return self.client_name



class Product(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='products')
    is_main_product = models.BooleanField(default=False)
    product_name = models.CharField(max_length=250, default="")
    sku = models.CharField(max_length=100, default="")
    #uniconta_sku = models.CharField(max_length=100, default="")
    #woocommerce_sku = models.CharField(max_length=100, default="")
    shopify_product_id = models.CharField(max_length=100, default="")
    shopify_variant_id = models.CharField(max_length=100, default="")
    shopify_inventory_item_id = models.CharField(max_length=100, default="")
    last_known_price = models.CharField(max_length=100, default="")
    last_known_inventory = models.IntegerField(default=0)

    def __str__(self):
        return self.sku



class Shop(models.Model):
    SHOP_TYPES = (('shopify', 'Shopify'), ('uniconta', 'Uniconta'), ('custom', 'Custom'))
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='shops')
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
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='feeds')
    shops = models.ManyToManyField(Shop, related_name='feeds')
    name = models.CharField(max_length=100, blank=True, null=True)
    source_type = models.CharField(max_length=10, choices=SOURCE_TYPES)
    feed_product_tag = models.CharField(max_length=30, default='item')
    ftp_host = models.CharField(max_length=255, null=True, blank=True)
    ftp_user = models.CharField(max_length=255, null=True, blank=True)
    ftp_pass = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    file_pattern = models.CharField(max_length=255, default='products.xml')
    sku_prefix = models.CharField(max_length=10, default="", blank=True)
    format_type = models.CharField(max_length=10, choices=FORMAT_TYPES)
    mapping = models.JSONField(blank=True, null=True, default=dict)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return self.name or f"{self.url or self.ftp_host or self.file_pattern} ({self.get_source_type_display()})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure shops belong to the same client
        if self.shops.exists():
            invalid_shops = self.shops.exclude(client=self.client)
            if invalid_shops.exists():
                raise ValueError("All shops linked to a feed must belong to the same client.")

class SyncLog(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True)  # Made nullable
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    message = models.TextField()

    def __str__(self):
        return f"{self.feed} - {self.shop or 'No Shop'} - {self.timestamp}"
from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class Client(models.Model):
    client_name = models.CharField(max_length=100, blank=False, default="Client")
    product_count = models.IntegerField(default=0)  # Total products in shop
    last_batch_product_count = models.IntegerField(default=0)  # Total products synced
    last_updated = models.DateTimeField(null=True, blank=True)  # Last sync completion
    sync_in_progress = models.BooleanField(default=False)  # Sync status
    update_iteration_delay = models.IntegerField(default=300)  # Delay in seconds between batches
    update_batch_size = models.IntegerField(default=50)  # Products per batch

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
    
    def save(self, *args, **kwargs):
        if self.pk is None:  # New object, save everything as is
            super().save(*args, **kwargs)
        else:  # Existing object, apply custom logic
            try:
                original = Product.objects.get(pk=self.pk)  # Fetch the existing instance

                # Preserve immutable fields
                self.product_name = original.product_name
                self.sku = original.sku
                self.shopify_product_id = original.shopify_product_id
                self.shopify_variant_id = original.shopify_variant_id
                self.shopify_inventory_item_id = original.shopify_inventory_item_id
                self.client = original.client  # Preserve client relationship
                self.is_main_product = original.is_main_product

                # Only update mutable fields if they’ve changed
                price_changed = str(original.last_known_price) != str(self.last_known_price)
                inventory_changed = original.last_known_inventory != self.last_known_inventory

                if not (price_changed or inventory_changed):
                    return  # No changes to price or inventory, skip the save

                # If we reach here, at least one has changed, so proceed with save
                super().save(*args, **kwargs)
            except ObjectDoesNotExist:
                # If for some reason the object doesn’t exist, save as new
                super().save(*args, **kwargs)



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
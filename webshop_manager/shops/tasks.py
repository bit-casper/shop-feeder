from celery import shared_task
import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from .models import Feed, Shop, SyncLog
import shopify

@shared_task
def sync_feed_to_shops(feed_id):
    feed = Feed.objects.get(id=feed_id)
    feed.sync_status = 'running'
    feed.save()

    try:
        # Fetch feed data
        if feed.source_type == 'url':
            response = requests.get(feed.url, timeout=10)
            response.raise_for_status()
            xml_data = response.content
        else:
            # Placeholder for FTP (implement later if needed)
            raise NotImplementedError("FTP sync not implemented yet")

        # Parse XML
        tree = ET.fromstring(xml_data)
        root = tree  # Assuming root is the iterable element

        # Process each item in the feed
        for item in root.findall('.//item'):  # Adjust based on XML structure
            mapped_data = {}
            for xml_key, shop_key in feed.mapping.items():
                element = item.find(xml_key)
                mapped_data[shop_key] = element.text if element is not None else 'N/A'

            # Sync to each subscribed shop
            for shop in feed.shops.all():
                if shop.shop_type == 'shopify':
                    sync_to_shopify(shop, mapped_data, feed)
                elif shop.shop_type == 'uniconta':
                    sync_to_uniconta(shop, mapped_data, feed)

        feed.sync_status = 'success'
        feed.last_sync = timezone.now()
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='success', message='Sync completed successfully')

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise

def sync_to_shopify(shop, data, feed):
    # Shopify API setup
    shopify.ShopifyResource.set_site(shop.api_endpoint)
    shopify.ShopifyResource.set_user(shop.api_key)
    shopify.ShopifyResource.set_password(shop.api_secret)

    # Create or update product (simplified example)
    product = shopify.Product()
    product.title = data.get('title', 'Unnamed Product')
    product.body_html = data.get('description', '')
    product.variants = [{
        'price': data.get('price', '0.00'),
        'sku': data.get('sku', '')
    }]
    success = product.save()

    if success:
        SyncLog.objects.create(feed=feed, shop=shop, status='success', message=f"Product {product.id} synced to Shopify")
    else:
        SyncLog.objects.create(feed=feed, shop=shop, status='failed', message="Failed to sync product to Shopify")

def sync_to_uniconta(shop, data, feed):
    # Uniconta API (simplified REST example - adjust to actual API)
    headers = {
        'Authorization': f"Bearer {shop.api_key}",
        'Content-Type': 'application/json'
    }
    payload = {
        'ItemNumber': data.get('sku', ''),
        'Name': data.get('title', 'Unnamed Product'),
        'Description': data.get('description', ''),
        'SalesPrice': float(data.get('price', '0.00'))
    }
    response = requests.post(f"{shop.api_endpoint}/api/items", json=payload, headers=headers)
    response.raise_for_status()

    SyncLog.objects.create(feed=feed, shop=shop, status='success', message="Product synced to Uniconta")
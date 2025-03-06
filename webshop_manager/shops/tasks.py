from celery import shared_task
import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from .models import Feed, Shop, SyncLog

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
        elif feed.source_type == 'ftp':
            # Placeholder for FTP
            raise NotImplementedError("FTP sync not implemented yet")
        elif feed.source_type == 'local':
            xml_data = ET.parse(feed.source_path)
        else:
            raise NotImplementedError("Unknown source")

        # Parse XML
        tree = ET.fromstring(xml_data)
        root = tree  # Assuming root is the iterable element

        # Process each item in the feed
        for item in root.findall('.//to'):  # Adjust based on XML structure
            mapped_data = {}
            for xml_key, shop_key in feed.mapping.items():
                element = item.find(xml_key)
                mapped_data[shop_key] = element.text if element is not None else 'N/A'

            # Sync to each subscribed shop
            for shop in feed.shops.all():
                if shop.shop_type == 'Shopify':
                    sync_to_shopify(shop, mapped_data, feed)
                elif shop.shop_type == 'Uniconta':
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

# def sync_to_shopify(shop, data, feed):
#     # Shopify REST API (using API key and password for basic auth)
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f"Basic {shop.api_key}:{shop.api_secret}".encode('utf-8').decode('ascii')  # Simplified; use base64 in production
#     }
#     payload = {
#         'product': {
#             'title': data.get('title', 'Unnamed Product'),
#             'body_html': data.get('description', ''),
#             'variants': [{
#                 'price': data.get('price', '0.00'),
#                 'sku': data.get('sku', '')
#             }]
#         }
#     }
#     # Shopify endpoint: adjust path based on API version (e.g., /admin/api/2023-10/products.json)
#     url = f"{shop.api_endpoint}/products.json"
#     response = requests.post(url, json=payload, headers=headers)
#     response.raise_for_status()

#     product_id = response.json()['product']['id']
#     SyncLog.objects.create(feed=feed, shop=shop, status='success', message=f"Product {product_id} synced to Shopify")

def sync_to_shopify(shop, data, feed):
    headers = {
        'X-Shopify-Access-Token': shop.api_key,  # Use api_key as token
        'Content-Type': 'application/json'
    }
    payload = {
        'product': {
            'title': data.get('title', 'Unnamed Product'),
            'body_html': data.get('description', ''),
            'variants': [{
                'price': data.get('price', '0.00'),
                'sku': data.get('sku', '')
            }]
        }
    }
    url = f"{shop.api_endpoint}/products.json"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    product_id = response.json()['product']['id']
    SyncLog.objects.create(feed=feed, shop=shop, status='success', message=f"Product {product_id} synced to Shopify")

def sync_to_uniconta(shop, data, feed):
    # Uniconta REST API (placeholder - adjust to actual API)
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
    # Adjust endpoint based on Uniconta API docs
    url = f"{shop.api_endpoint}/api/items"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    SyncLog.objects.create(feed=feed, shop=shop, status='success', message="Product synced to Uniconta")
from celery import shared_task
import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from .models import Feed, Shop, SyncLog
import os

# @shared_task
# def sync_feed_to_shops(feed_id):
#     feed = Feed.objects.get(id=feed_id)
#     feed.sync_status = 'running'
#     feed.save()

#     try:
#         # Fetch feed data
#         if feed.source_type == 'url':
#             response = requests.get(feed.url, timeout=10)
#             response.raise_for_status()
#             xml_data = response.content
#         elif feed.source_type == 'ftp':
#             # Placeholder for FTP
#             raise NotImplementedError("FTP sync not implemented yet")
#         elif feed.source_type == 'local':
#             xml_data = ET.tostring(ET.parse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_xml.xml")).getroot(), encoding='utf-8')
#             # xml_string = ET.tostring(xml_data.getroot(), encoding='utf-8')
#             # xml_data = ET.parse("/text_xml.xml")
#         else:
#             raise NotImplementedError("Unknown source")

#         # Parse XML
#         tree = ET.fromstring(xml_data)
#         root = tree  # Assuming root is the iterable element

#         # Process each item in the feed
#         for item in root.findall('.//item'):  # Adjust based on XML structure
#             mapped_data = {}
#             for xml_key, shop_key in feed.mapping.items():
#                 element = item.find(xml_key)
#                 mapped_data[shop_key] = element.text if element is not None else 'N/A'

#             # Sync to each subscribed shop
#             for shop in feed.shops.all():
#                 if shop.shop_type == 'shopify':
#                     sync_to_shopify(shop, mapped_data, feed)
#                 elif shop.shop_type == 'uniconta':
#                     sync_to_uniconta(shop, mapped_data, feed)

#         feed.sync_status = 'success'
#         feed.last_sync = timezone.now()
#         feed.save()
#         SyncLog.objects.create(feed=feed, shop=None, status='success', message='Sync completed successfully')

#     except Exception as e:
#         feed.sync_status = 'failed'
#         feed.save()
#         SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
#         raise

# @shared_task
# def sync_feed_to_shops(feed_id):
#     feed = Feed.objects.get(id=feed_id)
#     feed.sync_status = 'running'
#     feed.save()

#     try:
#         # Fetch feed data
#         if feed.source_type == 'url':
#             response = requests.get(feed.url)
#             response.raise_for_status()
#             xml_data = response.content
#         elif feed.source_type == 'ftp':
#             return JsonResponse({'error': 'FTP not yet implemented'}, status=400)
#         elif feed.source_type == 'local':
#             # Get the absolute path to the file based on views.py location
#             base_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of views.py
#             file_path = os.path.join(base_dir, feed.file_pattern)   # Full path to the file
#             tree = ET.parse(file_path)                             # Parse the file
#             xml_data = tree.getroot()                              # Get the root Element

#         # If source_type is 'url', xml_data is still bytes, so parse it
#         if feed.source_type != 'local':
#             tree = ET.fromstring(xml_data)

        
#         #for item in tree.findall('.//' + feed.feed_product_tag):
#         mapped_data = {}
        
#         for xml_key, shop_key in feed.mapping.items():
#             element = xml_data.find(xml_key)
#             value = element.text if element is not None else 'N/A'
#             mapped_data[shop_key] = value

#         # Sync to each subscribed shop
#         for shop in feed.shops.all():
#             if shop.shop_type == 'shopify':
#                 sync_to_shopify(shop, mapped_data, feed)
#             elif shop.shop_type == 'uniconta':
#                 sync_to_uniconta(shop, mapped_data, feed)

#         feed.sync_status = 'success'
#         feed.last_sync = timezone.now()
#         feed.save()
#         SyncLog.objects.create(feed=feed, shop=None, status='success', message='Sync completed successfully')

#     except Exception as e:
#         feed.sync_status = 'failed'
#         feed.save()
#         SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
#         raise



@shared_task
def sync_feed_to_shops(feed_id):
    feed = Feed.objects.get(id=feed_id)
    feed.sync_status = 'running'
    feed.save()

    try:
        # Fetch feed data
        if feed.source_type == 'url':
            response = requests.get(feed.url)
            response.raise_for_status()
            xml_data = response.content
        elif feed.source_type == 'ftp':
            return JsonResponse({'error': 'FTP not yet implemented'}, status=400)
        elif feed.source_type == 'local':
            # Get the absolute path to the file based on views.py location
            base_dir = os.path.dirname(os.path.abspath(__file__))  # Directory of views.py
            file_path = os.path.join(base_dir, feed.file_pattern)   # Full path to the file
            tree = ET.parse(file_path)                             # Parse the file
            xml_data = tree.getroot()                              # Get the root Element

        # If source_type is 'url', xml_data is still bytes, so parse it
        if feed.source_type != 'local':
            tree = ET.fromstring(xml_data)
            xml_data = tree

        
        # Parse XML
        #tree = ET.fromstring(xml_data)
        root = xml_data  # Assuming root is the iterable element

        # Process each item in the feed
        # for item in root.findall('.//item'):
        # for item in root.findall('.//' + feed.feed_product_tag):  # Adjust based on XML structure
        #     mapped_data = {}
        #     for xml_key, shop_key in feed.mapping.items():
        #         element = item.find(xml_key)
        #         mapped_data[shop_key] = element.text if element is not None else 'N/A'


        for item in root.findall('.//' + feed.feed_product_tag):  # './/Product'
            mapped_data = {}

            for xml_key, shop_key in feed.mapping.items():
                # element = root.find(f".//{xml_key}") if '/' in xml_key else item.find(xml_key)
                # mapped_data[shop_key] = element.text if element is not None else 'N/A'
                element = item.find(xml_key)
                value = element.text if element is not None else 'N/A'
                mapped_data[shop_key] = value

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
    import logging
    logger = logging.getLogger(__name__)
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": shop.api_access_token
    }
    payload = {
        'product': {
            'title': data.get('title', 'Unnamed Product'),
            'body_html': data.get('body_html', ''),
            'variants': [{
                'price': str(data.get('price', '0.00')),
                'sku': data.get('sku', ''),
                # 'inventory_quantity': data.get('inventory_quantity', '0')  # Add for completeness
            }]
        }
    }
    url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/products.json"
    logger.info(f"Syncing to Shopify - Shop: {shop.shop_name}, URL: {url}, Payload: {payload}, Headers: {headers}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"Shopify Response - Status: {response.status_code}, Body: {response.text}")
        response.raise_for_status()
        product_id = response.json()['product']['id']
        SyncLog.objects.create(feed=feed, shop=shop, status='success', message=f"Product {product_id} synced")
    except Exception as e:
        logger.error(f"Shopify Sync Failed - Error: {str(e)}, Response: {response.text if 'response' in locals() else 'No response'}")
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise


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
        'SalesPrice': data.get('price', '0.00')
    }
    # Adjust endpoint based on Uniconta API docs
    url = f"{shop.api_endpoint}/api/items"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    SyncLog.objects.create(feed=feed, shop=shop, status='success', message="Product synced to Uniconta")
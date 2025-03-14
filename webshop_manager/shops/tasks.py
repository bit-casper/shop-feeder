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
    # headers = {
    #     'X-Shopify-Access-Token': shop.api_key,  # Use api_key as token
    #     'Content-Type': 'application/json'
    # }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": shop.api_access_token
    }
    payload = {
        'product': {
            'title': data.get('title', 'Unnamed Product'),
            'body_html': data.get('description', ''),
            'variants': [{
                'price': str(data.get('price', '0.00')),
                'sku': data.get('sku', '')
            }]
        }
    }
    # payload = {
    #     "product": {
    #         'title': data.get('title', 'Unnamed Product'),
    #         'body_html': data.get('description', ''),
    #         "images": data.get("images", None),
    #         #"product_type": product.category,
    #         "vendor": data.get("vendor", None),
    #         #"metafields_global_description_tag": product.description,
    #         #"status": status,
    #         "variants": [
    #             {
    #                 'price': data.get('price', '0.00'),
    #                 'sku': data.get('sku', ''),
    #                 "barcode": data.get("barcode", None),
    #                 #"compare_at_price": product.compare_at_price,
    #                 #"tracked": True,
    #                 #"inventory_item_id": 1,  # to be gotten by get inventory endpoint
    #                 "inventory_quantity": data.get("inventory_quantity", None),
    #                 "weight": data.get("weight", None),
    #                 #"weight_unit": "lb"
    #             }
    #         ]
    #     }
    # }
    #endpoint https://caspers-test.myshopify.com/admin/api/2022-07
    #url = f"{shop.api_endpoint}/products.json"
    #url = "https://" + api_key + ":" +password + "@" + store + ".myshopify.com/admin/api/2021-04/products.json"
    url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/products.json"
    # url = "https://" + shop.api_key + ":" + shop.api_access_token + "@" + shop.shop_name + ".myshopify.com/admin/api/2021-04/products.json"
    #https://9101cbada402d38b6d5db33b72ed64e8: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@caspers-test.myshopify.com/admin/api/2021-04/products.json
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        product_id = response.json()['product']['id']
        SyncLog.objects.create(feed=feed, shop=shop, status='success', message=f"Product {product_id} synced to Shopify")
    except Exception as e:
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
        'SalesPrice': float(data.get('price', '0.00'))
    }
    # Adjust endpoint based on Uniconta API docs
    url = f"{shop.api_endpoint}/api/items"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    SyncLog.objects.create(feed=feed, shop=shop, status='success', message="Product synced to Uniconta")
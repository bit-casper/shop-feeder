from celery import shared_task
import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from .models import Feed, Shop, SyncLog
import os
from .utils import getAllProducts, DownloadNewFiles
import json
import time
import math



@shared_task
def sync_feed_to_shops(feed_id):
    feed = Feed.objects.get(id=feed_id)
    feed.sync_status = 'running'
    feed.save()

    mapped_data = []  # Initialize as a list to hold all products

    try:
        # Fetch feed data
        if feed.source_type == 'url':
            response = requests.get(feed.url)
            response.raise_for_status()
            xml_data = response.content
        elif feed.source_type == 'ftp':
            xml_data = DownloadNewFiles(feed)
            #return JsonResponse({'error': 'FTP not yet implemented'}, status=400)
        elif feed.source_type == 'local':
            base_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_dir, feed.file_pattern)
            tree = ET.parse(file_path)
            xml_data = tree.getroot()

        if feed.source_type != 'local':
            tree = ET.fromstring(xml_data)
            xml_data = tree

        root = xml_data

        # Map all products from XML into mapped_data
        for item in root.findall('.//' + feed.feed_product_tag):  # './/InventTable'
            product_data = {}  # Dictionary for a single product
            for xml_key, shop_key in feed.mapping.items():
                element = item.find(xml_key)
                value = element.text if element is not None else 'N/A'
                product_data[shop_key] = value
            mapped_data.append(product_data)  # Add this product to the list

        # Now process all shops with the complete mapped_data
        for shop in feed.shops.all():
            if shop.shop_type == 'shopify':
                # sync_to_shopify(shop, mapped_data, feed)
                sync_inventory_to_shopify(shop, mapped_data, feed)
                # create_to_shopify(shop, mapped_data, feed)
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

    # Fetch shopify data
    getAllProducts(shop)

    # Compare feeds and shopify and build a list of products to update
    changed_products = []
    with open('data.json', 'r') as f:
        shop_data = json.load(f)
        for ishop in shop_data:
            for variant in ishop['variants']:  # Loop through all variants
                for ifeed in data:
                    if variant['sku'] == ifeed['sku']:
                        if variant['price'] != ifeed['price']:
                            changed_products.append({
                                "variant": {
                                    # "id": ishop['id'],
                                    "id": variant['id'],
                                    "price": str(ifeed['price'])
                                }
                            })

    # Build headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": shop.api_access_token
    }

    # Execute the shopify update call
    try:
        # Loop over all changed products, build a payload for each of them and push it into shopify
        for i in changed_products:

            # Delay to enforce api rate limit
            time.sleep(520/1000)

            # Build payload
            payload = i

            # Build url and send request for updating variant
            url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/variants/" + str(i["variant"]["id"]) + ".json"
            response = requests.put(url, json=payload, headers=headers)
            response.raise_for_status()

            # Log the result
            data = response.json()
            sku = str(variant['sku'])
            product_id = str(data['variant']['product_id'])
            variant_id = str(data['variant']['id'])
            inventory_item_id = str(data['variant']['inventory_item_id'])
            created_string = "Updated variant with " + "\n" + "SKU: " + sku + "\n"  + "product_id: " + product_id + "\n" + "variant_id: " + variant_id + "\n" + "inventory_item_id: " + inventory_item_id
            SyncLog.objects.create(feed=feed, shop=shop, status='success', message=created_string)

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise




def sync_inventory_to_shopify(shop, data, feed):

    # Fetch shopify data
    getAllProducts(shop)

    # Compare feeds and shopify and build a list of products to update
    changed_products = []
    with open('data.json', 'r') as f:
        shop_data = json.load(f)
        for ishop in shop_data:
            for variant in ishop['variants']:  # Loop through all variants
                for ifeed in data:
                    if variant['sku'] == ifeed['sku']:
                        if math.floor(float(variant['inventory_quantity'])) != math.floor(float(ifeed['inventory_quantity'])):
                            changed_products.append({
                                "sku": variant['sku'], # For logging
                                "old_inventory": variant['inventory_quantity'], # For logging
                                #"location_id": 61527654518, # physical location
                                "location_id": 61796188278, # remote location
                                "inventory_item_id": variant['inventory_item_id'],
                                "available": ifeed['inventory_quantity']
                            })

    # Build headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": shop.api_access_token
    }

    # Execute the shopify update call
    try:
        # Loop over all changed products, build a payload for each of them and push it into shopify
        for i in changed_products:

            # Delay to enforce api rate limit
            time.sleep(520/1000)

            # Build payload with only the required fields
            payload = {
                "location_id": i['location_id'],
                "inventory_item_id": i['inventory_item_id'],
                "available": math.floor(float(i['available']))
            }

            # Build url and send request for updating inventory
            url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/inventory_levels/set.json"
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            # Log the result
            data = response.json()
            sku = str(i['sku'])
            inventory_id = str(data['inventory_level']['inventory_item_id'])
            new_inventory = str(data['inventory_level']['available'])
            old_inventory = str(i['old_inventory'])
            # created_string = "Updated inventory of SKU: " + sku + ", inventory_item_id: " + inventory_id + " - old: " + old_inventory + " / new: " + new_inventory
            created_string = "Updated inventory of" + "\n" + "SKU: " + sku + "\n" + "inventory_item_id: " + inventory_id + "\n" + "old: " + old_inventory + "\n" + "new: " + new_inventory
            SyncLog.objects.create(feed=feed, shop=shop, status='success', message=created_string)

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise



def create_to_shopify(shop, data, feed):

    # Build headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": shop.api_access_token
    }

    # Execute the shopify update call
    try:
        # Loop over all changed products, build a payload for each of them and push it into shopify
        for i in data:

            # Delay to enforce api rate limit
            time.sleep(520/1000)

            # Build payload
            payload = {
                "product": {
                    "title": i["title"],
                    "body_html": i["body_html"],
                    #"images": i["images"],
                    #"product_type": i["title"],
                    #"vendor": i["title"],
                    # "metafields_global_description_tag": product.description,
                    #"status": i["title"],
                    "variants": [

                        {
                            "barcode": i["barcode"],
                            "price": i["price"],
                            #"compare_at_price": i["compare_at_price"],
                            "tracked": True,
                            # "inventory_item_id": 1,  # to be gotten by get inventory endpoint
                            #"inventory_quantity": i["inventory_quantity"],
                            "sku": i["sku"],
                            "weight": i["weight"],
                            "weight_unit": "kg"
                        }
                    ]
                }
            }
            
            # Build url and send request for creating product
            url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/products.json"
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            # Log the result
            data = response.json()
            sku = str(i['sku'])
            product_id = str(data['product']['id'])
            inventory_id = str(data['product']['variants'][0]['inventory_item_id'])
            created_string = "Created product with" + "\n" + "SKU: " + sku + "\n" + "product_id: " + product_id + "\n" + "inventory_item_id: " + inventory_id
            SyncLog.objects.create(feed=feed, shop=shop, status='success', message=created_string)

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
        'SalesPrice': data.get('price', '0.00')
    }
    # Adjust endpoint based on Uniconta API docs
    url = f"{shop.api_endpoint}/api/items"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    SyncLog.objects.create(feed=feed, shop=shop, status='success', message="Product synced to Uniconta")

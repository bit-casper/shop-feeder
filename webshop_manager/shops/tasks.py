from celery import shared_task
import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from .models import Feed, Shop, SyncLog
import os
from .utils import DownloadNewFiles
from .integrations.shopify import *
from .integrations.uniconta import *

# WE NEED TO CREATE A CUSTOM TASK FOR SEJLERBIXEN
# Here's the flow for each update cycle:
#   - Incrementally sync Shopify products into our DB.
#   - Download, compare, update and create from feed to our DB. Newly create are marked with 'new = true'
#   - Compare and update changed prices and inventories from DB to Shopify.
#   - Test all products marked 'new = true' in DB, against Uniconta. If they don't exist, create them.


# This function reads products from Shopify and creates a super shallow mirror of them in our database.
@shared_task
def sync_shopify_products_to_db(shop_id, last_cursor=None, processed_products=0):
    shop = Shop.objects.get(id=shop_id)
    client = shop.client

    # Only block new manual syncs if sync is already in progress
    if last_cursor is None and client.sync_in_progress:
        return {"shop_id": shop_id, "error": "Sync already in progress"}

    # Mark sync as in progress on first call (manual start)
    if last_cursor is None:
        client.sync_in_progress = True
        client.save()

    url = f"https://{shop.shop_name}.myshopify.com/admin/api/2025-04/graphql.json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": shop.api_access_token
    }

    query = """
    query ($first: Int!, $after: String) {
        products(first: $first, after: $after) {
            edges {
                node {
                    id
                    title
                    variants(first: 1) {
                        edges {
                            node {
                                id
                                sku
                                price
                                inventoryQuantity
                                inventoryItem {
                                    id
                                }
                            }
                        }
                    }
                }
                cursor
            }
            pageInfo {
                hasNextPage
            }
        }
    }
    """
    variables = {"first": client.update_batch_size, "after": last_cursor}

    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    data = response.json().get("data", {}).get("products", {})

    batch_product_count = 0
    for edge in data.get("edges", []):
        product_node = edge["node"]
        variant = product_node["variants"]["edges"][0]["node"] if product_node["variants"]["edges"] else {}
        sku = variant.get("sku")
        if not sku:
            continue

        # Extract Shopify IDs and other fields
        shopify_product_id = product_node["id"].split('/')[-1]
        shopify_variant_id = variant["id"].split('/')[-1] if variant else ""
        shopify_inventory_item_id = variant["inventoryItem"]["id"].split('/')[-1] if variant.get("inventoryItem") else ""
        inventory_quantity = variant.get("inventoryQuantity", 0)  # Default to 0 if not available

        # Check if product exists by SKU and update all fields
        product, created = Product.objects.get_or_create(
            sku=sku,
            defaults={
                "client": client,
                "product_name": product_node["title"],
                "last_known_price": variant.get("price", "0.00"),
                "shopify_product_id": shopify_product_id,
                "shopify_variant_id": shopify_variant_id,
                "shopify_inventory_item_id": shopify_inventory_item_id,
                "last_known_inventory": inventory_quantity,
            },
        )
        if not created:
            # Update all fields; model save() will handle restrictions
            product.product_name = product_node["title"]
            product.last_known_price = variant.get("price", "0.00")
            product.shopify_product_id = shopify_product_id
            product.shopify_variant_id = shopify_variant_id
            product.shopify_inventory_item_id = shopify_inventory_item_id
            product.last_known_inventory = inventory_quantity
            product.save()

        batch_product_count += 1

    total_processed = processed_products + batch_product_count

    page_info = data.get("pageInfo", {})
    if page_info.get("hasNextPage"):
        new_cursor = data["edges"][-1]["cursor"]
        sync_shopify_products_to_db.apply_async(
            args=(shop_id, new_cursor, total_processed),
            countdown=client.update_iteration_delay
        )
    else:
        client.product_count = Product.objects.filter(client=client).count()
        client.last_batch_product_count = total_processed
        client.last_updated = timezone.now()
        client.sync_in_progress = False
        client.save()

    return {
        "shop_id": shop_id,
        "last_cursor": new_cursor if page_info.get("hasNextPage") else None,
        "processed_products": total_processed
    }





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

        # Initialize as a list to hold all products
        mapped_data = []

        # Map all products from XML into mapped_data using the mapping in the feed model
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
                # sync_inventory_to_shopify(shop, mapped_data, feed)
                # sync_to_shopify_graphql(shop, mapped_data, feed)
                create_to_shopify(shop, mapped_data, feed)
            elif shop.shop_type == 'uniconta':
                sync_to_uniconta(shop, mapped_data, feed)
            elif shop.shop_type == 'custom':
                # We need to fetch shopify data and compare feed and shopify to find new products, then feed the new products into the uniconta function
                # Use either getAllProducts() or getAllProducts_GraphQL()
                # But we need access to the Shopify AND Uniconta credentials on this custom shop.
                # We first need to build the client model solution, then we should be able to use client->shops->shop
                #initialize_uniconta_custom_sync(shop, mapped_data, feed)
                sync_uniconta_to_db(shop, mapped_data, feed)

        feed.sync_status = 'success'
        feed.last_sync = timezone.now()
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='success', message='Sync completed successfully')

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise



@shared_task
def sync_shop_to_db(shop_id):
    shop = Shop.objects.get(id=shop_id)
    # shop.sync_status = 'running'
    # shop.save()

    try:
        # Fetch feed data
        if shop.shop_type == 'shopify':
            print("Syncing Shopify")
            sync_shopify_to_db(shop)
            
        elif shop.shop_type == 'uniconta':
            print("Syncing Uniconta")
            sync_uniconta_to_db(shop)
        #     xml_data = DownloadNewFiles(feed)
        #     #return JsonResponse({'error': 'FTP not yet implemented'}, status=400)
        # elif shop.shop_type == 'custom':
        #     base_dir = os.path.dirname(os.path.abspath(__file__))
        #     file_path = os.path.join(base_dir, feed.file_pattern)
        #     tree = ET.parse(file_path)
        #     xml_data = tree.getroot()

        print("success")
        # feed.sync_status = 'success'
        # feed.last_sync = timezone.now()
        # feed.save()
        # SyncLog.objects.create(feed=feed, shop=None, status='success', message='Sync completed successfully')

    except Exception as e:
        print("failed")
        # feed.sync_status = 'failed'
        # feed.save()
        # SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise
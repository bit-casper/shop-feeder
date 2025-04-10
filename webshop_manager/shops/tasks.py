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

@shared_task
def sync_shopify_products_to_db(shop_id, last_cursor=None):
    # Get the Shopify shop
    shop = Shop.objects.get(id=shop_id)
    client = shop.client

    # Shopify GraphQL endpoint
    url = f"https://{shop.shop_name}.myshopify.com/admin/api/2025-04/graphql.json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": shop.api_access_token
    }

    # GraphQL query with pagination
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
                                sku
                                price
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
    variables = {"first": 50, "after": last_cursor}

    # Make the request
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    data = response.json().get("data", {}).get("products", {})

    # Process each product
    for edge in data.get("edges", []):
        product_node = edge["node"]
        variant = product_node["variants"]["edges"][0]["node"] if product_node["variants"]["edges"] else {}
        sku = variant.get("sku")
        if not sku:
            continue  # Skip if no SKU

        # Check if product exists by SKU
        product, created = Product.objects.get_or_create(
            sku=sku,
            defaults={
                "client": client,
                "product_name": product_node["title"],
                "last_known_price": variant.get("price", "0.00"),
            },
        )
        if not created:
            # Optionally update existing product
            product.product_name = product_node["title"]
            product.last_known_price = variant.get("price", "0.00")
            product.save()

    # Check if there’s more to fetch
    page_info = data.get("pageInfo", {})
    if page_info.get("hasNextPage"):
        new_cursor = data["edges"][-1]["cursor"]
        # Schedule the next batch
        sync_shopify_products_to_db.delay(shop_id, new_cursor)

    return {"shop_id": shop_id, "last_cursor": new_cursor if page_info.get("hasNextPage") else None}






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
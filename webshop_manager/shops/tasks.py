from celery import shared_task
import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from .models import Feed, Shop, SyncLog
import os
from .utils import DownloadNewFiles
from .integrations.shopify import *
from .integrations.uniconta import *



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
                initialize_uniconta_custom_sync(shop, mapped_data, feed)

        feed.sync_status = 'success'
        feed.last_sync = timezone.now()
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='success', message='Sync completed successfully')

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise
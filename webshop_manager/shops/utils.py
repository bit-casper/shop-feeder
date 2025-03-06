import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from .models import Feed, SyncLog
import logging

logger = logging.getLogger(__name__)

def fetch_shopify_products(shop):
    headers = {'X-Shopify-Access-Token': shop.api_key, 'Content-Type': 'application/json'}
    url = f"{shop.api_endpoint}/products.json"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return {p['variants'][0]['sku']: p for p in response.json()['products']}

def sync_new_products_to_uniconta(shop, new_products):
    headers = {'Content-Type': 'application/json'}
    auth = (shop.api_key, shop.api_secret or '')
    for sku, data in new_products.items():
        payload = {
            'ItemNumber': sku,
            'Name': f"Product {sku}",
            'Price': data['price'],
            'Stock': data['stock'],
            'Webshop': True,
        }
        response = requests.post(f"{shop.api_endpoint}/items", json=payload, auth=auth)
        response.raise_for_status()
        logger.info(f"Added {sku} to Uniconta for shop {shop.id}")

def sync_feed(feed):
    logger.info(f"Starting sync for feed {feed.id}")
    try:
        # Fetch supplier feed once
        if feed.source_type == 'url':
            response = requests.get(feed.url)
            response.raise_for_status()
            xml_data = response.content
        # Add FTP logic if needed...
        elif feed.source_type == 'local':
            xml_data = ET.parse("test_xml.xml")
        tree = ET.fromstring(xml_data)
        supplier_products = {}
        for item in tree.findall('.//product'):  # Adjust XPath
            sku = item.find(feed.mapping['sku']).text
            supplier_products[sku] = {
                'price': float(item.find(feed.mapping['price']).text),
                'stock': int(item.find(feed.mapping['stock']).text),
            }

        # Process for each subscribed shop
        for shop in feed.shops.all():
            if shop.shop_type == 'shopify':
                shopify_products = fetch_shopify_products(shop)
                updates = []
                for sku, supplier_data in supplier_products.items():
                    if sku in shopify_products:
                        variant = shopify_products[sku]['variants'][0]
                        if (variant['price'] != str(supplier_data['price']) or
                            variant['inventory_quantity'] != supplier_data['stock']):
                            updates.append({
                                'id': variant['id'],
                                'price': supplier_data['price'],
                                'inventory_quantity': supplier_data['stock'],
                            })
                if updates:
                    headers = {'X-Shopify-Access-Token': shop.api_key, 'Content-Type': 'application/json'}
                    for update in updates:
                        url = f"{shop.api_endpoint}/variants/{update['id']}.json"
                        payload = {'variant': update}
                        response = requests.put(url, json=payload, headers=headers)
                        response.raise_for_status()
                        SyncLog.objects.create(feed=feed, shop=shop, status='success', message=f"Updated SKU {update['id']}")
                else:
                    SyncLog.objects.create(feed=feed, shop=shop, status='success', message="No updates needed")

            elif shop.shop_type == 'uniconta':
                shopify_shop = feed.shops.filter(shop_type='shopify').first()
                if shopify_shop:
                    shopify_products = fetch_shopify_products(shopify_shop)
                    new_products = {sku: data for sku, data in supplier_products.items() if sku not in shopify_products}
                    sync_new_products_to_uniconta(shop, new_products)
                    SyncLog.objects.create(feed=feed, shop=shop, status='success', message=f"Added {len(new_products)} new products")

        feed.last_sync = timezone.now()
        feed.sync_status = 'success'
        feed.save()
    except Exception as e:
        feed.last_sync = timezone.now()
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=shop, status='failed', message=str(e))
        logger.error(f"Feed {feed.id} sync failed: {str(e)}")
        raise
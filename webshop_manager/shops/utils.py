import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from .models import Feed, SyncLog
import json
import time
# import logging

# logger = logging.getLogger(__name__)

# def fetch_shopify_products(shop):
#     headers = {'X-Shopify-Access-Token': shop.api_key, 'Content-Type': 'application/json'}
#     url = f"{shop.api_endpoint}/products.json"
#     response = requests.get(url, headers=headers)
#     response.raise_for_status()
#     return {p['variants'][0]['sku']: p for p in response.json()['products']}

# def sync_new_products_to_uniconta(shop, new_products):
#     headers = {'Content-Type': 'application/json'}
#     auth = (shop.api_key, shop.api_secret or '')
#     for sku, data in new_products.items():
#         payload = {
#             'ItemNumber': sku,
#             'Name': f"Product {sku}",
#             'Price': data['price'],
#             'Stock': data['stock'],
#             'Webshop': True,
#         }
#         response = requests.post(f"{shop.api_endpoint}/items", json=payload, auth=auth)
#         response.raise_for_status()
        # logger.info(f"Added {sku} to Uniconta for shop {shop.id}")

# def sync_feed(feed):
#     # logger.info(f"Starting sync for feed {feed.id}")
#     try:
#         # Fetch supplier feed once
#         if feed.source_type == 'url':
#             response = requests.get(feed.url)
#             response.raise_for_status()
#             xml_data = response.content
#         # Add FTP logic if needed...
#         elif feed.source_type == 'local':
#             xml_data = ET.parse(ET.parse(feed.source_path))
#         tree = ET.fromstring(xml_data)
#         supplier_products = {}
#         for item in tree.findall('.//product'):  # Adjust XPath
#             sku = item.find(feed.mapping['sku']).text
#             supplier_products[sku] = {
#                 'price': float(item.find(feed.mapping['price']).text),
#                 'stock': int(item.find(feed.mapping['stock']).text),
#             }

#         # Process for each subscribed shop
#         for shop in feed.shops.all():
#             if shop.shop_type == 'shopify':
#                 shopify_products = fetch_shopify_products(shop)
#                 updates = []
#                 for sku, supplier_data in supplier_products.items():
#                     if sku in shopify_products:
#                         variant = shopify_products[sku]['variants'][0]
#                         if (variant['price'] != str(supplier_data['price']) or
#                             variant['inventory_quantity'] != supplier_data['stock']):
#                             updates.append({
#                                 'id': variant['id'],
#                                 'price': supplier_data['price'],
#                                 'inventory_quantity': supplier_data['stock'],
#                             })
#                 if updates:
#                     headers = {'X-Shopify-Access-Token': shop.api_key, 'Content-Type': 'application/json'}
#                     for update in updates:
#                         url = f"{shop.api_endpoint}/variants/{update['id']}.json"
#                         payload = {'variant': update}
#                         response = requests.put(url, json=payload, headers=headers)
#                         response.raise_for_status()
#                         SyncLog.objects.create(feed=feed, shop=shop, status='success', message=f"Updated SKU {update['id']}")
#                 else:
#                     SyncLog.objects.create(feed=feed, shop=shop, status='success', message="No updates needed")

#             elif shop.shop_type == 'uniconta':
#                 shopify_shop = feed.shops.filter(shop_type='shopify').first()
#                 if shopify_shop:
#                     shopify_products = fetch_shopify_products(shopify_shop)
#                     new_products = {sku: data for sku, data in supplier_products.items() if sku not in shopify_products}
#                     sync_new_products_to_uniconta(shop, new_products)
#                     SyncLog.objects.create(feed=feed, shop=shop, status='success', message=f"Added {len(new_products)} new products")

#         feed.last_sync = timezone.now()
#         feed.sync_status = 'success'
#         feed.save()
#     except Exception as e:
#         feed.last_sync = timezone.now()
#         feed.sync_status = 'failed'
#         feed.save()
#         SyncLog.objects.create(feed=feed, shop=shop, status='failed', message=str(e))
#         # logger.error(f"Feed {feed.id} sync failed: {str(e)}")
#         raise





# index = 0
#product_list = []


# def getAllProducts(shop):  # get all shopify products and save them into a json file
#     url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/products.json"
#     product_list_url = url + "?fields=id,variants&limit=200"

#     print("Getting all shopify products ....")
#     getProducts(shop, product_list_url)
#     with open('data.json', 'w') as f:
#         json.dump(product_list, f)
#     # return product_list
#     print("Shopify products List size : "+str(len(product_list)))

def getAllProducts(shop):  # get all shopify products and save them into a json file
    url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/products.json"
    product_list_url = url + "?fields=id,variants&limit=200"

    print("Getting all shopify products ....")
    product_list = getProducts(shop, product_list_url)
    with open('data.json', 'w') as f:
        json.dump(product_list, f)
    # return product_list
    print("Shopify products List size : "+str(len(product_list)))



def getProducts(shop, url, last_product_list = None):  # get shopify products
    #global index
    if last_product_list == None:
        final_product_list = []
    else:
        final_product_list = last_product_list

    index = 0
    index = index+1
    print("page : "+str(index))

    time.sleep(501/1000)
    headers = {"Accept": "application/json",
               "Content-Type": "application/json",
               "X-Shopify-Access-Token": shop.api_access_token}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        products = data['products']

        for p in products:
            # product_list.append(p)
            final_product_list.append(p)

        if "Link" in r.headers:
            if "rel=\"next\"" in r.headers['Link']:
                next = ''
                urls = findUrlInString(r.headers['Link'])
                if len(urls) == 1:
                    next = urls[0]
                else:
                    next = urls[1]
                getProducts(next, last_product_list=final_product_list)

        return final_product_list
    except requests.exceptions.Timeout as e:
        print(e)
        time.sleep(2)
        getProducts(url)
    # Tell the user their URL was bad and try a different one
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        raise SystemExit(e)



def getInventoryItem(shop, inventory_id):
    time.sleep(520/1000)

    # url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/products.json"
    inventory_url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/inventory_items/"
    url = inventory_url + str(inventory_id) + ".json"

    headers = {"Accept": "application/json",
               "Content-Type": "application/json",
               "X-Shopify-Access-Token": shop.api_access_token}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if r.status_code == 200:
            return data['inventory_item']
        else:
            return None
    except requests.exceptions.Timeout as e:
        print(e, flush=True)
    # Tell the user their URL was bad and try a different one
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        raise SystemExit(e)



def updateInventoryItem(shop, inventory_data):
    time.sleep(520/1000)
    inventory_url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/inventory_items/"
    url = inventory_url + str(inventory_data['id']) + ".json"

    payload = {
        "inventory_item": inventory_data
    }

    headers = {"Accept": "application/json",
               "Content-Type": "application/json",
               "X-Shopify-Access-Token": shop.api_access_token}

    try:
        r = requests.put(url, json=payload, headers=headers, timeout=10)
        data = r.json()
        if r.status_code == 200:
            return data['inventory_item']['id']
        else:
            inventory_string = "Inventory not updated, inventory_id : " + \
                str(inventory_data['id'])
            print(inventory_string, flush=True)
            return None
    except requests.exceptions.Timeout as e:
        print(e, flush=True)
    # Tell the user their URL was bad and try a different one
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        raise SystemExit(e)
    


# def pushProduct(shop, call, api_product, product: Product):
#     time.sleep(520/1000)
#     images = []

#     if len(product.pictures) > 0:
#         for img in product.pictures:
#             images.append({'src': img})

#     status = "active"

#     payload = {
#         "product": {
#             "title": product.title,
#             "body_html": product.description,
#             "images": images,
#             "product_type": product.category,
#             "vendor": product.brandName,
#             # "metafields_global_description_tag": product.description,
#             "status": status,
#             "variants": [

#                 {
#                     "barcode": product.barcode,
#                     "price": product.price,
#                     "compare_at_price": product.compare_at_price,
#                     "tracked": True,
#                     # "inventory_item_id": 1,  # to be gotten by get inventory endpoint
#                     "inventory_quantity": product.quantity,
#                     "sku": product.sku,
#                     "weight": product.weight,
#                     "weight_unit": "lb"
#                 }
#             ]
#         }
#     }

#     headers = {"Accept": "application/json",
#                "Content-Type": "application/json",
#                "X-Shopify-Access-Token": shop.api_access_token}

#     try:
#         r = ""
#         if call == "create":
#             r = requests.post(api_product, json=payload,
#                               headers=headers, timeout=10)
#         else:
#             r = requests.put(api_product, json=payload,
#                              headers=headers, timeout=10)
#         data = r.json()
#         if "errors" in data.keys():
#             print(data, flush=True)
#         if r.status_code == 201 or (call == "update" and r.status_code == 200):
#             product_id = data['product']['id']
#             inventory_id = data['product']['variants'][0]['inventory_item_id']

#             created_string = " product with id : " + \
#                 str(product_id) + " : "+call+"d , SKU : "+product.sku

#             print(created_string, flush=True)

#             inventory_data = {
#                 "id": inventory_id,
#                 "cost": product.netPrice
#             }

#             if call == "update":
#                 inventory_data = getInventoryItem(inventory_id)
#                 if inventory_data is None:
#                     inventory_data = {
#                         "id": inventory_id,
#                         "cost": product.netPrice
#                     }
#                     inventory_data['id'] = inventory_id
#                 inventory_data['cost'] = product.netPrice

#             updateInventoryItem(inventory_data)

#         return r.status_code
#     except requests.exceptions.Timeout as e:
#         print(e, flush=True)
#         return None

#     # Tell the user their URL was bad and try a different one
#     except requests.exceptions.RequestException as e:
#         # catastrophic error. bail.
#         raise SystemExit(e)



def findUrlInString(string):
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]
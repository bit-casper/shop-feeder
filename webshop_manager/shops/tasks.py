from celery import shared_task
import requests
import xml.etree.ElementTree as ET
from django.utils import timezone
from .models import Feed, Shop, SyncLog
import os
import time


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
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        product_id = response.json()['product']['id']
        SyncLog.objects.create(feed=feed, shop=shop, status='success', message=f"Product {product_id} synced")
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








# import json
# product_list = []


# def getAllProducts(shop):  # get all shopify products and save them into a json file
#     url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/products.json"
#     product_list_url = url + "?fields=id,variants&limit=200"

#     print("Getting all shopify products ....")
#     getProducts(product_list_url)
#     with open('data.json', 'w') as f:
#         json.dump(product_list, f)
#     print("Shopify products List size : "+str(len(product_list)))






# def getProducts(shop, url):  # get shopify products
#     global index
#     index = index+1
#     print("page : "+str(index))

#     time.sleep(501/1000)
#     headers = {"Accept": "application/json",
#                "Content-Type": "application/json",
#                "X-Shopify-Access-Token": shop.api_access_token}
#     try:
#         r = requests.get(url, headers=headers, timeout=10)
#         data = r.json()
#         products = data['products']

#         for p in products:
#             product_list.append(p)

#         if "rel=\"next\"" in r.headers['Link']:
#             next = ''
#             urls = findUrlInString(r.headers['Link'])
#             if len(urls) == 1:
#                 next = urls[0]
#             else:
#                 next = urls[1]
#             getProducts(next)

#     except requests.exceptions.Timeout as e:
#         print(e)
#         time.sleep(2)
#         getProducts(url)
#     # Tell the user their URL was bad and try a different one
#     except requests.exceptions.RequestException as e:
#         # catastrophic error. bail.
#         raise SystemExit(e)







# def getInventoryItem(shop, inventory_id):
#     time.sleep(520/1000)

#     # url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/products.json"
#     inventory_url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/inventory_items/"
#     url = inventory_url + str(inventory_id) + ".json"

#     headers = {"Accept": "application/json",
#                "Content-Type": "application/json",
#                "X-Shopify-Access-Token": shop.api_access_token}

#     try:
#         r = requests.get(url, headers=headers, timeout=10)
#         data = r.json()
#         if r.status_code == 200:
#             return data['inventory_item']
#         else:
#             return None
#     except requests.exceptions.Timeout as e:
#         print(e, flush=True)
#     # Tell the user their URL was bad and try a different one
#     except requests.exceptions.RequestException as e:
#         # catastrophic error. bail.
#         raise SystemExit(e)




# def updateInventoryItem(shop, inventory_data):
#     time.sleep(520/1000)
#     inventory_url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/inventory_items/"
#     url = inventory_url + str(inventory_data['id']) + ".json"

#     payload = {
#         "inventory_item": inventory_data
#     }

#     headers = {"Accept": "application/json",
#                "Content-Type": "application/json",
#                "X-Shopify-Access-Token": shop.api_access_token}

#     try:
#         r = requests.put(url, json=payload, headers=headers, timeout=10)
#         data = r.json()
#         if r.status_code == 200:
#             return data['inventory_item']['id']
#         else:
#             inventory_string = "Inventory not updated, inventory_id : " + \
#                 str(inventory_data['id'])
#             print(inventory_string, flush=True)
#             return None
#     except requests.exceptions.Timeout as e:
#         print(e, flush=True)
#     # Tell the user their URL was bad and try a different one
#     except requests.exceptions.RequestException as e:
#         # catastrophic error. bail.
#         raise SystemExit(e)
    




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





# def findUrlInString(string):
#     # findall() has been used
#     # with valid conditions for urls in string
#     regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
#     url = re.findall(regex, string)
#     return [x[0] for x in url]
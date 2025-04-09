import requests
from ..models import Feed, SyncLog
import json
import time
import math
from ..utils import *


# Sync shopify to local DB
def sync_shopify_to_db(shop):

    # Fetch shopify data
    getAllProducts(shop) # creates data.json

    # Compare shopify to our database and create products in database if they do not already exist
    #changed_products = []

    with open('data.json', 'r') as f:
        shop_data = json.load(f)
        for ishop in shop_data: # 
            for variant in ishop['variants']:  # Loop through all variants
                sku = variant["sku"]
                product_id = variant["product_id"]
                variant_id = variant["id"]
                product_name = variant["title"]
                price = variant["price"]
                #inventory = variant[""]
                inventory_item_id = variant["inventory_item_id"]


    # for ifeed in mapped_data:
    #     if "MainItemSKU" in ifeed:
    #         is_main_product = True
    #     else:
    #         is_main_product = False

    #     if "sku" in ifeed:
    #         sku = ifeed['sku']
    #     if "price" in ifeed:
    #         price = ifeed["price"]
        


def sync_to_shopify(shop, mapped_data, feed):

    # Fetch shopify data
    getAllProducts(shop) # creates data.json

    # Compare feeds and shopify and build a list of products to update
    changed_products = []
    with open('data.json', 'r') as f:
        shop_data = json.load(f)
        for ishop in shop_data:
            for variant in ishop['variants']:  # Loop through all variants
                for ifeed in mapped_data:
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
            response_data = response.json()
            sku = str(variant['sku'])
            product_id = str(response_data['variant']['product_id'])
            variant_id = str(response_data['variant']['id'])
            inventory_item_id = str(response_data['variant']['inventory_item_id'])
            created_string = "Updated variant with " + "\n" + "SKU: " + sku + "\n"  + "product_id: " + product_id + "\n" + "variant_id: " + variant_id + "\n" + "inventory_item_id: " + inventory_item_id
            SyncLog.objects.create(feed=feed, shop=shop, status='success', message=created_string)

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise



def sync_inventory_to_shopify(shop, mapped_data, feed):

    # Fetch shopify data
    getAllProducts(shop)

    # Compare feeds and shopify and build a list of products to update
    changed_products = []
    with open('data.json', 'r') as f:
        shop_data = json.load(f)
        for ishop in shop_data:
            for variant in ishop['variants']:  # Loop through all variants
                for ifeed in mapped_data:
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
            response_data = response.json()
            sku = str(i['sku'])
            inventory_id = str(response_data['inventory_level']['inventory_item_id'])
            new_inventory = str(response_data['inventory_level']['available'])
            old_inventory = str(i['old_inventory'])
            # created_string = "Updated inventory of SKU: " + sku + ", inventory_item_id: " + inventory_id + " - old: " + old_inventory + " / new: " + new_inventory
            created_string = "Updated inventory of" + "\n" + "SKU: " + sku + "\n" + "inventory_item_id: " + inventory_id + "\n" + "old: " + old_inventory + "\n" + "new: " + new_inventory
            SyncLog.objects.create(feed=feed, shop=shop, status='success', message=created_string)

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise



def create_to_shopify(shop, mapped_data, feed):

    # Build headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": shop.api_access_token
    }

    # Execute the shopify update call
    try:
        # Loop over all changed products, build a payload for each of them and push it into shopify
        for i in mapped_data:

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
            response_data = response.json()
            sku = str(i['sku'])
            product_id = str(response_data['product']['id'])
            inventory_id = str(response_data['product']['variants'][0]['inventory_item_id'])
            created_string = "Created product with" + "\n" + "SKU: " + sku + "\n" + "product_id: " + product_id + "\n" + "inventory_item_id: " + inventory_id
            SyncLog.objects.create(feed=feed, shop=shop, status='success', message=created_string)

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise



def sync_to_shopify_graphql(shop, mapped_data, feed):

    # Fetch shopify data
    getAllProducts_GraphQL(shop)

    # Compare feeds and shopify and build a list of products to update
    changed_products = []
    with open('data.json', 'r') as f:
        shop_data = json.load(f)
        for ishop in shop_data:
            for variant in ishop['variants']:  # Loop through all variants
                for ifeed in mapped_data:
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
            #payload = i
            # GraphQL query
            # products_query = '''
            #     query {
            #         products(first: 5) {
            #             edges {
            #                 node {
            #                     id
            #                     handle
            #                 }
            #             }
            #             pageInfo {
            #                 hasNextPage
            #             }
            #         }
            #     }
            # '''

            products_query = '''
                query {
                    products(first: 10, after: "eyJsYXN0X2lkIjoyMDk5NTY0MiwibGFzdF92YWx1ZSI6IjIwOTk1NjQyIn0=") {
                        edges {
                            node {
                                id
                                title
                                handle
                            }
                            cursor
                        }
                        pageInfo {
                            hasNextPage
                        }
                    }
                }
            '''

            # Build url and send request for updating variant
            # GraphQL url
            url = f"https://{shop.shop_name}.myshopify.com/admin/api/2025-01/graphql.json"

            # GraphQL request
            response = requests.post(url, json=products_query, headers=headers)
            response.raise_for_status()

            # Log the result
            response_data = response.json()
            sku = str(variant['sku'])
            product_id = str(response_data['variant']['product_id'])
            variant_id = str(response_data['variant']['id'])
            inventory_item_id = str(response_data['variant']['inventory_item_id'])
            created_string = "Updated variant with " + "\n" + "SKU: " + sku + "\n"  + "product_id: " + product_id + "\n" + "variant_id: " + variant_id + "\n" + "inventory_item_id: " + inventory_item_id
            SyncLog.objects.create(feed=feed, shop=shop, status='success', message=created_string)

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise











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

# get all shopify products and save them into a json file
def getAllProducts(shop):  
    url = f"https://{shop.shop_name}.myshopify.com/admin/api/2022-07/products.json"
    product_list_url = url + "?fields=id,variants&limit=200"

    print("Getting all shopify products ....")
    product_list = getProducts(shop, product_list_url)
    with open('data.json', 'w') as f:
        json.dump(product_list, f)
    # return product_list
    print("Shopify products List size : "+str(len(product_list)))



def getAllProducts_GraphQL(shop):  # get all shopify products and save them into a json file
    url = f"https://{shop.shop_name}.myshopify.com/admin/api/2025-01/graphql.json"
    # product_list_url = url + "?fields=id,variants&limit=200"

    print("Getting all shopify products ....")
    product_list = getProducts_GraphQL(shop, url)
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



def getProducts_GraphQL(shop, url, last_product_list = None):  # get shopify products
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
    
    # query = """
    # query {
    #     products(first: 5) {
    #         edges {
    #             node {
    #                 id
    #                 title
    #                 description
    #                 variants(first: 5) {
    #                     edges {
    #                         node {
    #                             sku
    #                             price
    #                             inventoryQuantity
    #                             inventoryItem {
    #                                 id
    #                             }
    #                         }
    #                     }
    #                 }
    #             }
    #         }
    #     }
    # }
    # """
    
    query = """
    query {
        products(first: 5) {
            edges {
                node {
                    id
                    title
                    description
                    variants(first: 5) {
                        edges {
                            node {
                                id
                                sku
                                price
                                inventoryQuantity
                                inventoryItem {
                                    id
                                    inventoryLevels(first: 5) {
                                        edges {
                                            node {
                                                quantities(names: ["available"]) {
                                                    name
                                                    quantity
                                                }
                                                location {
                                                    name
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    payload = {
        "query": query,
        "variables": {}  # Optional: add variables if needed
    }

    
    try:
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        data = r.json()
        print(r.text)
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
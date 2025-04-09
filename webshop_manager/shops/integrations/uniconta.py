import requests
from ..models import Feed, SyncLog
import json
import time
import math
from ..utils import *
import base64
from ..models import Product


# We need a processing function
# We need a sync function

def sync_uniconta_to_db(shop):
    getAllUnicontaProducts(shop) # creates data.json

    # Create or update products in database based on the downloaded shopify data
    with open('uniconta_data.json', 'r') as f:
        shop_data = json.load(f)
        for ishop in shop_data: # 
            for variant in ishop['variants']:  # Loop through all variants
                sku = variant["sku"]
                product_id = variant["product_id"]
                variant_id = variant["id"]
                product_name = variant["title"]
                price = variant["price"]
                inventory = variant.get("inventory_quantity", 0)
                inventory_item_id = variant["inventory_item_id"]

                Product.objects.update_or_create(
                    sku=sku,
                    defaults={
                        'client': shop.client,
                        'is_main_product': False,
                        'product_name': product_name,
                        'sku': sku,
                        'shopify_product_id': product_id,
                        'shopify_variant_id': variant_id,
                        'shopify_inventory_item_id': inventory_item_id,
                        'last_known_price': price,
                        'last_known_inventory': inventory
                    }
                )



# Handle our special sejlerbixen case
def initialize_uniconta_custom_sync(shop, mapped_data, feed):
    username = shop.api_key
    password = shop.api_secret
    company_id = shop.api_access_token

    credentials = f"00{company_id}/{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    auth_header = f"Basic {encoded_credentials}"
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }


    # changed_products = []
    # with open('data.json', 'r') as f:
    #     shop_data = json.load(f)
    #     for ishop in shop_data:
    #         for variant in ishop['variants']:  # Loop through all variants
    #             for ifeed in data:
    #                 if variant['sku'] == ifeed['sku']:
    #                     if variant['price'] != ifeed['price']:
    #                         changed_products.append({
    #                             "variant": {
    #                                 # "id": ishop['id'],
    #                                 "id": variant['id'],
    #                                 "price": str(ifeed['price'])
    #                             }
    #                         })
    
    # Execute the shopify update call
    try:
        # Loop over all changed products, build a payload for each of them and push it into shopify
        for i in mapped_data:
            print(i)
            # Delay to enforce api rate limit
            time.sleep(520/1000)
            #time.sleep(1)

            if i["MainItemSKU"] == None:
                MainItemSKU = i["sku"]
            else:
                MainItemSKU = i["MainItemSKU"]

            # WE NEED TO PROCESS ALL THE PRODUCTS BEFORE WE RUN THIS LOOP TO CALL THE API
            # BECAUSE WE NEED TO FIND ALL THE VARIANT NAMES FIRST

            VariantSKUs = "" # Actually a single string of variant names, seperated by commas. (NOT A LIST)

            payload = {
                "Item": i['sku'],
                "Name": i['title'],
                "Description": i['body_html'],
                "SalesPrice1": i['price'],
                "EAN": i['barcode'],
                "Weight": i['weight'],
                # "Image": i['images'],             # Not used at this time.
                "MainItemSKU": MainItemSKU,         # Custom Field: The SKU of the parent product of this item. If this is the parent, this is its own SKU.
                "VariantSKUs": VariantSKUs,         # Custom Field: Comma seperated strings of variant NAMES. (NOT A LIST)
                # "Webshop": true                   # Custom Field: Generally ignored because it should be false by default.
            }

            # Build url and send request for updating variant
            url = "https://odata.uniconta.com/api/Entities/Insert/InvItemClientUser"

            # Send request
            response = requests.post(url, json=payload, headers=headers)
            #print(response.status_code)
            #print(response.text)
            response.raise_for_status()

            # Log the result
            # data = response.json()
            sku = str(i['sku'])
            # variant_id = str(i['variant']['id'])
            # inventory_item_id = str(i['variant']['inventory_item_id'])
            
            #created_string = "Created product with " + "\n" + "SKU: " + sku + "\n"  + "product_id: " + product_id + "\n" + "variant_id: " + variant_id + "\n" + "inventory_item_id: " + inventory_item_id
            created_string = "Created product with " + "\n" + "SKU: " + sku + "\n"  + "MainItemSKU: " + MainItemSKU + "\n" + "Variant names: " + VariantSKUs
            #SyncLog.objects.create(feed=feed, shop=shop, status='success', message="Product synced to Uniconta")
            SyncLog.objects.create(feed=feed, shop=shop, status='success', message=created_string)

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise



# This is where the uniconta shop should start
def initialize_uniconta_sync(shop, mapped_data, feed):
    pass



def sync_to_uniconta(shop, mapped_data, feed):

    username = shop.api_key
    password = shop.api_secret
    company_id = shop.api_access_token

    credentials = f"00{company_id}/{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    auth_header = f"Basic {encoded_credentials}"
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }


    # changed_products = []
    # with open('data.json', 'r') as f:
    #     shop_data = json.load(f)
    #     for ishop in shop_data:
    #         for variant in ishop['variants']:  # Loop through all variants
    #             for ifeed in data:
    #                 if variant['sku'] == ifeed['sku']:
    #                     if variant['price'] != ifeed['price']:
    #                         changed_products.append({
    #                             "variant": {
    #                                 # "id": ishop['id'],
    #                                 "id": variant['id'],
    #                                 "price": str(ifeed['price'])
    #                             }
    #                         })
    
    # Execute the shopify update call
    try:
        # Loop over all changed products, build a payload for each of them and push it into shopify
        for i in mapped_data:
            print(i)
            # Delay to enforce api rate limit
            time.sleep(520/1000)
            #time.sleep(1)

            if i["MainItemSKU"] == None:
                MainItemSKU = i["sku"]
            else:
                MainItemSKU = i["MainItemSKU"]

            # WE NEED TO PROCESS ALL THE PRODUCTS BEFORE WE RUN THIS LOOP TO CALL THE API
            # BECAUSE WE NEED TO FIND ALL THE VARIANT NAMES FIRST

            VariantSKUs = "" # Actually a single string of variant names, seperated by commas. (NOT A LIST)

            payload = {
                "Item": i['sku'],
                "Name": i['title'],
                "Description": i['body_html'],
                "SalesPrice1": i['price'],
                "EAN": i['barcode'],
                "Weight": i['weight'],
                # "Image": i['images'],             # Not used at this time.
                "MainItemSKU": MainItemSKU,         # Custom Field: The SKU of the parent product of this item. If this is the parent, this is its own SKU.
                "VariantSKUs": VariantSKUs,         # Custom Field: Comma seperated strings of variant NAMES. (NOT A LIST)
                # "Webshop": true                   # Custom Field: Generally ignored because it should be false by default.
            }

            # Build url and send request for updating variant
            url = "https://odata.uniconta.com/api/Entities/Insert/InvItemClientUser"

            # Send request
            response = requests.post(url, json=payload, headers=headers)
            #print(response.status_code)
            #print(response.text)
            response.raise_for_status()

            # Log the result
            # data = response.json()
            sku = str(i['sku'])
            # variant_id = str(i['variant']['id'])
            # inventory_item_id = str(i['variant']['inventory_item_id'])
            
            #created_string = "Created product with " + "\n" + "SKU: " + sku + "\n"  + "product_id: " + product_id + "\n" + "variant_id: " + variant_id + "\n" + "inventory_item_id: " + inventory_item_id
            created_string = "Created product with " + "\n" + "SKU: " + sku + "\n"  + "MainItemSKU: " + MainItemSKU + "\n" + "Variant names: " + VariantSKUs
            #SyncLog.objects.create(feed=feed, shop=shop, status='success', message="Product synced to Uniconta")
            SyncLog.objects.create(feed=feed, shop=shop, status='success', message=created_string)

    except Exception as e:
        feed.sync_status = 'failed'
        feed.save()
        SyncLog.objects.create(feed=feed, shop=None, status='failed', message=str(e))
        raise





# get all uniconta products and save them into a json file
def getAllUnicontaProducts(shop):
    username = shop.api_key
    password = shop.api_secret
    company_id = shop.api_access_token

    credentials = f"00{company_id}/{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    auth_header = f"Basic {encoded_credentials}"
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }

    url = "https://odata.uniconta.com/api/Entities/InvItemClientUser"

    print("Getting all uniconta products ....")
    #product_list = getProducts(shop, product_list_url)
    # Send request
    response = requests.get(url, headers=headers)
    #print(response.status_code)
    #print(response.text)
    response.raise_for_status()

    # Log the result
    product_list = response.json()

    with open('uniconta_data.json', 'w') as f:
        json.dump(product_list, f)
    # return product_list
    print("Shopify products List size : "+str(len(product_list)))
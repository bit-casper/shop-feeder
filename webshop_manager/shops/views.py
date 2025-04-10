import os
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse
import requests
import xml.etree.ElementTree as ET
from .models import Client, Shop, Feed
from .forms import ClientForm, ShopForm, FeedForm
from .tasks import sync_feed_to_shops, sync_shop_to_db, sync_shopify_products_to_db
from django.db.models import Count


class ClientCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = ClientForm()
        return render(request, 'shops/client_form.html', {'form': form, 'title': 'Add Client'})

    def post(self, request):
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_list')
        return render(request, 'shops/client_form.html', {'form': form, 'title': 'Add Client'})
    


class ClientListView(LoginRequiredMixin, View):
    def get(self, request):
        clients = Client.objects.all().annotate(product_count=Count('products'))
        return render(request, 'shops/client_list.html', {'clients': clients})
    


# class ClientUpdateView(LoginRequiredMixin, View):
#     def get(self, request, client_id):
#         client = get_object_or_404(Shop, id=client_id)
#         form = ClientForm(instance=client)
#         return render(request, 'shops/client_form.html')#, {'form': form, 'shop': shop, 'title': 'Edit Shop'})

#     def post(self, request, client_id):
#         client = get_object_or_404(Client, id=client_id)
#         form = ClientForm(request.POST, instance=client)
#         if form.is_valid():
#             form.save()
#             return redirect('client_list')
#         return render(request, 'shops/client_form.html')#, {'form': form, 'shop': shop, 'title': 'Edit Shop'})

class ClientUpdateView(LoginRequiredMixin, View):
    def get(self, request, client_id):
        client = get_object_or_404(Client, id=client_id)  # Fixed: Changed Shop to Client
        form = ClientForm(instance=client)
        return render(request, 'shops/client_form.html', {
            'form': form,
            'client': client,
            'title': 'Edit Client',
        })

    def post(self, request, client_id):
        client = get_object_or_404(Client, id=client_id)
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_list')
        return render(request, 'shops/client_form.html', {
            'form': form,
            'client': client,
            'title': 'Edit Client',
        })
    


class ClientDeleteView(LoginRequiredMixin, View):
    def post(self, request, client_id):
        client = get_object_or_404(Client, id=client_id)
        client.delete()
        return redirect('client_list')



class ShopCreateView(LoginRequiredMixin, View):
    def get(self, request, client_id):
        form = ShopForm()
        return render(request, 'shops/shop_form.html', {'form': form, 'title': 'Add Shop', 'client_id': client_id})

    def post(self, request, client_id):
        form = ShopForm(request.POST)
        if form.is_valid():
            shop = form.save(commit=False) 
            shop.client = Client.objects.get(id=client_id) 
            shop.save()
            return redirect('shop_list', client_id=client_id)
        return render(request, 'shops/shop_form.html', {'form': form, 'title': 'Add Shop', 'client_id': client_id})



class ShopListView(LoginRequiredMixin, View):
    def get(self, request, client_id):
        client = get_object_or_404(Client, id=client_id)
        shops = Shop.objects.filter(client_id=client_id)
        feeds = Feed.objects.filter(client_id=client_id).prefetch_related('shops').distinct()
        return render(request, 'shops/shop_list.html', {'shops': shops, 'feeds': feeds, 'client': client,})

    def post(self, request, client_id):
        if 'sync_feed' in request.POST:
            feed_id = request.POST.get('feed_id')
            sync_feed_to_shops.delay(feed_id)
            return redirect('shop_list', client_id=client_id)
        elif 'sync_shop' in request.POST:
            shop_id = request.POST.get('shop_id')
            #sync_shop_to_db.delay(shop_id)
            sync_shopify_products_to_db.delay(shop_id)
            return redirect('shop_list', client_id=client_id)
        return self.get(request, client_id)



class ShopUpdateView(LoginRequiredMixin, View):
    def get(self, request, shop_id, client_id):  # Add client_id parameter
        shop = get_object_or_404(Shop, id=shop_id, client_id=client_id)
        form = ShopForm(instance=shop)
        return render(request, 'shops/shop_form.html', {'form': form, 'shop': shop, 'title': 'Edit Shop', 'client_id': client_id})

    def post(self, request, shop_id, client_id):  # Add client_id parameter
        shop = get_object_or_404(Shop, id=shop_id, client_id=client_id)
        form = ShopForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            return redirect('shop_list', client_id=client_id)
        return render(request, 'shops/shop_form.html', {'form': form, 'shop': shop, 'title': 'Edit Shop', 'client_id': client_id})



class ShopDeleteView(LoginRequiredMixin, View):
    def post(self, request, shop_id, client_id):  # Add client_id
        shop = get_object_or_404(Shop, id=shop_id, client_id=client_id)
        shop.delete()
        return redirect('shop_list', client_id=client_id)



class FeedCreateView(LoginRequiredMixin, View):
    def get(self, request, client_id):
        form = FeedForm(client_id=client_id)
        return render(request, 'shops/feed_form.html', {'form': form, 'title': 'Add Feed', 'client_id': client_id})

    def post(self, request, client_id):
        form = FeedForm(request.POST, client_id=client_id)
        if form.is_valid():
            feed = form.save(commit=False)
            feed.client = Client.objects.get(id=client_id)
            feed.save()
            form.save_m2m()
            return redirect('shop_list', client_id=client_id)
        return render(request, 'shops/feed_form.html', {'form': form, 'title': 'Add Feed', 'client_id': client_id})



class FeedEditDashboardView(LoginRequiredMixin, View):
    def get(self, request, feed_id, client_id):
        feed = get_object_or_404(Feed, id=feed_id, client_id=client_id)
        form = FeedForm(instance=feed, client_id=client_id)
        return render(request, 'shops/feed_form.html', {
            'form': form,
            'feed': feed,
            'title': f'Edit Feed: {feed.url or feed.ftp_host or feed.name}',
            'client_id': client_id,
        })

    def post(self, request, feed_id, client_id):
        feed = get_object_or_404(Feed, id=feed_id, client_id=client_id)
        form = FeedForm(request.POST, instance=feed, client_id=client_id)
        if form.is_valid():
            feed = form.save(commit=False)
            feed.save()
            feed.shops.set(form.cleaned_data['shops'])
            return redirect('shop_list', client_id=client_id)
        print("Form errors:", form.errors)
        return render(request, 'shops/feed_form.html', {
            'form': form,
            'feed': feed,
            'title': f'Edit Feed: {feed.url or feed.ftp_host}',
            'client_id': client_id,
        })



class FeedDeleteView(LoginRequiredMixin, View):
    def post(self, request, feed_id, client_id):  # Add client_id
        feed = get_object_or_404(Feed, id=feed_id, client_id=client_id)
        feed.delete()
        return redirect('shop_list', client_id=client_id)



class FeedTestMappingView(LoginRequiredMixin, View):
    def post(self, request, shop_id, pk):
        feed = get_object_or_404(Feed, pk=pk, shops__id=shop_id)
        
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

            
            for item in tree.findall('.//' + str(feed.feed_product_tag)):
                #print(item.text)
                mapped_data = {}
                
                for xml_key, shop_key in feed.mapping.items():
                    element = item.find(xml_key)
                    value = element.text if element is not None else 'N/A'
                    mapped_data[shop_key] = value

                # Sync to each subscribed shop
                # for shop in feed.shops.all():
                #     if shop.shop_type == 'shopify':
                #         sync_to_shopify(shop, mapped_data, feed)
                #     elif shop.shop_type == 'uniconta':
                #         sync_to_uniconta(shop, mapped_data, feed)

            return JsonResponse({'sample': mapped_data})
            #return JsonResponse({'sample': "disabled"})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
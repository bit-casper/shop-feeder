import os
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse
import requests
import xml.etree.ElementTree as ET
from .models import Shop, Feed
from .forms import ShopForm, FeedForm
from .tasks import sync_feed_to_shops  # Add this import

class ShopListView(LoginRequiredMixin, View):
    def get(self, request):
        shops = Shop.objects.all()
        feeds = Feed.objects.all().prefetch_related('shops')
        return render(request, 'shops/shop_list.html', {'shops': shops, 'feeds': feeds})

    def post(self, request):
        if 'sync_feed' in request.POST:
            feed_id = request.POST.get('feed_id')
            sync_feed_to_shops.delay(feed_id)  # Now recognized
            return redirect('shop_list')
        return self.get(request)

class ShopCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = ShopForm()
        return render(request, 'shops/shop_form.html', {'form': form, 'title': 'Add Shop'})

    def post(self, request):
        form = ShopForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shop_list')
        return render(request, 'shops/shop_form.html', {'form': form, 'title': 'Add Shop'})

class ShopUpdateView(LoginRequiredMixin, View):
    def get(self, request, shop_id):
        shop = get_object_or_404(Shop, id=shop_id)
        form = ShopForm(instance=shop)
        return render(request, 'shops/shop_form.html', {'form': form, 'shop': shop, 'title': 'Edit Shop'})

    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, id=shop_id)
        form = ShopForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            return redirect('shop_list')
        return render(request, 'shops/shop_form.html', {'form': form, 'shop': shop, 'title': 'Edit Shop'})

class ShopDeleteView(LoginRequiredMixin, View):
    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, id=shop_id)
        shop.delete()
        return redirect('shop_list')

class FeedCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = FeedForm()
        return render(request, 'shops/feed_form.html', {'form': form, 'title': 'Add Feed'})

    def post(self, request):
        form = FeedForm(request.POST)
        if form.is_valid():
            feed = form.save(commit=False)
            feed.save()
            if form.cleaned_data['shops']:
                feed.shops.set(form.cleaned_data['shops'])
            return redirect('shop_list')
        print("Form errors:", form.errors)
        return render(request, 'shops/feed_form.html', {'form': form, 'title': 'Add Feed'})

class FeedEditDashboardView(LoginRequiredMixin, View):
    def get(self, request, feed_id):
        feed = get_object_or_404(Feed, id=feed_id)
        form = FeedForm(instance=feed)
        return render(request, 'shops/feed_form.html', {
            'form': form,
            'feed': feed,
            'title': f'Edit Feed: {feed.url or feed.ftp_host or feed.name}',
        })

    def post(self, request, feed_id):
        feed = get_object_or_404(Feed, id=feed_id)
        form = FeedForm(request.POST, instance=feed)
        if form.is_valid():
            feed = form.save(commit=False)
            feed.save()
            feed.shops.set(form.cleaned_data['shops'])
            return redirect('shop_list')
        print("Form errors:", form.errors)
        return render(request, 'shops/feed_form.html', {
            'form': form,
            'feed': feed,
            'title': f'Edit Feed: {feed.url or feed.ftp_host}',
        })

class FeedDeleteView(LoginRequiredMixin, View):
    def post(self, request, feed_id):
        feed = get_object_or_404(Feed, id=feed_id)
        feed.delete()
        return redirect('shop_list')




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
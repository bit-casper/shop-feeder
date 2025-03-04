from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .models import Shop, Feed
from .forms import ShopForm, FeedForm
import ftplib
import requests
import xml.etree.ElementTree as ET
import json
from django.http import JsonResponse
from django.utils import timezone
import io



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

class ShopListView(LoginRequiredMixin, View):
    def get(self, request):
        shops = Shop.objects.all()
        return render(request, 'shops/shop_list.html', {'shops': shops})

class ShopUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        form = ShopForm(instance=shop)
        return render(request, 'shops/shop_form.html', {'form': form, 'title': 'Edit Shop', 'shop': shop})
    
    def post(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        form = ShopForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            return redirect('shop_list')
        return render(request, 'shops/shop_form.html', {'form': form, 'title': 'Edit Shop', 'shop': shop})

class ShopDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        shop.delete()
        return redirect('shop_list')



class FeedListView(LoginRequiredMixin, View):
    def get(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        feeds = Feed.objects.filter(shop=shop)
        return render(request, 'shops/feed_list.html', {'shop': shop, 'feeds': feeds})



class FeedCreateView(LoginRequiredMixin, View):
    def get(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        form = FeedForm()
        return render(request, 'shops/feed_form.html', {'form': form, 'shop': shop, 'title': 'Add Feed'})
    
    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        form = FeedForm(request.POST)
        if form.is_valid():
            feed = form.save(commit=False)
            feed.shop = shop
            feed.save()
            return redirect('feed_list', shop_id=shop_id)
        return render(request, 'shops/feed_form.html', {'form': form, 'shop': shop, 'title': 'Add Feed'})



class FeedUpdateView(LoginRequiredMixin, View):
    def get(self, request, shop_id, pk):
        feed = get_object_or_404(Feed, pk=pk, shop_id=shop_id)
        form = FeedForm(instance=feed)
        return render(request, 'shops/feed_form.html', {'form': form, 'shop': feed.shop, 'title': 'Edit Feed', 'feed': feed})
    
    def post(self, request, shop_id, pk):
        feed = get_object_or_404(Feed, pk=pk, shop_id=shop_id)
        form = FeedForm(request.POST, instance=feed)
        if form.is_valid():
            form.save()
            return redirect('feed_list', shop_id=shop_id)
        return render(request, 'shops/feed_form.html', {'form': form, 'shop': feed.shop, 'title': 'Edit Feed', 'feed': feed})



class FeedDeleteView(LoginRequiredMixin, View):
    def post(self, request, shop_id, pk):
        feed = get_object_or_404(Feed, pk=pk, shop_id=shop_id)
        feed.delete()
        return redirect('feed_list', shop_id=shop_id)



class FeedTestMappingView(LoginRequiredMixin, View):
    def post(self, request, shop_id, pk):
        feed = get_object_or_404(Feed, pk=pk, shop_id=shop_id)
        
        try:
            if feed.source_type == 'ftp':
                if not feed.ftp_host:
                    return JsonResponse({'error': 'FTP host is missing'}, status=400)
                ftp = ftplib.FTP(feed.ftp_host)
                ftp.login(feed.ftp_user, feed.ftp_pass)
                with open('temp.xml', 'wb') as f:
                    ftp.retrbinary(f"RETR {feed.file_pattern}", f.write)
                ftp.quit()
                file_path = 'temp.xml'
            else:  # url
                if not feed.url:
                    return JsonResponse({'error': 'URL is missing'}, status=400)
                response = requests.get(feed.url)
                response.raise_for_status()
                with open('temp.xml', 'wb') as f:
                    f.write(response.content)
                file_path = 'temp.xml'

            tree = ET.parse(file_path)
            root = tree.getroot()
            sample = root  # Use root as sample (matches earlier fix)
            
            mapping = feed.mapping
            mapped_data = {}
            for xml_key, shop_key in mapping.items():
                element = sample.find(xml_key)
                value = element.text if element is not None else 'N/A'
                mapped_data[shop_key] = value

            return JsonResponse({'sample': mapped_data})
        except ftplib.all_errors as e:
            return JsonResponse({'error': f'FTP Error: {str(e)}'}, status=500)
        except requests.RequestException as e:
            return JsonResponse({'error': f'URL Error: {str(e)}'}, status=500)
        except Exception as e:
            return JsonResponse({'error': f'Unexpected Error: {str(e)}'}, status=500)
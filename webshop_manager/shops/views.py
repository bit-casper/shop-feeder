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
            'title': f'Edit Feed: {feed.url or feed.ftp_host}',
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
            if feed.source_type == 'url':
                response = requests.get(feed.url)
                response.raise_for_status()
                xml_data = response.content
            else:
                return JsonResponse({'error': 'FTP not yet implemented'}, status=400)

            tree = ET.fromstring(xml_data)
            root = tree.getroot()
            mapped_data = {}
            for xml_key, shop_key in feed.mapping.items():
                element = root.find(xml_key)
                value = element.text if element is not None else 'N/A'
                mapped_data[shop_key] = value

            return JsonResponse({'sample': mapped_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
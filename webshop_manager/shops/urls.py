from django.urls import path
from .views import (
    ShopListView, ShopCreateView, ShopUpdateView, ShopDeleteView,
    FeedListView, FeedCreateView, FeedUpdateView, FeedDeleteView,
    FeedTestMappingView
)

urlpatterns = [
    path('', ShopListView.as_view(), name='shop_list'),
    path('shops/add/', ShopCreateView.as_view(), name='shop_create'),
    path('shops/<int:pk>/edit/', ShopUpdateView.as_view(), name='shop_update'),
    path('shops/<int:pk>/delete/', ShopDeleteView.as_view(), name='shop_delete'),
    path('shops/<int:shop_id>/feeds/', FeedListView.as_view(), name='feed_list'),
    path('shops/<int:shop_id>/feeds/add/', FeedCreateView.as_view(), name='feed_create'),
    path('shops/<int:shop_id>/feeds/<int:pk>/edit/', FeedUpdateView.as_view(), name='feed_update'),
    path('shops/<int:shop_id>/feeds/<int:pk>/delete/', FeedDeleteView.as_view(), name='feed_delete'),
    path('shops/<int:shop_id>/feeds/<int:pk>/test/', FeedTestMappingView.as_view(), name='feed_test_mapping'),
]
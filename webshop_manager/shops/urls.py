from django.urls import path
from . import views

urlpatterns = [
    # Client-related URLs
    path('', views.ClientListView.as_view(), name='client_list'),
    path('clients/add/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:client_id>/edit/', views.ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:client_id>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
    
    # Shop-related URLs
    path('client/<int:client_id>/', views.ShopListView.as_view(), name='shop_list'),
    path('client/<int:client_id>/shops/add/', views.ShopCreateView.as_view(), name='shop_create'),
    path('client/<int:client_id>/shops/<int:shop_id>/edit/', views.ShopUpdateView.as_view(), name='shop_update'),
    path('client/<int:client_id>/shops/<int:shop_id>/delete/', views.ShopDeleteView.as_view(), name='shop_delete'),
    
    # Feed-related URLs
    path('client/<int:client_id>/feeds/add/', views.FeedCreateView.as_view(), name='feed_create'),
    path('client/<int:client_id>/feeds/<int:feed_id>/edit/', views.FeedEditDashboardView.as_view(), name='feed_edit_dashboard'),
    path('client/<int:client_id>/feeds/<int:feed_id>/delete/', views.FeedDeleteView.as_view(), name='feed_delete'),
    path('shops/<int:shop_id>/feeds/<int:pk>/test/', views.FeedTestMappingView.as_view(), name='feed_test_mapping'),
]
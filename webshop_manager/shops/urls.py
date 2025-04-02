from django.urls import path
from . import views

urlpatterns = [
    path('', views.ClientListView.as_view(), name='client_list'),
    path('add/', views.ClientCreateView.as_view(), name='client_create'),
    path('<int:client_id>/edit/', views.ClientUpdateView.as_view(), name='client_update'),
    path('<int:client_id>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
    path('client/<int:client_id', views.ShopListView.as_view(), name='shop_list'),
    path('add/', views.ShopCreateView.as_view(), name='shop_create'),
    path('<int:shop_id>/edit/', views.ShopUpdateView.as_view(), name='shop_update'),
    path('<int:shop_id>/delete/', views.ShopDeleteView.as_view(), name='shop_delete'),
    path('feeds/add/', views.FeedCreateView.as_view(), name='feed_create'),
    path('feeds/<int:feed_id>/edit/', views.FeedEditDashboardView.as_view(), name='feed_edit_dashboard'),
    path('feeds/<int:feed_id>/delete/', views.FeedDeleteView.as_view(), name='feed_delete'),
    #path('<int:shop_id>/feeds/<int:pk>/test/', views.FeedTestMappingView.as_view(), name='feed_test'),  # Temporary
    path('shops/<int:shop_id>/feeds/<int:pk>/test/', views.FeedTestMappingView.as_view(), name='feed_test_mapping'),
]
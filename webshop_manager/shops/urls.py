from django.urls import path
from . import views

urlpatterns = [
    path('', views.ShopListView.as_view(), name='shop_list'),
    path('add/', views.ShopCreateView.as_view(), name='shop_create'),
    path('<int:shop_id>/edit/', views.ShopUpdateView.as_view(), name='shop_update'),
    path('<int:shop_id>/delete/', views.ShopDeleteView.as_view(), name='shop_delete'),
    path('feeds/add/', views.FeedCreateView.as_view(), name='feed_create'),
    path('feeds/<int:feed_id>/edit/', views.FeedEditDashboardView.as_view(), name='feed_edit_dashboard'),
    path('feeds/<int:feed_id>/delete/', views.FeedDeleteView.as_view(), name='feed_delete'),
    path('<int:shop_id>/feeds/<int:pk>/test/', views.FeedTestMappingView.as_view(), name='feed_test'),  # Temporary
]
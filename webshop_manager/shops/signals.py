from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Feed
from .tasks import sync_single_feed
from celery.schedules import crontab
from celery.task import periodic_task
from django.utils import timezone

@receiver(post_save, sender=Feed)
def schedule_feed_sync(sender, instance, created, **kwargs):
    if created or instance.sync_status == 'pending':
        sync_single_feed.delay(instance.id)

@periodic_task(run_every=crontab(minute='*/15'))
def sync_all_feeds():
    for feed in Feed.objects.filter(sync_status='pending'):
        if feed.shops.filter(is_active=True).exists():
            sync_single_feed.delay(feed.id)
    for feed in Feed.objects.filter(sync_status='success'):
        if feed.shops.filter(is_active=True).exists() and (not feed.last_sync or (timezone.now() - feed.last_sync).total_seconds() / 60 >= min(shop.sync_interval for shop in feed.shops.all())):
            sync_single_feed.delay(feed.id)
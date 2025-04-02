from django import forms
from .models import Client, Shop, Feed


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['client_name']
        widgets = {
            
        }

class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['shop_name', 'shop_type', 'api_endpoint', 'api_key', 'api_secret', 'api_access_token', 'is_active', 'sync_interval']
        widgets = {
            'api_key': forms.PasswordInput(),
            'api_secret': forms.PasswordInput(),
            'api_access_token': forms.PasswordInput(),
        }

class FeedForm(forms.ModelForm):
    shops = forms.ModelMultipleChoiceField(
        queryset=Shop.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Subscribed Shops'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for shop in self.fields['shops'].queryset:
            self.fields['shops'].choices = [
                (shop.id, f"{shop.shop_name} - {shop.get_shop_type_display()}")
                for shop in self.fields['shops'].queryset
            ]

    class Meta:
        model = Feed
        fields = ['name', 'shops', 'source_type', 'feed_product_tag', 'sku_prefix', 'ftp_host', 'ftp_user', 'ftp_pass', 'url', 'file_pattern', 'format_type', 'mapping']
        widgets = {
            'ftp_pass': forms.PasswordInput(),
            'mapping': forms.Textarea(attrs={'rows': 4}),
        }
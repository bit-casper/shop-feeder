from django import forms
from .models import Shop, Feed

class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'shop_type', 'api_endpoint', 'api_key', 'api_secret', 'is_active', 'sync_interval']
        widgets = {
            'api_key': forms.PasswordInput(),
            'api_secret': forms.PasswordInput(),
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
                (shop.id, f"{shop.name} - {shop.get_shop_type_display()}")
                for shop in self.fields['shops'].queryset
            ]

    class Meta:
        model = Feed
        fields = ['name', 'shops', 'source_type', 'ftp_host', 'ftp_user', 'ftp_pass', 'url', 'file_pattern', 'format_type', 'mapping']
        widgets = {
            'ftp_pass': forms.PasswordInput(),
            'mapping': forms.Textarea(attrs={'rows': 4}),
        }
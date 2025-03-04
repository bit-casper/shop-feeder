from django import forms
from django.core.exceptions import ValidationError
from .models import Shop, Feed
import json

class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'shop_type', 'api_endpoint', 'api_key', 'api_secret', 'is_active', 'sync_interval']
        widgets = {
            'api_key': forms.PasswordInput(render_value=True),
            'api_secret': forms.PasswordInput(render_value=True),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        api_endpoint = cleaned_data.get('api_endpoint')
        api_key = cleaned_data.get('api_key')

        if not name:
            raise ValidationError("Shop name is required.")
        if not api_endpoint:
            raise ValidationError("API endpoint is required.")
        if not api_key:
            raise ValidationError("API key is required.")
        return cleaned_data

class FeedForm(forms.ModelForm):
    class Meta:
        model = Feed
        fields = ['source_type', 'ftp_host', 'ftp_user', 'ftp_pass', 'url', 'file_pattern', 'format_type', 'mapping']
        widgets = {
            'ftp_user': forms.PasswordInput(render_value=True),
            'ftp_pass': forms.PasswordInput(render_value=True),
            'mapping': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get('source_type')
        ftp_host = cleaned_data.get('ftp_host')
        url = cleaned_data.get('url')
        file_pattern = cleaned_data.get('file_pattern')

        if source_type == 'ftp':
            if not ftp_host:
                raise ValidationError("FTP host is required for FTP source type.")
            if not cleaned_data.get('ftp_user'):
                raise ValidationError("FTP user is required for FTP source type.")
            if not cleaned_data.get('ftp_pass'):
                raise ValidationError("FTP password is required for FTP source type.")
        elif source_type == 'url':
            if not url:
                raise ValidationError("URL is required for URL source type.")
        
        if not file_pattern:
            raise ValidationError("File pattern is required.")
        return cleaned_data

    def clean_mapping(self):
        mapping = self.cleaned_data['mapping']
        if isinstance(mapping, str):
            try:
                return json.loads(mapping)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid JSON format")
        return mapping
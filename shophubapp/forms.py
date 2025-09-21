from django import forms

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Product

from .models import Profile, ListOfProducts

MAX_UPLOAD_SIZE = 2500000


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio_input_text', 'profile_picture']

    def clean_bio(self):
        bio = self.cleaned_data.get('bio_input_text')
        if len(bio) > 500:
            raise forms.ValidationError("Bio cannot exceed 500 characters.")
        return bio

    def clean_picture(self):
        picture = self.cleaned_data['profile_picture']
        if not picture or not hasattr(picture, 'content_type'):
            raise forms.ValidationError('You must upload a picture')
        if not picture.content_type or not picture.content_type.startswith('image'):
            raise forms.ValidationError('File type is not image')
        if picture.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError(
                'File too big (max size is {0} bytes)'.format(MAX_UPLOAD_SIZE))
        return picture


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'brand',
                  'image_url', 'product_url', 'cooldown_hours']

    def clean_product_input(self):
        input_descr = self.cleaned_data.get('description')
        if len(input_descr) > 200:
            raise forms.ValidationError(
                "Description cannot exceed 200 characters.")
        return input_descr


class URLForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_url', 'cooldown_hours']


class ListOfProductsForm(forms.ModelForm):
    class Meta:
        model = ListOfProducts
        fields = ['name', 'private']

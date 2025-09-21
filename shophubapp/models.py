from datetime import timedelta
from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from math import ceil
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ListOfProducts(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_lists')
    name = models.CharField(max_length=100)
    private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    collaborators = models.ManyToManyField(User, related_name = 'collaborating_lists', blank = True)

    def __str__(self):
        return f"{self.user.username}'s {self.name} List"

    def get_first_product_image_url(self):
        first_product = self.products.first()  # Access the related 'products' queryset
        if first_product and first_product.image_url:
            return first_product.image_url
        return '/static/bags.png'  # Return None if no products or no image

    def get_user_id(self):
        return self.user_id


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio_input_text = models.TextField(blank=True, max_length=200)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', default='profile_pics/default.jpg')
    followers = models.ManyToManyField(
        'self', related_name='following', symmetrical=False)
    friendrequests = models.ManyToManyField(
        'self', related_name='friend_requests', symmetrical=False)
    sentrequests = models.ManyToManyField(
        'self', related_name='sent_requests', symmetrical=False)
    starred_lists = models.ManyToManyField(
        ListOfProducts, related_name='starred_lists', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Product(models.Model):
    """Represents a product fetched from an external shopping site."""
    user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
    list_of_products = models.ForeignKey(
        ListOfProducts, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=200)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    product_url = models.URLField(max_length=500)
    added_at = models.DateTimeField(auto_now_add=True)
    cooldown_hours = models.PositiveIntegerField(default=24)

    @property
    def is_locked(self):
        return now() < self.added_at + timedelta(hours=self.cooldown_hours)

    @property
    def remaining_cooldown_hours(self):
        elapsed_time = now() - self.added_at
        remaining_time = timedelta(hours=self.cooldown_hours) - elapsed_time
        remaining_hours = remaining_time.total_seconds() / 3600
        return max(0, ceil(remaining_hours))

    def __str__(self):
        return self.name


class OutgoingLinkClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField()
    clicked_at = models.DateTimeField(auto_now_add=True)


class Notifications(models.Model):
    recipient = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'notifications')
    sender = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'sent_notifications')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField() 
    content_object = GenericForeignKey('content_type', 'object_id')
    timestamp = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.sender} -> {self.recipient}: {self.content_object}'
    
    def get_absolute_url(self):
        return reverse('view_list', args=[self.id])
    

class CollaborationRequest(models.Model):
    list = models.ForeignKey(ListOfProducts, on_delete=models.CASCADE, related_name='collaboration_requests')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_collab_requests')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_collab_requests')
    accepted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender} requested collaboration on {self.list.name}'

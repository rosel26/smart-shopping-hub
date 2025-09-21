from django.contrib import admin

# Register your models here.
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    exclude = ('added_at',)
    list_display = ('name', 'user', 'price', 'brand',
                    'cooldown_hours', 'is_locked')
    list_filter = ('user', 'brand')
    search_fields = ('name', 'brand')
    readonly_fields = ('is_locked',)

    fields = ('user', 'list_of_products', 'name', 'price', 'brand',
              'image_url', 'product_url', 'cooldown_hours')

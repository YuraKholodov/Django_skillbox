from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse

from shopapp.models import Product


class ShopSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return Product.objects.filter(archived=False)

    def lastmod(self, obj: Product):
        return obj.created_at

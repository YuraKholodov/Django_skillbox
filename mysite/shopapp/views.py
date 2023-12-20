"""
В этом модуле лежат различные наборы представлений.

Разные view интернет-магазина: по товарам, заказам и т.д.
"""

import logging
from timeit import default_timer

from csv import DictWriter

from django.contrib.syndication.views import Feed
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, reverse, redirect, get_object_or_404

from django.contrib.auth.models import Group, User
from django.urls import reverse_lazy
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from rest_framework.generics import ListAPIView

from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .common import save_csv_products
from .models import Product, Order, ProductImage
from .forms import GroupForm, ProductForm
from .serializers import ProductSerializer, OrderSerializer

from django.views import View

log = logging.getLogger(__name__)


@extend_schema(description="Product views CRUD")
class ProductViewSet(ModelViewSet):
    """
    Набор представлений для действий над Product
    Полный CRUD для сущностей товара
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields = ["name", "description"]
    filterset_fields = [
        "name",
        "description",
        "price",
        "discount",
        "archived",
    ]
    ordering_fields = [
        "name",
        "price",
        "discount",
    ]

    @method_decorator(cache_page(60 * 2))
    def list(self, *args, **kwargs):
        print("hello products list")
        return super().list(*args, **kwargs)

    @action(methods=["get"], detail=False)
    def download_csv(self, request: Request):
        response = HttpResponse(content_type="text/csv")
        filename = "products-export.csv"
        response["Content-Disposition"] = f"attachment; filename={filename}"
        queryset = self.filter_queryset(self.get_queryset())
        fields = [
            "name",
            "description",
            "price",
            "discount",
        ]
        queryset = queryset.only(*fields)
        writer = DictWriter(response, fieldnames=fields)
        writer.writeheader()

        for product in queryset:
            writer.writerow(
                {
                    field: getattr(product, field)
                    for field in fields
                }
            )
        return response

    @extend_schema(
        summary="Get one product by ID",
        description="Retrieves **product**, returns 404 if not found",
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Empty response, product by id not found"),
        }
    )
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser], )
    def upload_csv(self, request: Request):
        products = save_csv_products(
            request.FILES["file"].file,
            encoding=request.encoding,
        )
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class UserOrdersListExport(View):

    def get(self, request: HttpRequest, user_id) -> JsonResponse:
        _user = get_object_or_404(User, pk=user_id)
        cache_key = "orders_data_export_" + str(_user.pk)
        orders_data = cache.get(cache_key)

        if orders_data is None:
            orders = Order.objects. \
                filter(user=_user). \
                select_related("user"). \
                prefetch_related("products"). \
                order_by("pk")

            orders_data = OrderSerializer(orders, many=True)
            cache.set(cache_key, orders_data, 300)
        return JsonResponse({"orders": orders_data.data})


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.select_related('user').prefetch_related('products').all()
    serializer_class = OrderSerializer
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]
    search_fields = ["delivery_address", "user"]
    filterset_fields = [
        "delivery_address",
        "promocode",
        "created_at",
        "user",
        "products",
    ]
    ordering_fields = [
        "delivery_address",
        "created_at",
        "user",
    ]


class ShopIndexView(View):

    # @method_decorator(cache_page(60 * 2))
    def get(self, request: HttpRequest) -> HttpResponse:
        products = [
            ("Iphone7", 1000),
            ("SmartPhone", 200),
            ("TelePhone", 20),
        ]
        context = {
            "time_running": default_timer(),
            "products": products,
            "items": 5,
        }
        log.debug("Products for shop index: %s", products)
        log.info("Rendering shop index")
        return render(request, "shopapp/shop_index.html", context=context)


class GroupsListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            "form": GroupForm(),
            "groups": Group.objects.prefetch_related("permissions").all(),
        }
        return render(request, "shopapp/groups_list.html", context=context)

    def post(self, request: HttpRequest) -> HttpResponse:
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect(request.path)


class ProductDetailsView(DetailView):
    template_name = "shopapp/product_details.html"
    queryset = Product.objects.prefetch_related('images')
    context_object_name = "product"


class ProductsListView(ListView):
    template_name = "shopapp/products_list.html"
    # model = Product
    context_object_name = "products"
    queryset = Product.objects.filter(archived=False)


class ProductCreateView(PermissionRequiredMixin, CreateView):
    permission_required = ("shopapp.add_product",)
    model = Product
    # fields = "name", "price", "description", "discount", "preview"
    success_url = reverse_lazy("shopapp:products_list")
    form_class = ProductForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        for image in form.files.getlist("images"):
            ProductImage.objects.create(product=self.object, image=image, )

        return response


class ProductUpdateView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    permission_required = ("shopapp.change_product",)

    def test_func(self):
        return self.request.user == self.get_object().created_by

    model = Product
    # fields = "name", "price", "description", "discount", "preview"
    template_name_suffix = "_update_form"
    form_class = ProductForm

    def form_valid(self, form):
        response = super().form_valid(form)
        for image in form.files.getlist("images"):
            ProductImage.objects.create(product=self.object, image=image, )

        return response

    def get_success_url(self):
        return reverse("shopapp:product_details", kwargs={"pk": self.object.pk})


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy("shopapp:products_list")

    def form_valid(self, form):
        succes_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(succes_url)


class OrdersListView(LoginRequiredMixin, ListView):
    context_object_name = "orders"
    queryset = Order.objects.select_related("user").prefetch_related("products")


class UserOrdersListView(LoginRequiredMixin, ListView):
    context_object_name = "user_orders"
    template_name = "shopapp/user_orders_list.html"

    def get_queryset(self):
        self.owner = get_object_or_404(User, pk=self.kwargs.get("user_id"))
        return Order.objects.filter(user=self.owner).select_related("user").prefetch_related("products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self.owner
        return context


class OrderDetailView(PermissionRequiredMixin, DetailView):
    permission_required = ("shopapp.view_order",)
    queryset = Order.objects.select_related("user").prefetch_related("products")


class OrderCreateView(CreateView):
    model = Order
    fields = "delivery_address", "promocode", "products"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("shopapp:order_details", kwargs={"pk": self.object.pk})


class OrderUpdateView(UpdateView):
    model = Order
    fields = "delivery_address", "promocode", "user", "products"
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse("shopapp:order_details", kwargs={"pk": self.object.pk})


class OrderDeleteView(DeleteView):
    model = Order
    success_url = reverse_lazy("shopapp:orders_list")


class ProductsDataExportView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        cache_key = "products_data_export"
        products_data = cache.get(cache_key)
        if products_data is None:
            products = Product.objects.order_by("pk").all()
            products_data = [
                {
                    "pk": product.pk,
                    "name": product.name,
                    "price": product.price,
                    "archived": product.archived,
                }
                for product in products
            ]
            cache.set(cache_key, products_data, 300)
        elem = products_data[0]
        name = elem['name']
        print("name:", name)
        return JsonResponse({"products": products_data})


class OrdersDataExportView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request: HttpRequest) -> JsonResponse:
        orders = Order.objects.order_by("pk").all()
        orders_data = [
            {
                "pk": order.pk,
                "delivery_address": order.delivery_address,
                "promocode": order.promocode,
                "user": order.user.username,
                "products": str([product.pk for product in order.products.all()]),
            }
            for order in orders
        ]
        return JsonResponse({"orders": orders_data})


class LatestProductsFeed(Feed):
    title = "Blog products (latest)"
    description = "Updates on changes and addition blog about new products"
    link = reverse_lazy("shopapp:products_list")

    def items(self):
        return (Product.objects.filter(archived=False)[:5])

    def item_title(self, item: Product):
        return item.name

    def item_description(self, item: Product):
        return item.description[:200]

    def item_link(self, item: Product):
        return reverse("shopapp:product_details", kwargs={"pk": item.pk})

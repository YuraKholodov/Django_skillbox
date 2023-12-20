import json
from string import ascii_letters
from random import choices

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.test import TestCase

from .models import Product, Order
from .utils import add_two_numbers
from django.urls import reverse


class AddTwoNumbersTestCase(TestCase):
    def test_add_two_numbers(self):
        result = add_two_numbers(2, 3)
        self.assertEqual(result, 5)


class ProductCreateViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.permission_create_product = Permission.objects.get(codename="add_product")
        cls.user = User.objects.create_user(
            username="test_name", password="test_password"
        )
        cls.user.user_permissions.add(cls.permission_create_product)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)
        self.product_name = "".join(choices(ascii_letters, k=10))
        Product.objects.filter(name=self.product_name).delete()

    def test_create_product(self):
        response = self.client.post(
            reverse("shopapp:product_create"),
            {
                "name": self.product_name,
                "price": "123.45",
                "description": "A good table",
                "discount": "10",
            },
        )
        self.assertRedirects(response, reverse("shopapp:products_list"))
        self.assertTrue(Product.objects.filter(name=self.product_name).exists())


class ProductDetailsViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.product = Product.objects.create(name="Best Product")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.product.delete()

    def test_get_product(self):
        response = self.client.get(
            reverse("shopapp:product_details", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_get_product_and_check_content(self):
        response = self.client.get(
            reverse("shopapp:product_details", kwargs={"pk": self.product.pk})
        )
        self.assertContains(response, self.product.name)


class ProductsListViewTestCase(TestCase):
    # fixtures = [
    #     'products-fixture.json',
    # ]

    def test_products(self):
        response = self.client.get(reverse("shopapp:products_list"))
        self.assertQuerysetEqual(
            qs=Product.objects.filter(archived=False).all(),
            values=(p.pk for p in response.context["products"]),
            transform=lambda p: p.pk,
        )
        self.assertTemplateUsed(response, "shopapp/products_list.html")


class OrdersListViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(
            username="test_name", password="test_password"
        )

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_orders_view(self):
        response = self.client.get(reverse("shopapp:orders_list"))
        self.assertTemplateUsed(response, "shopapp/order_list.html")

    def test_orders_view_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse("shopapp:orders_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(settings.LOGIN_URL), response.url)


class OrderDetailViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.permission_view_order = Permission.objects.get(codename="view_order")
        cls.user = User.objects.create_user(
            username="test_name", password="test_password"
        )
        cls.user.user_permissions.add(cls.permission_view_order)
        cls.product = Product.objects.create(
            name="test_product", description="test_description"
        )

    @classmethod
    def tearDownClass(cls):
        cls.product.delete()
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)
        self.order = Order.objects.create(
            delivery_address="test_address", promocode="test_promocode", user=self.user
        )
        self.order.products.add(self.product)

    def test_order_details(self):
        response = self.client.get(
            reverse("shopapp:order_details", kwargs={"pk": self.order.pk})
        )
        self.assertContains(response, "test_address")
        self.assertContains(response, "test_promocode")
        self.assertEqual(response.context["object"].pk, self.order.pk)


class ProductsExportViewTestCase(TestCase):
    fixtures = ['products-fixture.json', ]

    def setUp(self) -> None:
        Product.objects.create(name="test_product")

    def test_get_products_view(self):
        response = self.client.get(
            reverse("shopapp:products_export"),
        )
        self.assertEqual(response.status_code, 200)
        products = Product.objects.order_by("pk").all()
        expected_data = [
            {
                "pk": product.pk,
                "name": product.name,
                "price": str(product.price),
                "archived": product.archived,
            }
            for product in products
        ]
        self.assertEqual(response.json()["products"], expected_data)


class OrdersExportViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(
            username="test_user", password="test_password", is_staff=True
        )
        cls.product = Product.objects.create(
            name="test_name", description="test_description"
        )

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.product.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)
        self.order = Order.objects.create(
            delivery_address="test_address", promocode="test_promo", user=self.user
        )
        self.order.products.add(self.product)

    def tearDown(self) -> None:
        self.order.delete()

    def test_get_orders_view(self):
        response = self.client.get(
            reverse("shopapp:orders_export"),
        )
        self.assertEqual(response.status_code, 200)
        orders = Order.objects.order_by("pk").all()
        expected_data = [
            {
                "pk": order.pk,
                "delivery_address": order.delivery_address,
                "promocode": order.promocode,
                "user": order.user.username,
                "products": str([product.pk for product in order.products.all()]),
            }
            for order in orders
        ]
        orders_data = response.json()
        self.assertEqual(orders_data["orders"], expected_data)
        self.assertEqual(response.status_code, 200)

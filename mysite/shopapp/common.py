from csv import DictReader
from io import TextIOWrapper

from shopapp.models import Product, Order


def save_csv_products(file, encoding):
    csv_file = TextIOWrapper(
        file,
        encoding=encoding,
    )
    reader = DictReader(csv_file)

    products = [
        Product(**row)
        for row in reader
    ]
    Product.objects.bulk_create(products)
    return products


def save_csv_orders(file, encoding):
    csv_file = TextIOWrapper(
        file,
        encoding=encoding,
    )
    reader = DictReader(csv_file)

    orders = [
        Order(**row)
        for row in reader
    ]
    for order in orders:
        parameters = {
            "delivery_address": order.delivery_address,
            "promocode": order.promocode,
            "user": order.user,
        }
        _order = Order.objects.create(**parameters)
        for pr_id in order.products.split(" "):
            _order.products.add(pr_id)
        _order.save()

    return orders

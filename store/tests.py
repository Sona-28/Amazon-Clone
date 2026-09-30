from django.test import Client, TestCase
from django.urls import reverse

from .models import Category, Product


class DatabaseConnectionTests(TestCase):
    def test_postgres_write_and_read(self):
        category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Audio and accessories",
        )
        product = Product.objects.create(
            category=category,
            name="Wireless Headphones",
            slug="wireless-headphones",
            price="79.99",
        )

        loaded = Product.objects.select_related("category").get(pk=product.pk)
        self.assertEqual(loaded.name, "Wireless Headphones")
        self.assertEqual(loaded.category.slug, "electronics")
        self.assertEqual(Category.objects.count(), 1)


class PageRoutingTests(TestCase):
    def test_named_routes_return_pages(self):
        client = Client()
        expected = {
            "home": "/",
            "categories": "/categories/",
            "auth": "/auth/",
            "cart": "/cart/",
        }
        for name, path in expected.items():
            self.assertEqual(reverse(name), path)
            response = client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

    def test_auth_post_stays_on_auth_page(self):
        response = Client().post(reverse("auth"), {"panel": "register"})
        self.assertEqual(response.status_code, 302)
        follow = Client().post(reverse("auth"), {"panel": "forgot"}, follow=True)
        self.assertEqual(follow.status_code, 200)
        self.assertContains(follow, "wireframe")

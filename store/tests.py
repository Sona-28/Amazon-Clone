from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Cart, CartItem, Category, Product


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


class CatalogPageTests(TestCase):
    def test_pages_render_database_records(self):
        category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Audio, phones, and accessories",
        )
        product = Product.objects.create(
            category=category,
            name="Wireless Headphones",
            slug="wireless-headphones",
            description="Over-ear sound",
            price="79.99",
            image="img/headphones.svg",
            is_active=True,
        )
        client = Client()
        session = client.session
        session.save()
        cart = Cart.objects.create(session_key=client.session.session_key)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        home = client.get(reverse("home"))
        categories = client.get(reverse("categories"))
        cart_page = client.get(reverse("cart"))
        other_visitor = Client().get(reverse("home"))

        self.assertContains(home, "Wireless Headphones")
        self.assertContains(home, "Electronics")
        self.assertContains(home, 'class="cart-count">1<')
        self.assertContains(categories, "Audio, phones, and accessories")
        self.assertContains(cart_page, "159.98")
        self.assertContains(cart_page, 'class="cart-count">1<')
        self.assertContains(other_visitor, 'class="cart-count">0<')


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


class AddToCartTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            category=category,
            name="Wireless Headphones",
            slug="wireless-headphones",
            price="79.99",
            stock=3,
            is_active=True,
        )
        self.url = reverse("product_detail", kwargs={"product_slug": self.product.slug})

    def test_out_of_stock_is_rejected(self):
        self.product.stock = 0
        self.product.save(update_fields=["stock"])

        response = Client().post(self.url, {"quantity": 1})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_guest_cart_is_stored_on_the_session(self):
        client = Client()
        response = client.post(self.url, {"quantity": 2})

        self.assertRedirects(response, reverse("cart"))
        session_key = client.session.session_key
        item = CartItem.objects.select_related("cart").get()
        self.assertEqual(item.quantity, 2)
        self.assertIsNone(item.cart.user)
        self.assertEqual(item.cart.session_key, session_key)

        client.post(self.url, {"quantity": 1})
        item.refresh_from_db()
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(Cart.objects.filter(session_key=session_key).count(), 1)

    def test_authenticated_cart_is_stored_on_the_user(self):
        user = User.objects.create_user(username="shopper@example.com", password="secret-pass")
        client = Client()
        client.force_login(user)

        response = client.post(self.url, {"quantity": 1})

        self.assertRedirects(response, reverse("cart"))
        item = CartItem.objects.select_related("cart").get()
        self.assertEqual(item.cart.user, user)
        self.assertEqual(item.quantity, 1)

        client.post(self.url, {"quantity": 1})
        item.refresh_from_db()
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(Cart.objects.filter(user=user).count(), 1)

    def test_quantity_cannot_exceed_stock(self):
        response = Client().post(self.url, {"quantity": 4})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_existing_quantity_cannot_exceed_stock(self):
        client = Client()
        client.post(self.url, {"quantity": 2})

        response = client.post(self.url, {"quantity": 2})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)
        self.assertEqual(CartItem.objects.get().quantity, 2)

    def test_invalid_quantity_is_rejected(self):
        response = Client().post(self.url, {"quantity": "abc"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)
        self.assertEqual(CartItem.objects.count(), 0)

from decimal import Decimal

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

FEATURED_PRODUCTS = [
    {
        "name": "Wireless Headphones",
        "price": Decimal("79.99"),
        "image": "img/headphones.svg",
        "category": "Electronics",
        "blurb": "Over-ear sound with all-day comfort.",
    },
    {
        "name": "Steel Water Bottle",
        "price": Decimal("24.50"),
        "image": "img/bottle.svg",
        "category": "Home",
        "blurb": "Keeps drinks cold for hours.",
    },
    {
        "name": "Everyday Runners",
        "price": Decimal("89.00"),
        "image": "img/shoes.svg",
        "category": "Fashion",
        "blurb": "Lightweight shoes for daily miles.",
    },
    {
        "name": "Desk Lamp",
        "price": Decimal("34.99"),
        "image": "img/lamp.svg",
        "category": "Home",
        "blurb": "Warm light for a focused workspace.",
    },
]

CATEGORIES = [
    {"name": "Electronics", "detail": "Audio, phones, and accessories", "tone": "navy"},
    {"name": "Home", "detail": "Kitchen, lighting, and living", "tone": "teal"},
    {"name": "Fashion", "detail": "Shoes, basics, and outerwear", "tone": "clay"},
    {"name": "Sports", "detail": "Training gear and outdoors", "tone": "green"},
    {"name": "Books", "detail": "Fiction, study, and hobbies", "tone": "gold"},
    {"name": "Beauty", "detail": "Skin, hair, and everyday care", "tone": "rose"},
]

PLACEHOLDER_CART = [
    {
        "name": "Wireless Headphones",
        "price": Decimal("79.99"),
        "quantity": 1,
        "image": "img/headphones.svg",
    },
    {
        "name": "Steel Water Bottle",
        "price": Decimal("24.50"),
        "quantity": 2,
        "image": "img/bottle.svg",
    },
]


def _cart_context():
    items = []
    subtotal = Decimal("0.00")
    for item in PLACEHOLDER_CART:
        line_total = item["price"] * item["quantity"]
        subtotal += line_total
        items.append({**item, "line_total": line_total})
    return {"cart_items": items, "subtotal": subtotal, "total": subtotal}


def home(request):
    return render(
        request,
        "store/home.html",
        {"featured_products": FEATURED_PRODUCTS, "categories": CATEGORIES[:4]},
    )


def categories(request):
    return render(request, "store/categories.html", {"categories": CATEGORIES})


def auth_page(request):
    panel = request.POST.get("panel") or request.GET.get("panel") or "sign-in"
    if panel not in {"sign-in", "register", "forgot"}:
        panel = "sign-in"

    if request.method == "POST":
        messages.info(
            request,
            "This form is a wireframe. Sign-in and registration arrive in a later phase.",
        )
        return redirect(f"{reverse('auth')}?panel={panel}")

    return render(request, "store/auth.html", {"panel": panel})


def cart(request):
    return render(request, "store/cart.html", _cart_context())

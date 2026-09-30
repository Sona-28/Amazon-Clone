from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db import transaction

from .models import CartItem, Category, Order, OrderItem, Product, Cart, Address


def home(request):
    featured_products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .order_by("-created_at")[:8]
    )
    return render(
        request,
        "store/home.html",
        {
            "featured_products": featured_products,
            "categories": Category.objects.all()[:4],
        },
    )


def categories(request):
    return render(
        request,
        "store/categories.html",
        {"categories": Category.objects.all()},
    )

def category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = (Product.objects.filter(category=category, is_active=True)
                .select_related("category")
                .order_by("-created_at"))
    return render(
        request,
        "store/category_products.html",
        {"category": category, "products": products},
    )
    

def auth_page(request):
    panel = (request.POST.get("panel") or request.GET.get("panel") or "sign-in")
    if panel not in {"sign-in", "register", "forgot"}:
        panel = "sign-in"

    if request.method == "POST":
        if panel == "register":
            name = request.POST.get("name","").strip()
            email = request.POST.get("email", "").strip().lower()
            password = request.POST.get("password", "")

            if not name or not email or not password:
                messages.error(
                    request, "Please fill all the required fields"
                )
                return redirect(f"{reverse('auth')}?panel={panel}")
            
            if User.objects.filter(email=email).exists():
                messages.error(
                    request, "A user with this email already exists"
                )
                return redirect(f"{reverse('auth')}?panel={panel}")
            
            user = User.objects.create_user(username=email, email=email, password=password)
            user.first_name = name
            user.save()
            messages.success(
                request, "Account created successfully"
            )
            return redirect(f"{reverse('auth')}?panel={panel}")
        elif panel == "sign-in":
            email = request.POST.get("email", "").strip().lower()
            password = request.POST.get("password", "")
            user = authenticate(request, username=email, password=password)
            if user is None:
                messages.error(
                    request, "Invalid email or password"
                )
                return redirect(f"{reverse('auth')}?panel={panel}")
            
            login(request, user)
            messages.success(
                request, f"Welcome back, {user.first_name or user.username}."
            )
            return redirect("home")
        elif panel == "forgot":
            messages.info(
                request,
                "Password reset will be implemented in the next authentication phase.",
            )

            return redirect(
                f"{reverse('auth')}?panel=forgot"
            )


    return render(request, "store/auth.html", {"panel": panel})

def logout_user(request):
    logout(request)

    messages.success(
        request,
        "You have been signed out.",
    )

    return redirect("home")

def cart(request):
    if request.user.is_authenticated:
        cart_obj = Cart.objects.filter(user=request.user).order_by("-updated_at").first()
        if cart_obj is None:
            cart_obj = Cart.objects.create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart_obj).order_by("id")
        subtotal = Decimal("0.00")
        for item in cart_items:
            item.line_total = item.product.price * item.quantity
            subtotal += item.line_total
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart_obj = Cart.objects.filter(session_key=session_key, user__isnull=True).order_by("-updated_at").first()
        if cart_obj is None:
            cart_obj = Cart.objects.create(session_key=session_key)
        cart_items = CartItem.objects.filter(cart=cart_obj).order_by("id")
        subtotal = Decimal("0.00")
        for item in cart_items:
            item.line_total = item.product.price * item.quantity
            subtotal += item.line_total
    return render(
        request,
        "store/cart.html",
        {"cart_items": cart_items, "subtotal": subtotal, "total": subtotal}
    )

def update_cart(request, cart_item_id):
    if request.method != "POST":
        return redirect("cart")

    cart_item = get_object_or_404(
        CartItem.objects.select_related("cart", "product"),
        id=cart_item_id,
    )

    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            return redirect("cart")
    else:
        session_key = request.session.session_key

        if (
            not session_key
            or cart_item.cart.user is not None
            or cart_item.cart.session_key != session_key
        ):
            return redirect("cart")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        messages.error(request, "Invalid quantity.")
        return redirect("cart")

    if quantity <= 0:
        cart_item.delete()
        return redirect("cart")

    if quantity > cart_item.product.stock:
        messages.error(
            request,
            f"Only {cart_item.product.stock} units of "
            f"{cart_item.product.name} are available.",
        )
        return redirect("cart")

    cart_item.quantity = quantity
    cart_item.save()

    return redirect("cart")


def remove_from_cart(request, cart_item_id):
    if request.method != "POST":
        return redirect("cart")

    cart_item = get_object_or_404(
        CartItem.objects.select_related("cart", "product"),
        id=cart_item_id,
    )
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            return redirect("cart")
    else:
        session_key = request.session.session_key

        if (
            not session_key
            or cart_item.cart.user is not None
            or cart_item.cart.session_key != session_key
        ):
            return redirect("cart")

    product_name = cart_item.product.name

    cart_item.delete()

    messages.success(
        request,
        f"{product_name} was removed from your cart.",
    )

    return redirect("cart")

def checkout(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in before proceeding to checkout.")
        return redirect(f"{reverse('auth')}?panel=sign-in")

    cart_obj = Cart.objects.filter(user=request.user).first()

    if not cart_obj:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    cart_items = list(
        cart_obj.items.select_related("product").order_by("id")
    )

    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    subtotal = Decimal("0.00")

    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(
                request,
                f"Not enough stock available for {item.product.name}.",
            )
            return redirect("cart")

        item.line_total = item.product.price * item.quantity
        subtotal += item.line_total
    
    addresses = Address.objects.filter(user=request.user).order_by("-is_default", "created_at")
    default_address = addresses.filter(is_default=True).first()

    if request.method == "POST":

        payment_method = request.POST.get("payment_method")
        address_id = request.POST.get("address_id")

        if payment_method != "cod":
            messages.error(request, "Please select Cash on Delivery.")
            return redirect("checkout")

        if not address_id:
            messages.error(request, "Please select a shipping address.")
            return redirect("checkout")
        
        address = get_object_or_404(Address, id=address_id, user=request.user)

        with transaction.atomic():

            for item in cart_items:
                product = Product.objects.select_for_update().get(
                    id=item.product.id
                )

                if item.quantity > product.stock:
                    messages.error(
                        request,
                        f"Only {product.stock} units of "
                        f"{product.name} are available.",
                    )
                    return redirect("cart")

            order = Order.objects.create(
                user=request.user,
                status=Order.Status.PLACED,
                total_price=Decimal(subtotal),
                shipping_full_name=address.full_name,
                shipping_phone=address.phone,
                shipping_address_line_1=address.address_line_1,
                shipping_address_line_2=address.address_line_2,
                shipping_city=address.city,
                shipping_state=address.state,
                shipping_postal_code=address.postal_code,
                shipping_country=address.country,
            )

            for item in cart_items:

                product = Product.objects.select_for_update().get(
                    id=item.product.id
                )

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    unit_price=product.price,
                )

                product.stock -= item.quantity
                product.save(update_fields=["stock"])

            cart_obj.items.all().delete()

        messages.success(
            request,
            f"Order #{order.id} placed successfully with Cash on Delivery.",
        )

        return redirect("order_success", order_id=order.id)

    return render(
        request,
        "store/checkout.html",
        {
            "cart_items": cart_items,
            "subtotal": subtotal,
            "total": subtotal,
            "payment_method": "cod",
            "addresses": addresses,
            "default_address": default_address,
        },
    )

def add_address(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('auth')}?panel=sign-in")

    if request.method != "POST":
        return redirect("checkout")

    full_name = (request.POST.get("full_name") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    address_line_1 = (request.POST.get("address_line_1") or "").strip()
    address_line_2 = (request.POST.get("address_line_2") or "").strip()
    city = (request.POST.get("city") or "").strip()
    state = (request.POST.get("state") or "").strip()
    postal_code = (request.POST.get("postal_code") or "").strip()
    country = (request.POST.get("country") or "").strip()
    is_default = request.POST.get("is_default") == "on"

    if not all([full_name, phone, address_line_1, city, state, postal_code, country]):
        messages.error(request, "Please fill all the required fields.")
        return redirect("checkout")
    
    if not Address.objects.filter(user=request.user).exists():
        is_default = True
    if is_default:
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    Address.objects.create(user=request.user, full_name=full_name, phone=phone, address_line_1=address_line_1, address_line_2=address_line_2, city=city, state=state, postal_code=postal_code, country=country, is_default=is_default)
    messages.success(request, "Address added successfully.")
    return redirect(f"{reverse('checkout')}?success=true")

def edit_address(request, address_id):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('auth')}?panel=sign-in")

    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method != "POST":
        return redirect("checkout")
    
    full_name = request.POST.get("full_name")
    phone = request.POST.get("phone")
    address_line_1 = request.POST.get("address_line_1")
    address_line_2 = request.POST.get("address_line_2")
    city = request.POST.get("city")
    state = request.POST.get("state")
    postal_code = request.POST.get("postal_code")
    country = request.POST.get("country")
    is_default = request.POST.get("is_default") == "on"

    if not address_line_1 or not city or not state or not postal_code or not country:
        messages.error(request, "Please fill all the required fields.")
        return redirect("checkout")
    
    address.full_name = full_name
    address.phone = phone
    address.address_line_1 = address_line_1
    address.address_line_2 = address_line_2
    address.city = city
    address.state = state
    address.postal_code = postal_code
    address.country = country
    address.is_default = is_default
    address.save()
    messages.success(request, "Address updated successfully.")
    return redirect(f"{reverse('checkout')}?success=true")

def delete_address(request, address_id):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('auth')}?panel=sign-in")

    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, "Address deleted successfully.")
    return redirect(f"{reverse('checkout')}?success=true")

def set_default_address(request, address_id):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('auth')}?panel=sign-in")

    address = get_object_or_404(Address, id=address_id, user=request.user)
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, "Address set as default successfully.")
    return redirect(f"{reverse('checkout')}?success=true")

def _order_items(order):
    items = list(order.items.all())
    for item in items:
        item.line_total = item.unit_price * item.quantity
    return items


def orders(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in to view your orders.")
        return redirect(f"{reverse('auth')}?panel=sign-in")

    user_orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )
    for order in user_orders:
        order.display_items = _order_items(order)

    return render(request, "store/orders.html", {"orders": user_orders})


def order_detail(request, order_id):
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in to view your orders.")
        return redirect(f"{reverse('auth')}?panel=sign-in")

    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
        user=request.user,
    )
    return render(
        request,
        "store/order_detail.html",
        {"order": order, "order_items": _order_items(order)},
    )


def order_success(request, order_id):
    if not request.user.is_authenticated:
        return redirect("home")

    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
        user=request.user,
    )
    order_items = _order_items(order)

    return render(
        request,
        "store/order_success.html",
        {"order": order, "order_items": order_items},
    )

def product_detail(request, product_slug):
    product = get_object_or_404(
        Product.objects.select_related("category"),
        slug=product_slug,
        is_active=True,
    )
    if request.method == "POST":
        raw_quantity = request.POST.get("quantity", "1")
        try:
            quantity = int(raw_quantity)
        except (TypeError, ValueError):
            messages.error(request, "Please enter a valid quantity.")
            return redirect("product_detail", product_slug=product.slug)

        if quantity < 1:
            messages.error(request, "Please enter a quantity of at least 1.")
            return redirect("product_detail", product_slug=product.slug)

        if product.stock <= 0:
            messages.error(request, "This product is currently out of stock.")
            return redirect("product_detail", product_slug=product.slug)

        if quantity > product.stock:
            messages.error(
                request,
                f"Only {product.stock} units of this product are available.",
            )
            return redirect("product_detail", product_slug=product.slug)

        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).order_by("-updated_at").first()
            if cart is None:
                cart = Cart.objects.create(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            cart = (
                Cart.objects.filter(session_key=session_key, user__isnull=True)
                .order_by("-updated_at")
                .first()
            )
            if cart is None:
                cart = Cart.objects.create(session_key=session_key)

        item = CartItem.objects.filter(cart=cart, product=product).first()
        if item is not None:
            new_quantity = item.quantity + quantity
            if new_quantity > product.stock:
                remaining = product.stock - item.quantity
                if remaining == 0:
                    messages.error(
                        request,
                        f"You already have {item.quantity} in your cart. "
                        f"This product is out of stock.",
                    )
                    return redirect("product_detail", product_slug=product.slug)
                else:
                    item.quantity = remaining
                    item.save(update_fields=["quantity"])
                    messages.success(request, f"Only {remaining} more {product.name} can be added ({product.stock} in stock).")
                    return redirect("product_detail", product_slug=product.slug)
            item.quantity = new_quantity
            item.save(update_fields=["quantity"])
        else:
            CartItem.objects.create(cart=cart, product=product, quantity=quantity)

        cart.save()
        messages.success(request, f"{product.name} was added to your cart.")
        return redirect("cart")

    return render(
        request,
        "store/product_detail.html",
        {"product": product},
    )
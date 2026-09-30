from .models import Cart


def cart_summary(request):
    cart = None
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        cart = Cart.objects.filter(user=user).order_by("-updated_at").first()
    else:
        session = getattr(request, "session", None)
        session_key = getattr(session, "session_key", None)
        if session_key:
            cart = (
                Cart.objects.filter(session_key=session_key, user__isnull=True)
                .order_by("-updated_at")
                .first()
            )
    count = cart.items.count() if cart is not None else 0
    return {"cart_count": count}

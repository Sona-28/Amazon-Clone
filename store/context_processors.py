from .views import PLACEHOLDER_CART


def cart_summary(request):
    return {"cart_count": len(PLACEHOLDER_CART)}

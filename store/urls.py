from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("categories/", views.categories, name="categories"),
    path("categories/<slug:category_slug>/", views.category_products, name="category_products"),
    path("auth/", views.auth_page, name="auth"),
    path("logout/", views.logout_user, name="logout"),
    path("cart/", views.cart, name="cart"),
    path("cart/update/<int:cart_item_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:cart_item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("products/<slug:product_slug>/", views.product_detail, name="product_detail"),
    path("checkout/", views.checkout, name="checkout"),
    path("add-address/", views.add_address, name="add_address"),
    path("set-default-address/<int:address_id>/", views.set_default_address, name="set_default_address"),
    path("delete-address/<int:address_id>/", views.delete_address, name="delete_address"),
    path("order-success/<int:order_id>/", views.order_success, name="order_success"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
]

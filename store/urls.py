from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("categories/", views.categories, name="categories"),
    path("auth/", views.auth_page, name="auth"),
    path("cart/", views.cart, name="cart"),
]

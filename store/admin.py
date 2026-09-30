from django.contrib import admin
from .models import Cart, CartItem, Category, Order, OrderItem, Product, Address


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "stock",
        "is_active",
        "created_at",
    )

    list_filter = (
        "category",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }

    list_editable = (
        "price",
        "stock",
        "is_active",
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "session_key",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "session_key",
        "user__username",
        "user__email",
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "cart",
        "product",
        "quantity",
    )

    search_fields = (
        "product__name",
        "cart__user__username",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "total_price",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "quantity",
        "unit_price",
    )

    search_fields = (
        "product__name",
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "full_name",
        "phone",
        "address_line_1",
        "city",
        "state",
        "postal_code",
        "country",
        "is_default",
    )
    list_filter = (
        "is_default",
        "country",
    )
    search_fields = (
        "user__username",
        "user__email",
        "address_line_1",
        "city",
        "state",
        "postal_code",
        "country",
    )

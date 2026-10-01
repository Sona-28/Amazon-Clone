# Amazone

Amazone is a Django storefront. Shoppers browse products, keep a cart, sign in, save a delivery address, and place a cash-on-delivery order. Signed-in shoppers can open their past orders. Staff manage the catalog from Django admin.

Prices are stored as decimals on each product. The catalog and cart show them with `$`. Checkout and the order history show them with `£`.

## Run it locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py loaddata store_data.json
python manage.py runserver
```

`store_data.json` loads categories and products. Create an admin account with `python manage.py createsuperuser`, then open `/admin/`.

Local PostgreSQL settings live in `.env` (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`). Do not commit `.env`.

## Home

`/` shows the eight newest active products and the first four categories. Each product card links to its detail page. A category card links to that category.

## Categories

`/categories/` lists every category. `/categories/<slug>/` lists the active products in that category, newest first. Inactive products stay hidden. An unknown slug returns a 404.

## Product detail

`/products/<slug>/` shows the name, description, price, image, and how many units are in stock. A missing image is shown as a placeholder.

If the product is in stock, the page has an add-to-cart form. The quantity must be at least 1 and cannot be higher than the stock. Adding the same product again increases the quantity already in the cart, still capped by stock. Out-of-stock products cannot be added.

## Cart

`/cart/` lists the current cart with a photo, name, price, quantity, line total, subtotal, and total. Shipping is not calculated.

Guests get a cart stored against their session. Signed-in shoppers get a cart stored against their account. These carts stay separate. Signing in does not copy the guest cart over.

The quantity buttons post to `/cart/update/<id>/`. Setting the quantity to 0 removes the line. A quantity above stock is rejected. Remove posts to `/cart/remove/<id>/`. Both actions only change a line that belongs to the current user or guest session.

The cart count in the header is the number of lines in that cart.

## Accounts

`/auth/` has three panels.

**Sign in** checks the email and password. The email is stored as the username. A successful sign-in goes to the home page.

**Register** needs a name, email, and password. The name is saved as the first name. A duplicate email is rejected. After registration the shopper stays on the sign-in panel and signs in separately.

**Forgot password** only shows a message. Password reset is not built yet.

**Sign out** is `/logout/`. It ends the session and returns to the home page. The header and footer show Sign In for guests, and Sign Out plus Orders for signed-in shoppers.

## Checkout

`/checkout/` is only for a signed-in shopper with items in the cart. Guests are sent to sign in. An empty cart is sent back to the cart page.

The page shows the order lines, a saved shipping address, cash on delivery, and the total. Place Order stays disabled until an address exists. If any line asks for more units than are in stock, checkout sends the shopper back to the cart.

**Add address** opens a form for name, phone, two address lines, city, state, postal code, and country. The first address for an account is saved as the default. A later address can be marked default, which clears the previous default. **Set as default** does the same from the address list. The chosen address is selected with a radio button, and the default address starts selected.

Placing the order requires cash on delivery and one of the shopper’s own addresses. Inside a database transaction the app checks stock again, creates the order with status Placed, copies the address onto the order, saves each line at the current unit price, reduces stock, and empties the cart. The shopper then lands on `/order-success/<id>/`, which shows the items, status, payment method, and total.

## Orders

**Orders** appears in the header and footer only after sign-in. `/orders/` lists that account’s orders, newest first. Each card shows the order number, date, status, line items, and total, and links to `/orders/<id>/`.

The detail page shows every item with its price and quantity, the delivery address saved on the order, the status, cash on delivery, the date, and the total. One shopper cannot open another shopper’s order.

## Admin

`/admin/` is Django admin. Staff can manage:

- **Categories** — name, slug, and description. The slug fills in from the name.
- **Products** — category, price, stock, active flag, description, and image. The image field is a URL or a static path. Price, stock, and active can be edited from the list.
- **Carts and cart items** — guest session carts and signed-in carts.
- **Orders and order items** — status, totals, shipping fields, and lines.
- **Addresses** — saved delivery addresses, including which one is the default.

## Deploy on Render

`render.yaml` creates a web service and a PostgreSQL database. The build installs dependencies, collects static files, runs migrations, and loads `store_data.json`. Gunicorn serves the app. WhiteNoise serves CSS and JavaScript.

1. Push this repo to GitHub or GitLab.
2. In Render, choose **New** → **Blueprint** and select the repo.
3. Render generates `SECRET_KEY`, sets `DEBUG=False`, and connects `DATABASE_URL`.
4. After the first deploy, open the Render shell and run `python manage.py createsuperuser`.

When `DATABASE_URL` is set, Django uses it. Local runs keep using the `DB_*` values in `.env`. Set `DB_SSL=True` only for Render’s external database URL. The internal URL from the blueprint does not need it.

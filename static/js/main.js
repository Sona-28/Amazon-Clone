document.documentElement.dataset.js = "ready";

const toggle = document.querySelector(".nav-toggle");
const nav = document.querySelector(".site-nav");

if (toggle && nav) {
  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
  });
}

function money(value) {
  return `$${value.toFixed(2)}`;
}

function refreshCart() {
  const items = [...document.querySelectorAll(".cart-item")];
  let subtotal = 0;

  items.forEach((item) => {
    const line = Number(item.dataset.price) * Number(item.dataset.qty);
    subtotal += line;
    const lineTotal = item.querySelector(".line-total");
    const quantity = item.querySelector(".qty-value");
    if (lineTotal) lineTotal.textContent = money(line);
    if (quantity) quantity.textContent = item.dataset.qty;
  });

  const subtotalNode = document.querySelector("[data-subtotal]");
  const totalNode = document.querySelector("[data-total]");
  if (subtotalNode) subtotalNode.textContent = money(subtotal);
  if (totalNode) totalNode.textContent = money(subtotal);

  const count = document.querySelector(".cart-count");
  if (count && document.querySelector(".cart-layout")) {
    count.textContent = String(items.length);
  }

  const empty = document.querySelector(".cart-empty");
  const layout = document.querySelector(".cart-layout");
  if (empty && layout) {
    empty.hidden = items.length > 0;
    layout.hidden = items.length === 0;
  }
}

document.querySelectorAll(".cart-item").forEach((item) => {
  item.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;

    if (button.hasAttribute("data-remove")) {
      item.remove();
      refreshCart();
      return;
    }

    const delta = Number(button.dataset.qty || 0);
    if (!delta) return;
    const next = Math.max(1, Number(item.dataset.qty) + delta);
    item.dataset.qty = String(next);
    refreshCart();
  });
});

const checkout = document.querySelector("[data-checkout]");
const notice = document.querySelector("[data-checkout-notice]");
if (checkout && notice) {
  checkout.addEventListener("click", () => {
    notice.hidden = false;
  });
}

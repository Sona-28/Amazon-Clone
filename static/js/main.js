document.documentElement.dataset.js = "ready";

const toggle = document.querySelector(".nav-toggle");
const nav = document.querySelector(".site-nav");

if (toggle && nav) {
  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
  });
}

const checkout = document.querySelector("[data-checkout]");
const notice = document.querySelector("[data-checkout-notice]");
if (checkout && notice) {
  checkout.addEventListener("click", () => {
    notice.hidden = false;
  });
}

const addressModal = document.getElementById("address-modal");
const openAddressModal = document.getElementById("open-address-modal");
const closeAddressModal = document.getElementById("close-address-modal");

if (addressModal && openAddressModal) {

    function openModal() {
        addressModal.hidden = false;
        addressModal.setAttribute("aria-hidden", "false");

        document.body.classList.add("modal-open");

        const firstInput = addressModal.querySelector("input");

        if (firstInput) {
            firstInput.focus();
        }
    }

    function closeModal() {
        addressModal.hidden = true;
        addressModal.setAttribute("aria-hidden", "true");

        document.body.classList.remove("modal-open");
    }

    openAddressModal.addEventListener("click", openModal);

    if (closeAddressModal) {
        closeAddressModal.addEventListener("click", closeModal);
    }

    addressModal
        .querySelectorAll("[data-close-address-modal]")
        .forEach((element) => {
            element.addEventListener("click", closeModal);
        });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !addressModal.hidden) {
            closeModal();
        }
    });
}
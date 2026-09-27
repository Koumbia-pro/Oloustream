/* Oloustream — comportements communs (site public, espaces client et partenaire, dashboard) */
(function () {
    "use strict";

    // Menus déroulants : [data-toggle-panel="id"] ouvre/ferme #id
    function closeAllPanels(except) {
        document.querySelectorAll("[data-toggle-panel]").forEach(function (btn) {
            var panel = document.getElementById(btn.getAttribute("data-toggle-panel"));
            if (panel && panel !== except) {
                panel.classList.remove("open");
                btn.setAttribute("aria-expanded", "false");
            }
        });
    }

    document.addEventListener("click", function (event) {
        var toggle = event.target.closest("[data-toggle-panel]");
        if (toggle) {
            event.preventDefault();
            var panel = document.getElementById(toggle.getAttribute("data-toggle-panel"));
            if (!panel) return;
            var willOpen = !panel.classList.contains("open");
            closeAllPanels(panel);
            panel.classList.toggle("open", willOpen);
            toggle.setAttribute("aria-expanded", willOpen ? "true" : "false");
            return;
        }
        if (!event.target.closest(".mega, .dropdown-panel")) closeAllPanels(null);
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeAllPanels(null);
            closeDrawer();
        }
    });

    // Menu mobile
    var drawer = document.getElementById("mobile-drawer");
    function openDrawer() {
        if (!drawer) return;
        drawer.classList.add("open");
        document.body.style.overflow = "hidden";
    }
    function closeDrawer() {
        if (!drawer) return;
        drawer.classList.remove("open");
        document.body.style.overflow = "";
    }
    document.querySelectorAll("[data-drawer-open]").forEach(function (el) { el.addEventListener("click", openDrawer); });
    document.querySelectorAll("[data-drawer-close]").forEach(function (el) { el.addEventListener("click", closeDrawer); });

    // Barre latérale du dashboard (mobile)
    document.querySelectorAll("[data-sidebar-open]").forEach(function (el) {
        el.addEventListener("click", function () { document.body.classList.add("sidebar-open"); });
    });
    document.querySelectorAll("[data-sidebar-close]").forEach(function (el) {
        el.addEventListener("click", function () { document.body.classList.remove("sidebar-open"); });
    });

    // Ombre de l'en-tête au défilement
    var header = document.querySelector(".site-header");
    if (header) {
        var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 8); };
        onScroll();
        window.addEventListener("scroll", onScroll, { passive: true });
    }

    // Afficher / masquer un mot de passe
    document.addEventListener("click", function (event) {
        var btn = event.target.closest(".toggle-pw");
        if (!btn) return;
        var input = btn.parentElement.querySelector("input");
        if (!input) return;
        var show = input.type === "password";
        input.type = show ? "text" : "password";
        btn.setAttribute("aria-label", show ? "Masquer le mot de passe" : "Afficher le mot de passe");
        var icon = btn.querySelector("i");
        if (icon) icon.className = show ? "fa-regular fa-eye-slash" : "fa-regular fa-eye";
    });

    // Confirmation avant une action sensible : <form data-confirm="Message ?">
    document.addEventListener("submit", function (event) {
        var form = event.target;
        var message = form.getAttribute("data-confirm");
        if (message && !window.confirm(message)) {
            event.preventDefault();
            return;
        }
        // Évite les doubles envois
        var submit = form.querySelector("[type=submit]:not([data-no-lock])");
        if (submit && !form.hasAttribute("data-no-lock")) {
            setTimeout(function () { submit.disabled = true; }, 0);
        }
    });

    // Disparition automatique des messages de succès
    document.querySelectorAll(".alert[data-autohide]").forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = "opacity .4s";
            alert.style.opacity = "0";
            setTimeout(function () { alert.remove(); }, 400);
        }, 6000);
    });

    // Aperçu d'image avant envoi : <input type="file" data-preview="#img">
    document.addEventListener("change", function (event) {
        var input = event.target;
        if (!input.matches("input[type=file][data-preview]")) return;
        var target = document.querySelector(input.getAttribute("data-preview"));
        if (!target || !input.files || !input.files[0]) return;
        if (!input.files[0].type.startsWith("image/")) return;
        target.src = URL.createObjectURL(input.files[0]);
        target.hidden = false;
    });
})();

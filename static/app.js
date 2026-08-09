const root = document.documentElement;
const themeButton = document.querySelector("[data-theme-toggle]");
const languageSelects = document.querySelectorAll("[data-language-select]");
const menu = document.querySelector("#mobile-menu");
const menuOpen = document.querySelector("[data-menu-open]");
const menuCloseControls = document.querySelectorAll("[data-menu-close]");
const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
const allowedThemes = new Set(["system", "light", "dark"]);


function localTheme() {
    try {
        const preference = localStorage.getItem("ili-pika-theme") || "system";
        return allowedThemes.has(preference) ? preference : "system";
    } catch (error) {
        return "system";
    }
}


function resolvedTheme(preference) {
    const normalizedPreference = allowedThemes.has(preference)
        ? preference
        : "system";

    if (normalizedPreference === "system") {
        return window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";
    }

    return normalizedPreference;
}


function applyTheme(preference) {
    root.dataset.theme = resolvedTheme(preference);

    if (themeButton) {
        const icon = root.dataset.theme === "dark" ? "sun" : "moon";
        const iconPath = themeButton.querySelector("use");
        if (iconPath) {
            const source = iconPath.getAttribute("href").split("#")[0];
            iconPath.setAttribute("href", `${source}#${icon}`);
        }
    }
}


if (themeButton) {
    themeButton.addEventListener("click", function () {
        const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
        try {
            localStorage.setItem("ili-pika-theme", nextTheme);
        } catch (error) {
            root.dataset.themePreference = nextTheme;
        }
        applyTheme(nextTheme);
    });
}


languageSelects.forEach(function (select) {
    select.addEventListener("change", function () {
        select.form.submit();
    });
});


document.addEventListener("click", function (event) {
    const destructiveControl = event.target.closest("[data-confirm]");
    if (
        destructiveControl
        && !window.confirm(destructiveControl.dataset.confirm)
    ) {
        event.preventDefault();
    }
});


function closeMobileMenu() {
    if (!menu || !menuOpen) {
        return;
    }

    menu.classList.remove("open");
    menu.setAttribute("aria-hidden", "true");
    menuOpen.setAttribute("aria-expanded", "false");
    document.body.classList.remove("menu-open");
    menuCloseControls.forEach(function (control) {
        if (control.classList.contains("mobile-menu-backdrop")) {
            control.hidden = true;
        }
    });
    menuOpen.focus();
}


if (menu && menuOpen) {
    menuOpen.addEventListener("click", function () {
        menu.classList.add("open");
        menu.setAttribute("aria-hidden", "false");
        menuOpen.setAttribute("aria-expanded", "true");
        document.body.classList.add("menu-open");
        menuCloseControls.forEach(function (control) {
            if (control.classList.contains("mobile-menu-backdrop")) {
                control.hidden = false;
            }
        });
        const firstControl = menu.querySelector("button, a");
        if (firstControl) {
            firstControl.focus();
        }
    });

    menuCloseControls.forEach(function (control) {
        control.addEventListener("click", closeMobileMenu);
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && menu.classList.contains("open")) {
            closeMobileMenu();
        }

        if (event.key === "Tab" && menu.classList.contains("open")) {
            const controls = Array.from(
                menu.querySelectorAll("a, button, input, select, textarea, [tabindex]:not([tabindex='-1'])")
            ).filter(function (control) {
                return !control.disabled;
            });
            const first = controls[0];
            const last = controls[controls.length - 1];

            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        }
    });
}


systemTheme.addEventListener("change", function () {
    const preference = root.dataset.authenticated === "true"
        ? root.dataset.themePreference
        : localTheme();
    if (preference === "system") {
        applyTheme("system");
    }
});


applyTheme(
    root.dataset.authenticated === "true"
        ? root.dataset.themePreference
        : localTheme()
);

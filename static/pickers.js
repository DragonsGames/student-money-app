document.addEventListener("click", function (event) {
    const iconToggle = event.target.closest("[data-icon-toggle]");
    if (iconToggle) {
        const picker = iconToggle.closest("[data-icon-picker]");
        const menu = picker.querySelector("[data-icon-menu]");
        const isOpen = !menu.hidden;
        menu.hidden = isOpen;
        iconToggle.setAttribute("aria-expanded", String(!isOpen));
        return;
    }

    const iconChoice = event.target.closest("[data-icon-value]");
    if (iconChoice) {
        const picker = iconChoice.closest("[data-icon-picker]");
        const input = picker.querySelector("input");
        const menu = picker.querySelector("[data-icon-menu]");
        const toggle = picker.querySelector("[data-icon-toggle]");
        input.value = iconChoice.dataset.iconValue;
        picker.querySelectorAll("[data-icon-value]").forEach(function (choice) {
            choice.classList.toggle("selected", choice === iconChoice);
        });
        menu.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
        input.focus();
        return;
    }

    const colorChoice = event.target.closest("[data-color-value]");
    if (colorChoice) {
        const picker = colorChoice.closest("[data-color-picker]");
        const hidden = picker.querySelector('input[type="hidden"]');
        const native = picker.querySelector("[data-color-native]");
        hidden.value = colorChoice.dataset.colorValue;
        native.value = colorChoice.dataset.colorValue;
        picker.querySelectorAll("[data-color-value]").forEach(function (choice) {
            choice.classList.toggle("selected", choice === colorChoice);
        });
    }
});


document.addEventListener("input", function (event) {
    if (!event.target.matches("[data-color-native]")) {
        return;
    }

    const picker = event.target.closest("[data-color-picker]");
    picker.querySelector('input[type="hidden"]').value = event.target.value;
    picker.querySelectorAll("[data-color-value]").forEach(function (choice) {
        choice.classList.toggle(
            "selected",
            choice.dataset.colorValue.toLowerCase() === event.target.value.toLowerCase()
        );
    });
});

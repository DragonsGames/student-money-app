const container = document.getElementById("categories");
const addButton = document.getElementById("add-category");

addButton.addEventListener("click", function () {
    const categories = container.querySelectorAll(".category");

    const newCategory = categories[0].cloneNode(true);
    const newIndex = categories.length;

    newCategory.querySelectorAll("input, select").forEach(function (element) {
        if (element.name) {
            element.name = element.name.replace(
                /categories-\d+-/,
                `categories-${newIndex}-`
            );
        }

        if (element.id) {
            element.id = element.id.replace(
                /categories-\d+-/,
                `categories-${newIndex}-`
            );
        }

        if (element.tagName === "INPUT") {
            element.value = "";
        }

        if (element.tagName === "SELECT") {
            element.selectedIndex = 0;
        }
    });

    container.appendChild(newCategory);
});

container.addEventListener("click", function (event) {
    if (!event.target.classList.contains("remove-category")) {
        return;
    }

    const categories = container.querySelectorAll(".category");

    if (categories.length > 1) {
        event.target.closest(".category").remove();
    }
});
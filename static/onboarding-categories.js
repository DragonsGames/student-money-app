const categoryContainer = document.getElementById("categories");
const addCategoryButton = document.getElementById("add-category");


if (categoryContainer && addCategoryButton) {
    function categoryItems() {
        return Array.from(categoryContainer.querySelectorAll(".category"));
    }

    // AI-assisted: keep WTForms FieldList indexes contiguous after add/remove actions.
    function reindexCategories() {
        const categories = categoryItems();

        categories.forEach(function (category, index) {
            category.querySelectorAll("input, select, label").forEach(function (element) {
                if (element.name) {
                    element.name = element.name.replace(
                        /categories-\d+-/,
                        `categories-${index}-`
                    );
                }

                if (element.id) {
                    element.id = element.id.replace(
                        /categories-\d+-/,
                        `categories-${index}-`
                    );
                }

                if (element.htmlFor) {
                    element.htmlFor = element.htmlFor.replace(
                        /categories-\d+-/,
                        `categories-${index}-`
                    );
                }
            });

            const removeButton = category.querySelector(".remove-category");
            if (removeButton) {
                removeButton.disabled = categories.length === 1;
                removeButton.setAttribute(
                    "aria-label",
                    `Remove category ${index + 1}`
                );
            }
        });
    }

    function clearClonedCategory(category) {
        category.querySelectorAll("input, select").forEach(function (field) {
            field.classList.remove("is-invalid");

            if (field.tagName === "SELECT") {
                field.selectedIndex = 0;
            } else {
                field.value = "";
            }
        });

        category.querySelectorAll(".form-error").forEach(function (error) {
            error.remove();
        });
    }

    addCategoryButton.addEventListener("click", function () {
        const firstCategory = categoryItems()[0];

        if (!firstCategory) {
            return;
        }

        const newCategory = firstCategory.cloneNode(true);
        clearClonedCategory(newCategory);
        categoryContainer.appendChild(newCategory);
        reindexCategories();

        const nameInput = newCategory.querySelector('[name$="-name"]');
        if (nameInput) {
            nameInput.focus();
        }
    });

    categoryContainer.addEventListener("click", function (event) {
        const removeButton = event.target.closest(".remove-category");

        if (!removeButton || categoryItems().length === 1) {
            return;
        }

        removeButton.closest(".category").remove();
        reindexCategories();
    });

    reindexCategories();
}

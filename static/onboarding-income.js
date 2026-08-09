const incomeContainer = document.getElementById("income-sources");
const addSourceButton = document.getElementById("add-source");


if (incomeContainer && addSourceButton) {
    function incomeSources() {
        return Array.from(incomeContainer.querySelectorAll(".income-source"));
    }

    // AI-assisted: keep WTForms FieldList indexes contiguous after add/remove actions.
    function reindexIncomeSources() {
        const sources = incomeSources();

        sources.forEach(function (source, index) {
            source.querySelectorAll("input, select, label").forEach(function (element) {
                if (element.name) {
                    element.name = element.name.replace(
                        /sources-\d+-/,
                        `sources-${index}-`
                    );
                }

                if (element.id) {
                    element.id = element.id.replace(
                        /sources-\d+-/,
                        `sources-${index}-`
                    );
                }

                if (element.htmlFor) {
                    element.htmlFor = element.htmlFor.replace(
                        /sources-\d+-/,
                        `sources-${index}-`
                    );
                }
            });

            const number = source.querySelector(".item-number");
            const removeButton = source.querySelector(".remove-source");

            if (number) {
                number.textContent = index + 1;
            }

            if (removeButton) {
                removeButton.disabled = sources.length === 1;
                removeButton.setAttribute(
                    "aria-label",
                    `${removeButton.dataset.removeLabel} ${index + 1}`
                );
            }
        });
    }

    function clearClonedSource(source) {
        source.querySelectorAll("input, select").forEach(function (field) {
            field.classList.remove("is-invalid");

            if (field.tagName === "SELECT") {
                field.selectedIndex = 0;
            } else {
                field.value = "";
            }
        });

        source.querySelectorAll(".form-error").forEach(function (error) {
            error.remove();
        });
    }

    addSourceButton.addEventListener("click", function () {
        const firstSource = incomeSources()[0];

        if (!firstSource) {
            return;
        }

        const newSource = firstSource.cloneNode(true);
        clearClonedSource(newSource);
        incomeContainer.appendChild(newSource);
        reindexIncomeSources();

        const firstInput = newSource.querySelector("input");
        if (firstInput) {
            firstInput.focus();
        }
    });

    incomeContainer.addEventListener("click", function (event) {
        const removeButton = event.target.closest(".remove-source");

        if (!removeButton || incomeSources().length === 1) {
            return;
        }

        removeButton.closest(".income-source").remove();
        reindexIncomeSources();
    });

    reindexIncomeSources();
}

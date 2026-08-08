// AI assistance: OpenAI Codex assisted with this category filtering behavior;
// reviewed and adapted by the project author.
const transactionType = document.getElementById("transaction_type");
const transactionCategory = document.getElementById("category_id");
const categoryEmptyMessage = document.getElementById("category-empty-message");


if (transactionType && transactionCategory && categoryEmptyMessage) {
    function filterCategories(resetSelection) {
        const selectedType = transactionType.value;
        const categoryOptions = Array.from(
            transactionCategory.querySelectorAll("option[data-category-type]")
        );

        let matchingCount = 0;

        categoryOptions.forEach(function (option) {
            const matches = option.dataset.categoryType === selectedType;
            option.hidden = !matches;
            option.disabled = !matches;

            if (matches) {
                matchingCount += 1;
            }
        });

        const selectedOption = transactionCategory.selectedOptions[0];
        if (
            resetSelection ||
            (selectedOption && selectedOption.dataset.categoryType !== selectedType)
        ) {
            transactionCategory.value = "0";
        }

        transactionCategory.disabled = matchingCount === 0;
        categoryEmptyMessage.hidden = matchingCount !== 0;
    }

    transactionType.addEventListener("change", function () {
        filterCategories(true);
    });

    filterCategories(false);
}

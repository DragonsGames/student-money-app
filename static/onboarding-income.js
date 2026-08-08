const container = document.getElementById("income-sources");
const addButton = document.getElementById("add-source");


addButton.addEventListener("click", function () {

    const sources = container.querySelectorAll(".income-source");

    const firstSource = sources[0];
    const newSource = firstSource.cloneNode(true);

    const newIndex = sources.length;

    newSource.querySelectorAll("input, select, label").forEach(function (element) {

        if (element.name) {
            element.name = element.name.replace(
                /sources-\d+-/,
                `sources-${newIndex}-`
            );
        }

        if (element.id) {
            element.id = element.id.replace(
                /sources-\d+-/,
                `sources-${newIndex}-`
            );
        }

        if (element.htmlFor) {
            element.htmlFor = element.htmlFor.replace(
                /sources-\d+-/,
                `sources-${newIndex}-`
            );
        }

        if (element.tagName === "INPUT") {
            element.value = "";
        }

        if (element.tagName === "SELECT") {
            element.selectedIndex = 0;
        }
    });

    container.appendChild(newSource);
});

container.addEventListener("click", function (event) {

    if (!event.target.classList.contains("remove-source")) {
        return;
    }

    const sources = container.querySelectorAll(".income-source");

    if (sources.length === 1) {
        return;
    }

    event.target.closest(".income-source").remove();
});
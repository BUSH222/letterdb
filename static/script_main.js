function sortTable(n) {
    var table = document.getElementById("MainTable");
    var rows = Array.from(table.rows).slice(1);
    var isNumber = /\d/;
    var sortedRows;
    var sortAscending = true;

    if (table.dataset.sortColumn === n.toString()) {
        sortAscending = table.dataset.sortOrder === "asc" ? false : true;
    }

    sortedRows = rows.sort(function(a, b) {
        var aValue = a.cells[n].innerText || a.cells[n].textContent;
        var bValue = b.cells[n].innerText || b.cells[n].textContent;

        // numeric: true sorts catalogue numbers as numbers (2 before 10)
        var order = aValue.localeCompare(bValue, "ru", { numeric: true });
        return sortAscending ? order : -order;

    });

    while (table.rows.length > 1) {
        table.deleteRow(1);
    }

    for (var row of sortedRows) {
        table.tBodies[0].appendChild(row);
    }

    table.dataset.sortColumn = n.toString();
    table.dataset.sortOrder = sortAscending ? "asc" : "desc";
}

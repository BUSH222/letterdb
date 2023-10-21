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

        if (isNumber.test(aValue) && isNumber.test(bValue)) {
            return sortAscending ? aValue - bValue : bValue - aValue;
        } else {
            return sortAscending ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
        }
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

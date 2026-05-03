from flask import Flask, render_template_string, request, jsonify
from tinydb import TinyDB
import os

app = Flask(__name__)

# -----------------------------
# Database setup
# -----------------------------
if not os.path.exists("db.json"):
    open("db.json", "w").close()

db = TinyDB("db.json")

# -----------------------------
# HTML + CSS + JS (Single Page)
# -----------------------------
html_page = """
<!DOCTYPE html>
<html>
<head>
    <title>Mini Inventory Tracker</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
        h1 { text-align: center; color: #333; }
        .container { max-width: 900px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px #aaa; }
        .form-section { margin-bottom: 20px; text-align: center; }
        input { padding: 8px; margin: 5px; border: 1px solid #ccc; border-radius: 5px; }
        button { padding: 8px 15px; margin: 5px; cursor: pointer; border-radius: 5px; border: none; }
        .add-btn { background: #28a745; color: white; }
        .edit-btn { background: #007bff; color: white; }
        .delete-btn { background: #dc3545; color: white; }
        .search-input { width: 200px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        table, th, td { border: 1px solid #ddd; }
        th, td { padding: 10px; text-align: center; }
        th { background: #007bff; color: white; cursor: pointer; }
        tr:nth-child(even) { background: #f2f2f2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 Mini Inventory Tracker</h1>
        
        <div class="form-section">
            <input type="hidden" id="item_id">
            <input type="text" id="name" placeholder="Item Name">
            <input type="number" id="quantity" placeholder="Quantity">
            <input type="number" id="price" placeholder="Price">
            <button onclick="addItem()" class="add-btn">Add / Update Item</button>
        </div>

        <div style="text-align: center; margin-bottom: 20px;">
            <input type="text" id="searchBox" class="search-input" placeholder="🔍 Search items..." onkeyup="searchItems()">
        </div>

        <table id="inventoryTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">ID ⬍</th>
                    <th onclick="sortTable(1)">Name ⬍</th>
                    <th onclick="sortTable(2)">Quantity ⬍</th>
                    <th onclick="sortTable(3)">Price ⬍</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

<script>
// -----------------------------
// Load inventory from server
// -----------------------------
function loadInventory() {
    fetch('/items')
    .then(res => res.json())
    .then(data => {
        let tbody = document.querySelector("#inventoryTable tbody");
        tbody.innerHTML = "";
        data.forEach(item => {
            tbody.innerHTML += `
                <tr>
                    <td>${item.id}</td>
                    <td>${item.name}</td>
                    <td>${item.quantity}</td>
                    <td>${item.price.toFixed(2)}</td>
                    <td>
                        <button class="edit-btn" onclick="editItem(${item.id}, '${item.name}', ${item.quantity}, ${item.price})">Edit</button>
                        <button class="delete-btn" onclick="deleteItem(${item.id})">Delete</button>
                    </td>
                </tr>
            `;
        });
    });
}

// -----------------------------
// Add or Update Item
// -----------------------------
function addItem() {
    let id = document.getElementById("item_id").value;
    let name = document.getElementById("name").value;
    let quantity = document.getElementById("quantity").value;
    let price = document.getElementById("price").value;

    if (!name || !quantity || !price) {
        alert("Please fill all fields");
        return;
    }

    fetch('/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({id, name, quantity, price})
    }).then(() => {
        document.getElementById("item_id").value = "";
        document.getElementById("name").value = "";
        document.getElementById("quantity").value = "";
        document.getElementById("price").value = "";
        loadInventory();
    });
}

// -----------------------------
// Edit Item (populate form)
// -----------------------------
function editItem(id, name, quantity, price) {
    document.getElementById("item_id").value = id;
    document.getElementById("name").value = name;
    document.getElementById("quantity").value = quantity;
    document.getElementById("price").value = price;
}

// -----------------------------
// Delete Item
// -----------------------------
function deleteItem(id) {
    if (confirm("Are you sure you want to delete this item?")) {
        fetch('/delete/' + id, { method: 'DELETE' })
        .then(() => loadInventory());
    }
}

// -----------------------------
// Search Items
// -----------------------------
function searchItems() {
    let input = document.getElementById("searchBox").value.toLowerCase();
    let rows = document.querySelectorAll("#inventoryTable tbody tr");

    rows.forEach(row => {
        let name = row.cells[1].innerText.toLowerCase();
        if (name.includes(input)) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }
    });
}

// -----------------------------
// Sort Table by Column
// -----------------------------
function sortTable(n) {
    let table = document.getElementById("inventoryTable");
    let rows = Array.from(table.rows).slice(1);
    let asc = table.getAttribute("data-sort-dir") !== "asc";
    
    rows.sort((a, b) => {
        let x = a.cells[n].innerText.toLowerCase();
        let y = b.cells[n].innerText.toLowerCase();
        if (!isNaN(x) && !isNaN(y)) {
            return asc ? x - y : y - x;
        }
        return asc ? x.localeCompare(y) : y.localeCompare(x);
    });

    rows.forEach(row => table.tBodies[0].appendChild(row));
    table.setAttribute("data-sort-dir", asc ? "asc" : "desc");
}

window.onload = loadInventory;
</script>
</body>
</html>
"""

# -----------------------------
# Flask Routes
# -----------------------------
@app.route("/")
def index():
    return render_template_string(html_page)

@app.route("/items")
def get_items():
    items = db.all()
    for i, item in enumerate(items):
        item["id"] = item.doc_id
    return jsonify(items)

@app.route("/add", methods=["POST"])
def add_item():
    data = request.json
    name = data.get("name")
    quantity = int(data.get("quantity", 0))
    price = float(data.get("price", 0))
    id = data.get("id")

    if id:  # Update existing
        db.update({"name": name, "quantity": quantity, "price": price}, doc_ids=[int(id)])
    else:  # Insert new
        db.insert({"name": name, "quantity": quantity, "price": price})
    return jsonify({"status": "success"})

@app.route("/delete/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    db.remove(doc_ids=[item_id])
    return jsonify({"status": "deleted"})

# -----------------------------
# Run Application
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
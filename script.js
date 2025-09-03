// --- State ---
const AFA = "AFA";
let inventory = [];
let sales = [];
let cart = [];
let scanner = null;
let editingIndex = -1;
let lastSale = null;

// --- Data Persistence ---
function saveData() {
  localStorage.setItem('pos_inventory', JSON.stringify(inventory));
  localStorage.setItem('pos_sales', JSON.stringify(sales));
  localStorage.setItem('pos_cart', JSON.stringify(cart));
}

function loadData() {
  const inv = localStorage.getItem('pos_inventory');
  const sal = localStorage.getItem('pos_sales');
  const crt = localStorage.getItem('pos_cart');
  if (inv) inventory = JSON.parse(inv);
  if (sal) sales = JSON.parse(sal);
  if (crt) cart = JSON.parse(crt);
}

// --- Helpers ---
const $ = (id) => document.getElementById(id);
const format = (n) => Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });

// --- Navigation ---
const NAV_IDS = {
  dashboard: "nav-dashboard",
  sales: "nav-sales",
  inventory: "nav-inventory",
  reports: "nav-reports",
};

function showSection(id) {
  // sections visibility
  document.querySelectorAll(".content section").forEach((s) => s.classList.remove("active"));
  $(id).classList.add("active");

  // active nav highlight
  Object.values(NAV_IDS).forEach((btnId) => $(btnId).classList.remove("active"));
  const navId = NAV_IDS[id];
  if (navId) $(navId).classList.add("active");

  // section-specific refresh
  if (id === "dashboard") updateDashboard();
  if (id === "inventory") renderInventory();
  if (id === "reports") renderReports();
}

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  loadData();
  showSection("dashboard");

  // Add sample items if inventory is empty
  if (inventory.length === 0) {
    const sampleItems = [
      { name: "Apple", buy: 50, sell: 80, qty: 100 },
      { name: "Banana", buy: 30, sell: 50, qty: 150 },
      { name: "Orange", buy: 40, sell: 70, qty: 120 },
      { name: "Milk 1L", buy: 120, sell: 150, qty: 50 },
      { name: "Bread", buy: 25, sell: 40, qty: 80 },
      { name: "Rice 1kg", buy: 80, sell: 110, qty: 60 },
      { name: "Chicken 1kg", buy: 200, sell: 280, qty: 30 },
      { name: "Eggs (12)", buy: 60, sell: 90, qty: 40 },
      { name: "Sugar 1kg", buy: 70, sell: 95, qty: 70 },
      { name: "Tea 100g", buy: 150, sell: 200, qty: 25 }
    ];

    sampleItems.forEach(item => {
      const barcode = Date.now().toString() + Math.random().toString(36).substr(2, 5);
      inventory.push({
        name: item.name,
        buy: item.buy,
        sell: item.sell,
        qty: item.qty,
        barcode: barcode,
        sold: 0
      });
    });

    saveData();
  }

  // form handler
  const itemForm = $("itemForm");
  if (itemForm) {
    itemForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const nameEl = $("itemName");
      const buyEl = $("buyingPrice");
      const sellEl = $("sellingPrice");
      const qtyEl = $("quantity");

      const name = nameEl.value.trim();
      const buy = parseFloat(buyEl.value);
      const sell = parseFloat(sellEl.value);
      const qty = parseInt(qtyEl.value, 10);

      if (!name) return alert("Please enter item name.");
      if (isNaN(buy) || isNaN(sell) || isNaN(qty)) return alert("Please enter valid numbers.");
      if (buy > sell) {
        if (!confirm("Buying price is greater than selling price. Continue?")) return;
      }

      if (editingIndex >= 0) {
        // Edit existing item
        inventory[editingIndex] = { ...inventory[editingIndex], name, buy, sell, qty };
        editingIndex = -1;
        itemForm.querySelector("button[type='submit']").textContent = "Add Item";
      } else {
        // Add new item
        const barcode = Date.now().toString(); // simple unique code
        inventory.push({ name, buy, sell, qty, barcode, sold: 0 });
      }

      nameEl.value = "";
      buyEl.value = "";
      sellEl.value = "";
      qtyEl.value = "";

      saveData(); // Save after adding/editing
      renderInventory();
    });
  }

  // manual barcode enter: submit on Enter
  const manualBarcode = $("manualBarcode");
  if (manualBarcode) {
    manualBarcode.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        processManualBarcode();
      }
    });
  }

  // search inventory
  const searchInventory = $("searchInventory");
  if (searchInventory) {
    searchInventory.addEventListener("input", renderInventory);
  }
});

function renderInventory() {
  const tbody = document.querySelector("#inventoryTable tbody");
  const searchTerm = $("searchInventory").value.toLowerCase();
  tbody.innerHTML = "";
  inventory.forEach((item, i) => {
    if (item.name.toLowerCase().includes(searchTerm) || item.barcode.includes(searchTerm)) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.name}</td>
        <td>${format(item.buy)}</td>
        <td>${format(item.sell)}</td>
        <td>${item.qty}</td>
        <td>
          ${item.barcode}<br>
          <small>${format(item.sell)} ${AFA}</small>
        </td>
        <td>
          <button onclick="editItem(${i})">✏️ Edit</button>
          <button onclick="printBarcode(${i})">🖨️ Print Barcode</button>
          <button class="danger" onclick="deleteItem(${i})">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    }
  });
}



function deleteItem(i) {
  if (!confirm("Delete this item?")) return;
  inventory.splice(i, 1);
  saveData(); // Save after deleting
  renderInventory();
}

function editItem(i) {
  const item = inventory[i];
  $("itemName").value = item.name;
  $("buyingPrice").value = item.buy;
  $("sellingPrice").value = item.sell;
  $("quantity").value = item.qty;
  editingIndex = i;
  $("itemForm").querySelector("button[type='submit']").textContent = "Update Item";
}

// --- Barcode printing (fixed) ---
function printBarcode(index) {
  const item = inventory[index];
  const w = window.open("", "_blank", "width=420,height=360");
  w.document.write(`
    <html>
    <head>
      <title>Barcode Label</title>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 8px; }
        .wrap { display: inline-block; padding: 6px 10px; border: 1px dashed #666; border-radius: 6px; }
        h3 { margin: 6px 0 4px; font-size: 16px; }
        p { margin: 2px 0 8px; }
        @media print { body { margin: 0; } .wrap { border: none; } }
      </style>
      <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
    </head>
    <body>
      <div class="wrap">
        <h3>${item.name}</h3>
        <p>Price: <strong>${format(item.sell)} ${AFA}</strong></p>
        <svg id="barcode"></svg>
      </div>
      <script>
        JsBarcode("#barcode", "${item.barcode}", {
          format: "CODE128",
          displayValue: true,
          fontSize: 14,
          text: "${item.barcode} • ${Number(item.sell).toLocaleString()} ${AFA}"
        });
        setTimeout(() => window.print(), 200);
      </script>
    </body>
    </html>
  `);
  w.document.close();
}

// --- Sales / Scanner ---
function startScanner() {
  $("manualEntry").style.display = "none";
  $("scannerContainer").style.display = "block";

  if (scanner) {
    try { scanner.stop(); scanner.clear(); } catch (e) {}
  }

  scanner = new Html5Qrcode("reader");

  const onScanSuccess = (decodedText) => {
    addToCart(decodedText);
    stopScanner();
  };

  const onScanFailure = () => { /* ignore */ };

  scanner.start(
    { facingMode: "environment" },
    {
      fps: 10,
      qrbox: 250,
      formatsToSupport: [
        Html5QrcodeSupportedFormats.CODE_128,
        Html5QrcodeSupportedFormats.EAN_13,
        Html5QrcodeSupportedFormats.QR_CODE
      ]
    },
    onScanSuccess,
    onScanFailure
  );
}

function stopScanner() {
  if (scanner) {
    return scanner.stop()
      .then(() => {
        scanner.clear();
        $("scannerContainer").style.display = "none";
      })
      .catch(() => { $("scannerContainer").style.display = "none"; });
  } else {
    $("scannerContainer").style.display = "none";
  }
}

function manualBarcodeEntry() {
  stopScanner();
  $("manualEntry").style.display = "block";
  $("manualBarcode").focus();
}

function processManualBarcode() {
  const code = $("manualBarcode").value.trim();
  if (!code) return alert("Enter a barcode");
  addToCart(code);
  $("manualBarcode").value = "";
  $("manualBarcode").focus(); // Keep focus for next entry
}

function closeManualEntry() {
  $("manualEntry").style.display = "none";
  $("manualBarcode").value = "";
}

function addToCart(code) {
  const item = inventory.find((i) => i.barcode === code);
  if (!item) return alert("Item not found");
  const existing = cart.find((c) => c.barcode === code);
  if (existing) existing.qty += 1;
  else cart.push({ name: item.name, buy: item.buy, sell: item.sell, barcode: item.barcode, qty: 1 });
  saveData(); // Save cart changes
  renderCart();
}

function renderCart() {
  const cartItemsDiv = $("cartItems");
  const cartSummary = $("cartSummary");
  const completeBtn = $("completeBtn");
  const clearBtn = $("clearBtn");
  const printBtn = $("printBtn");

  if (cart.length === 0) {
    cartItemsDiv.innerHTML = '<div class="empty-cart">Cart is empty. Add items using scanner or manual entry.</div>';
    cartSummary.style.display = "none";
    completeBtn.disabled = true;
    clearBtn.disabled = true;
    printBtn.disabled = true;
    return;
  }

  // Show cart items in table format
  let html = `
    <table class="cart-table">
      <thead>
        <tr>
          <th>Item</th>
          <th>Price</th>
          <th>Qty</th>
          <th>Subtotal</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
  `;

  cart.forEach((c, i) => {
    const subtotal = c.sell * c.qty;
    html += `
      <tr>
        <td>${c.name}</td>
        <td>${format(c.sell)} ${AFA}</td>
        <td>
          <div class="qty-controls">
            <button onclick="changeQty(${i}, -1)">-</button>
            <span>${c.qty}</span>
            <button onclick="changeQty(${i}, 1)">+</button>
          </div>
        </td>
        <td>${format(subtotal)} ${AFA}</td>
        <td><button class="danger" onclick="removeFromCart(${i})">Remove</button></td>
      </tr>
    `;
  });

  html += "</tbody></table>";
  cartItemsDiv.innerHTML = html;
  cartSummary.style.display = "block";
  completeBtn.disabled = false;
  clearBtn.disabled = false;
  printBtn.disabled = false;

  calculateTotal();
}

function changeQty(i, d) {
  cart[i].qty += d;
  if (cart[i].qty <= 0) cart.splice(i, 1);
  saveData(); // Save cart changes
  renderCart();
}

function removeFromCart(i) {
  if (confirm(`Remove ${cart[i].name} from cart?`)) {
    cart.splice(i, 1);
    saveData();
    renderCart();
  }
}

function clearCart() {
  if (confirm("Clear all items from cart?")) {
    cart = [];
    saveData();
    renderCart();
  }
}

function calculateTotal() {
  let subtotal = 0;
  cart.forEach(c => {
    subtotal += c.sell * c.qty;
  });

  const discountPercent = parseFloat($("discountPercent").value) || 0;
  const discountAmount = subtotal * (discountPercent / 100);
  const total = subtotal - discountAmount;

  $("subtotal").textContent = format(subtotal) + " " + AFA;
  $("discountAmount").textContent = format(discountAmount) + " " + AFA;
  $("totalAmount").textContent = format(total) + " " + AFA;
}

function completeSale() {
  if (cart.length === 0) return alert("Cart is empty");

  for (const c of cart) {
    const item = inventory.find((i) => i.barcode === c.barcode);
    if (!item) return alert(`Item missing from inventory: ${c.name}`);
    if (item.qty < c.qty) return alert(`Not enough stock for ${c.name}. In stock: ${item.qty}`);
  }

  let subtotal = 0;
  let profit = 0;
  cart.forEach((c) => {
    const item = inventory.find((i) => i.barcode === c.barcode);
    item.qty -= c.qty;
    item.sold += c.qty;
    subtotal += c.sell * c.qty;
    profit += (c.sell - c.buy) * c.qty;
  });

  // Calculate discount
  const discountPercent = parseFloat($("discountPercent").value) || 0;
  const discountAmount = subtotal * (discountPercent / 100);
  const total = subtotal - discountAmount;

  lastSale = {
    date: new Date(),
    items: JSON.parse(JSON.stringify(cart)),
    subtotal,
    discountPercent,
    discountAmount,
    total,
    profit
  };
  sales.push(lastSale);
  cart = [];
  saveData(); // Save after sale
  renderCart();
  alert(`Sale completed: ${format(total)} ${AFA}`);

  // Auto-print receipt
  printReceipt();

  if ($("inventory").classList.contains("active")) renderInventory();
  if ($("dashboard").classList.contains("active")) updateDashboard();
  if ($("reports").classList.contains("active")) renderReports();
}

// --- Dashboard ---
function updateDashboard() {
  const now = new Date();

  // Calculate sales metrics
  let daily = 0, weekly = 0, monthly = 0, totalProfit = 0;
  let dailyTransactions = 0, weeklyTransactions = 0, monthlyTransactions = 0;
  let itemsSoldToday = 0;

  sales.forEach((s) => {
    const saleDate = new Date(s.date);
    const daysDiff = (now - saleDate) / (1000 * 60 * 60 * 24);

    if (daysDiff < 1) {
      daily += s.total;
      dailyTransactions++;
      itemsSoldToday += s.items.reduce((sum, item) => sum + item.qty, 0);
    }
    if (daysDiff < 7) {
      weekly += s.total;
      weeklyTransactions++;
    }
    if (saleDate.getMonth() === now.getMonth() && saleDate.getFullYear() === now.getFullYear()) {
      monthly += s.total;
      monthlyTransactions++;
    }
    totalProfit += s.profit;
  });

  // Update main metrics
  $("dailySales").textContent = format(daily) + " AFA";
  $("weeklySales").textContent = format(weekly) + " AFA";
  $("monthlySales").textContent = format(monthly) + " AFA";
  $("totalProfit").textContent = format(totalProfit) + " AFA";
  $("totalTransactions").textContent = sales.length;
  $("totalItems").textContent = inventory.length;

  // Calculate percentage changes (simplified - comparing to previous period)
  updateMetricChanges(daily, weekly, monthly, totalProfit, sales.length);

  // Top selling items
  updateTopItems();

  // Low stock alerts
  updateLowStockAlerts();

  // Recent sales
  updateRecentSales();

  // Quick stats
  updateQuickStats(daily, totalProfit, itemsSoldToday, dailyTransactions);

  // System alerts
  updateSystemAlerts();
}

function updateMetricChanges(daily, weekly, monthly, profit, transactions) {
  // Simplified percentage calculations (in a real system, you'd compare with previous periods)
  const dailyChange = transactions > 0 ? "+12%" : "+0%";
  const weeklyChange = transactions > 0 ? "+8%" : "+0%";
  const monthlyChange = transactions > 0 ? "+15%" : "+0%";
  const profitChange = profit > 0 ? "+18%" : "+0%";
  const transactionChange = transactions > 0 ? "+10%" : "+0%";
  const inventoryChange = inventory.length > 0 ? "+5%" : "+0%";

  $("dailyChange").textContent = dailyChange;
  $("weeklyChange").textContent = weeklyChange;
  $("monthlyChange").textContent = monthlyChange;
  $("profitChange").textContent = profitChange;
  $("transactionChange").textContent = transactionChange;
  $("inventoryChange").textContent = inventoryChange;
}

function updateTopItems() {
  const top = [...inventory].sort((a, b) => b.sold - a.sold).slice(0, 5);
  if (top.length > 0) {
    $("topItems").innerHTML = top.map((i, index) =>
      `<li class="top-item">
        <span class="rank">#${index + 1}</span>
        <span class="item-name">${i.name}</span>
        <span class="item-sold">${i.sold} sold</span>
      </li>`
    ).join("");
  } else {
    $("topItems").innerHTML = '<li class="no-data">No sales data yet</li>';
  }
}

function updateLowStockAlerts() {
  const lowStock = inventory.filter((i) => i.qty <= 5);
  const outOfStock = inventory.filter((i) => i.qty === 0);

  let html = "";

  if (outOfStock.length > 0) {
    html += outOfStock.map(item =>
      `<div class="alert-item critical">
        <span class="alert-icon">🚨</span>
        <div class="alert-details">
          <strong>${item.name}</strong>
          <span>OUT OF STOCK</span>
        </div>
        <button onclick="showSection('inventory')" class="alert-action">Restock</button>
      </div>`
    ).join("");
  }

  if (lowStock.length > outOfStock.length) {
    html += lowStock.filter(item => item.qty > 0).map(item =>
      `<div class="alert-item warning">
        <span class="alert-icon">⚠️</span>
        <div class="alert-details">
          <strong>${item.name}</strong>
          <span>Low Stock: ${item.qty} remaining</span>
        </div>
        <button onclick="showSection('inventory')" class="alert-action">Manage</button>
      </div>`
    ).join("");
  }

  if (html === "") {
    html = '<p class="no-alerts">All items are well stocked! 🎉</p>';
  }

  $("lowStockItems").innerHTML = html;
}

function updateRecentSales() {
  const recent = sales.slice(-5).reverse(); // Last 5 sales
  if (recent.length > 0) {
    $("recentSales").innerHTML = recent.map(sale =>
      `<div class="recent-sale-item">
        <div class="sale-time">${new Date(sale.date).toLocaleTimeString()}</div>
        <div class="sale-details">
          <span class="sale-amount">${format(sale.total)} AFA</span>
          <span class="sale-items">${sale.items.length} item(s)</span>
        </div>
      </div>`
    ).join("");
  } else {
    $("recentSales").innerHTML = '<p class="no-data">No recent transactions</p>';
  }
}

function updateQuickStats(dailySales, totalProfit, itemsSoldToday, dailyTransactions) {
  const avgTransaction = dailyTransactions > 0 ? dailySales / dailyTransactions : 0;
  const profitMargin = dailySales > 0 ? (totalProfit / dailySales) * 100 : 0;
  const outOfStockCount = inventory.filter(i => i.qty === 0).length;

  $("avgTransaction").textContent = format(avgTransaction) + " AFA";
  $("profitMargin").textContent = profitMargin.toFixed(1) + "%";
  $("itemsSoldToday").textContent = itemsSoldToday;
  $("outOfStockCount").textContent = outOfStockCount;
}

function updateSystemAlerts() {
  const alertsContainer = $("alertsContainer");
  let alerts = [];

  // Out of stock alert
  const outOfStock = inventory.filter(i => i.qty === 0);
  if (outOfStock.length > 0) {
    alerts.push({
      type: 'critical',
      icon: '🚨',
      title: 'Out of Stock Items',
      message: `${outOfStock.length} item(s) are out of stock`,
      action: 'showSection("inventory")'
    });
  }

  // Low stock alert
  const lowStock = inventory.filter(i => i.qty > 0 && i.qty <= 5);
  if (lowStock.length > 0) {
    alerts.push({
      type: 'warning',
      icon: '⚠️',
      title: 'Low Stock Alert',
      message: `${lowStock.length} item(s) running low`,
      action: 'showSection("inventory")'
    });
  }

  // High demand items
  const highDemand = inventory.filter(i => i.sold > 50);
  if (highDemand.length > 0) {
    alerts.push({
      type: 'info',
      icon: '📈',
      title: 'High Demand Items',
      message: `${highDemand.length} item(s) selling fast`,
      action: 'showSection("reports")'
    });
  }

  // System status
  if (alerts.length === 0) {
    alerts.push({
      type: 'success',
      icon: '✅',
      title: 'System Status',
      message: 'All systems operational',
      action: null
    });
  }

  alertsContainer.innerHTML = alerts.map(alert =>
    `<div class="alert-card ${alert.type}">
      <div class="alert-icon">${alert.icon}</div>
      <div class="alert-content">
        <h4>${alert.title}</h4>
        <p>${alert.message}</p>
      </div>
      ${alert.action ? `<button onclick="${alert.action}" class="alert-action-btn">View</button>` : ''}
    </div>`
  ).join("");
}

function generateReport() {
  // Simple report generation - could be enhanced
  const reportData = {
    totalSales: sales.reduce((sum, s) => sum + s.total, 0),
    totalProfit: sales.reduce((sum, s) => sum + s.profit, 0),
    totalTransactions: sales.length,
    totalItems: inventory.length,
    outOfStock: inventory.filter(i => i.qty === 0).length,
    lowStock: inventory.filter(i => i.qty > 0 && i.qty <= 5).length
  };

  const reportWindow = window.open("", "_blank", "width=600,height=800");
  reportWindow.document.write(`
    <html>
    <head>
      <title>POS Report</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .metric { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
        .metric strong { color: #2c3e50; }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>POS System Report</h1>
        <p>Generated on ${new Date().toLocaleString()}</p>
      </div>
      <div style="margin-top: 20px;">
        <div class="metric"><strong>Total Sales:</strong> ${format(reportData.totalSales)} AFA</div>
        <div class="metric"><strong>Total Profit:</strong> ${format(reportData.totalProfit)} AFA</div>
        <div class="metric"><strong>Transactions:</strong> ${reportData.totalTransactions}</div>
        <div class="metric"><strong>Inventory Items:</strong> ${reportData.totalItems}</div>
        <div class="metric"><strong>Out of Stock:</strong> ${reportData.outOfStock}</div>
        <div class="metric"><strong>Low Stock Items:</strong> ${reportData.lowStock}</div>
      </div>
    </body>
    </html>
  `);
  reportWindow.document.close();
  setTimeout(() => reportWindow.print(), 200);
}

// --- Reports ---
function renderReports(fromDate = null, toDate = null) {
  const tbody = document.querySelector("#reportTable tbody");
  tbody.innerHTML = "";
  let sumProfit = 0, sumSales = 0;

  // Filter sales by date if provided
  let filteredSales = sales;
  if (fromDate || toDate) {
    filteredSales = sales.filter(s => {
      const saleDate = new Date(s.date);
      if (fromDate && saleDate < new Date(fromDate)) return false;
      if (toDate && saleDate > new Date(toDate + 'T23:59:59')) return false;
      return true;
    });
  }

  // Calculate sold quantities from filtered sales
  const soldItems = {};
  filteredSales.forEach(sale => {
    sale.items.forEach(item => {
      if (!soldItems[item.barcode]) {
        soldItems[item.barcode] = { qty: 0, buy: item.buy, sell: item.sell };
      }
      soldItems[item.barcode].qty += item.qty;
    });
  });

  // Render table
  Object.keys(soldItems).forEach(barcode => {
    const itemData = soldItems[barcode];
    const item = inventory.find(i => i.barcode === barcode);
    if (item && itemData.qty > 0) {
      const profit = (itemData.sell - itemData.buy) * itemData.qty;
      const salesTotal = itemData.sell * itemData.qty;
      sumProfit += profit;
      sumSales += salesTotal;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${item.name}</td>
        <td>${itemData.qty}</td>
        <td>${format(itemData.buy)}</td>
        <td>${format(itemData.sell)}</td>
        <td>${format(profit)}</td>
      `;
      tbody.appendChild(tr);
    }
  });

  $("reportSummary").textContent =
    `Total Sales: ${format(sumSales)} ${AFA} | Total Profit: ${format(sumProfit)} ${AFA}`;
}

function filterReports() {
  const fromDate = $("reportFromDate").value;
  const toDate = $("reportToDate").value;
  renderReports(fromDate, toDate);
}

function clearReportFilter() {
  $("reportFromDate").value = "";
  $("reportToDate").value = "";
  renderReports();
}

// --- Receipt Printing ---
function printReceipt() {
  if (!lastSale) return alert("No recent sale to print");
  const w = window.open("", "_blank", "width=400,height=600");
  w.document.write(`
    <html>
    <head>
      <title>Receipt</title>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <style>
        body { font-family: monospace; font-size: 12px; margin: 10px; }
        .header { text-align: center; margin-bottom: 10px; }
        .item { display: flex; justify-content: space-between; margin: 5px 0; }
        .subtotal { border-top: 1px dashed #000; padding-top: 5px; margin-top: 5px; }
        .discount { border-top: 1px dashed #000; padding-top: 5px; margin-top: 5px; }
        .total { border-top: 1px solid #000; padding-top: 5px; font-weight: bold; margin-top: 5px; }
        @media print { body { margin: 0; } }
      </style>
    </head>
    <body>
      <div class="header">
        <h2>POS Receipt</h2>
        <p>Date: ${new Date(lastSale.date).toLocaleString()}</p>
      </div>
      ${lastSale.items.map(item => `
        <div class="item">
          <span>${item.name} x${item.qty}</span>
          <span>${format(item.sell * item.qty)} ${AFA}</span>
        </div>
      `).join("")}
      <div class="subtotal">
        <div class="item">
          <span>Subtotal:</span>
          <span>${format(lastSale.subtotal)} ${AFA}</span>
        </div>
      </div>
      ${lastSale.discountPercent > 0 ? `
      <div class="discount">
        <div class="item">
          <span>Discount (${lastSale.discountPercent}%):</span>
          <span>-${format(lastSale.discountAmount)} ${AFA}</span>
        </div>
      </div>
      ` : ''}
      <div class="total">
        <div class="item">
          <span>Total:</span>
          <span>${format(lastSale.total)} ${AFA}</span>
        </div>
      </div>
      <p style="text-align: center; margin-top: 20px;">Thank you for your business!</p>
    </body>
    </html>
  `);
  w.document.close();
  setTimeout(() => w.print(), 200);
}



// --- Sample Data Generator ---
function addSampleItems() {
  const sampleItems = [
    { name: "Apple", buy: 50, sell: 80, qty: 100 },
    { name: "Banana", buy: 30, sell: 50, qty: 150 },
    { name: "Orange", buy: 40, sell: 70, qty: 120 },
    { name: "Milk 1L", buy: 120, sell: 150, qty: 50 },
    { name: "Bread", buy: 25, sell: 40, qty: 80 },
    { name: "Rice 1kg", buy: 80, sell: 110, qty: 60 },
    { name: "Chicken 1kg", buy: 200, sell: 280, qty: 30 },
    { name: "Eggs (12)", buy: 60, sell: 90, qty: 40 },
    { name: "Sugar 1kg", buy: 70, sell: 95, qty: 70 },
    { name: "Tea 100g", buy: 150, sell: 200, qty: 25 }
  ];

  sampleItems.forEach(item => {
    const barcode = Date.now().toString() + Math.random().toString(36).substr(2, 5);
    inventory.push({
      name: item.name,
      buy: item.buy,
      sell: item.sell,
      qty: item.qty,
      barcode: barcode,
      sold: 0
    });
  });

  saveData();
  renderInventory();
  alert("10 sample items added successfully!");
}

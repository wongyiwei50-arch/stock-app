<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fusion Stock Trading</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: Arial, Helvetica, sans-serif;
            background-color: #111111;
            color: white;
            min-height: 100vh;
        }
        button {
            border: none;
            cursor: pointer;
            background: #333333;
            color: white;
            padding: 10px;
            font-weight: bold;
            transition: 0.2s;
        }
        button:hover {
            background: #444444;
        }
        #loginPage, #app {
            display: none;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: #1f1f1f;
        }
        .login-box {
            background: #222222;
            padding: 20px;
            border-radius: 10px;
            width: 400px;
            text-align: center;
        }
        .login-box h1 {
            font-size: 36px;
            margin-bottom: 20px;
        }
        .login-box input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            background: #333333;
            color: white;
            border: 1px solid #444444;
        }
        .login-box button {
            width: 100%;
        }
        .status {
            font-size: 16px;
            margin-top: 20px;
        }
        #app {
            display: flex;
        }
        .panel {
            background: #222222;
            border-radius: 10px;
            padding: 20px;
            margin-right: 20px;
            flex: 0 0 350px;
        }
        .panel h2 {
            margin-bottom: 10px;
        }
        .panel .btn {
            width: 100%;
            margin-top: 10px;
        }
        #mainContent {
            flex: 1;
        }
        #chart {
            width: 100%;
            height: 300px;
            background: #444444;
        }
        .trade-history, .holdings {
            margin-top: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border: 1px solid #333333;
        }
        th {
            background: #333333;
        }
        tr:nth-child(even) {
            background: #444444;
        }
        .buy-sell-btn {
            background: #2196F3;
            color: white;
            padding: 12px;
            border-radius: 8px;
            width: 100%;
        }
        .buy-sell-btn.sell {
            background: #FF3B30;
        }
    </style>
</head>
<body>
    <!-- LOGIN / SIGNUP PAGE -->
    <section id="loginPage" class="login-page">
        <div class="login-box">
            <h1>Fusion Trading</h1>
            <input id="username" type="text" placeholder="Username" />
            <input id="password" type="password" placeholder="Password" />
            <button onclick="login()">Login</button>
            <p class="status"></p>
        </div>
    </section>

    <!-- MAIN APP -->
    <section id="app" class="app">
        <div class="panel">
            <h2>Stock Info</h2>
            <select id="stockSelect" onchange="updateStock()"></select>
            <p id="stockName">Stock: -</p>
            <div id="stockPrice">Price: -</div>
            <input id="quantity" type="number" placeholder="Quantity" value="1" />
            <button class="buy-sell-btn" onclick="buyStock()">Buy Stock</button>
            <button class="buy-sell-btn sell" onclick="sellStock()">Sell Stock</button>
        </div>
        <div id="mainContent">
            <h2>Trade History</h2>
            <div class="trade-history">
                <table id="tradeHistoryTable"></table>
            </div>
            <h2>Current Holdings</h2>
            <div class="holdings">
                <table id="holdingsTable"></table>
            </div>
            <div id="chart"></div>
        </div>
    </section>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const stockData = {
            "AAPL": { name: "Apple Inc.", price: 145 },
            "MSFT": { name: "Microsoft Corporation", price: 290 },
            "GOOGL": { name: "Alphabet Inc.", price: 2725 },
            "AMZN": { name: "Amazon.com Inc.", price: 3400 }
        };

        const users = {};
        const trades = [];
        const holdings = {};

        let currentUser = null;
        let currentStock = "AAPL";
        let currentStockPrice = stockData[currentStock].price;

        document.getElementById("loginPage").style.display = "flex";
        document.getElementById("app").style.display = "none";

        function login() {
            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value.trim();

            if (users[username] && users[username] === password) {
                currentUser = username;
                document.getElementById("loginPage").style.display = "none";
                document.getElementById("app").style.display = "flex";
                document.querySelector(".status").textContent = "Logged in as " + username;
                populateStockSelect();
                updateStock();
            } else {
                document.querySelector(".status").textContent = "Invalid credentials!";
            }
        }

        function populateStockSelect() {
            const stockSelect = document.getElementById("stockSelect");
            Object.keys(stockData).forEach(stock => {
                const option = document.createElement("option");
                option.value = stock;
                option.textContent = stockData[stock].name;
                stockSelect.appendChild(option);
            });
        }

        function updateStock() {
            currentStock = document.getElementById("stockSelect").value;
            currentStockPrice = stockData[currentStock].price;
            document.getElementById("stockName").textContent = "Stock: " + stockData[currentStock].name;
            document.getElementById("stockPrice").textContent = "Price: $" + currentStockPrice;
        }

        function buyStock() {
            const quantity = parseInt(document.getElementById("quantity").value);
            const cost = currentStockPrice * quantity;

            if (!holdings[currentStock]) {
                holdings[currentStock] = { quantity: 0, averagePrice: 0 };
            }

            if (holdings[currentStock].quantity === 0) {
                holdings[currentStock].averagePrice = currentStockPrice;
            } else {
                holdings[currentStock].averagePrice = (holdings[currentStock].averagePrice * holdings[currentStock].quantity + currentStockPrice * quantity) / (holdings[currentStock].quantity + quantity);
            }

            holdings[currentStock].quantity += quantity;

            trades.push({
                action: "Buy",
                stock: currentStock,
                quantity: quantity,
                price: currentStockPrice,
                total: cost,
                date: new Date().toLocaleString()
            });

            updateTradeHistory();
            updateHoldings();
        }

        function sellStock() {
            const quantity = parseInt(document.getElementById("quantity").value);

            if (!holdings[currentStock] || holdings[currentStock].quantity < quantity) {
                alert("Not enough stock to sell.");
                return;
            }

            const revenue = currentStockPrice * quantity;
            holdings[currentStock].quantity -= quantity;

            trades.push({
                action: "Sell",
                stock: currentStock,
                quantity: quantity,
                price: currentStockPrice,
                total: revenue,
                date: new Date().toLocaleString()
            });

            updateTradeHistory();
            updateHoldings();
        }

        function updateTradeHistory() {
            const table = document.getElementById("tradeHistoryTable");
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>Action</th>
                        <th>Stock</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Total</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    ${trades.map(trade => `
                        <tr>
                            <td>${trade.action}</td>
                            <td>${trade.stock}</td>
                            <td>${trade.quantity}</td>
                            <td>$${trade.price}</td>
                            <td>$${trade.total}</td>
                            <td>${trade.date}</td>
                        </tr>
                    `).join('')}
                </tbody>
            `;
        }

        function updateHoldings() {
            const table = document.getElementById("holdingsTable");
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>Stock</th>
                        <th>Quantity</th>
                        <th>Average Price</th>
                        <th>Total Value</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.keys(holdings).map(stock => `
                        <tr>
                            <td>${stockData[stock].name}</td>
                            <td>${holdings[stock].quantity}</td>
                            <td>$${holdings[stock].averagePrice.toFixed(2)}</td>
                            <td>$${(holdings[stock].quantity * stockData[stock].price).toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            `;
        }
    </script>
</body>
</html>

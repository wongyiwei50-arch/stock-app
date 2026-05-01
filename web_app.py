import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

# =========================
# PAGE SETUP
# =========================
st.set_page_config(
    page_title="Fusion Stock Trading",
    page_icon="📉",
    layout="wide"
)

# =========================
# CUSTOM CSS
# IMPORTANT: CSS must be inside st.markdown, not written directly in Python.
# =========================
st.markdown("""
<style>
    .stApp {
        background-color: #111111;
        color: white;
    }

    [data-testid="stSidebar"] {
        background-color: #000000;
    }

    .main-title {
        text-align: center;
        font-size: 34px;
        font-weight: 800;
        color: white;
        margin-bottom: 0px;
    }

    .subtitle {
        text-align: center;
        color: #bfbfbf;
        font-size: 15px;
        margin-top: 0px;
        margin-bottom: 20px;
    }

    .metric-box {
        background-color: #1d1f27;
        border: 1px solid #24384d;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        margin-bottom: 12px;
    }

    .metric-label {
        color: #bfbfbf;
        font-size: 14px;
    }

    .metric-value {
        color: white;
        font-size: 28px;
        font-weight: 800;
    }

    .sell-price {
        color: #ff3b30;
        font-size: 36px;
        font-weight: 900;
        text-align: center;
    }

    .buy-price {
        color: #1e90ff;
        font-size: 36px;
        font-weight: 900;
        text-align: center;
    }

    .section-card {
        background-color: #06111d;
        border: 1px solid #24384d;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 18px;
    }

    .status-box {
        background-color: #000000;
        color: #cfcfcf;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        margin-top: 12px;
        margin-bottom: 12px;
    }

    .small-note {
        color: #bcbcbc;
        font-size: 13px;
        text-align: center;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# FILES
# =========================
USERS_FILE = "users.json"


def portfolio_file(username):
    return f"portfolio_{username}.json"


# =========================
# USER FUNCTIONS
# =========================
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)


# =========================
# PORTFOLIO FUNCTIONS
# =========================
def default_portfolio():
    return {
        "cash": 10000.0,
        "stocks": {},
        "price_alerts": {},
        "trade_history": []
    }


def load_portfolio(username):
    file_name = portfolio_file(username)
    if not os.path.exists(file_name):
        return default_portfolio()

    try:
        with open(file_name, "r", encoding="utf-8") as file:
            data = json.load(file)
            return {
                "cash": data.get("cash", 10000.0),
                "stocks": data.get("stocks", {}),
                "price_alerts": data.get("price_alerts", {}),
                "trade_history": data.get("trade_history", [])
            }
    except Exception:
        return default_portfolio()


def save_portfolio(username):
    data = {
        "cash": st.session_state.cash,
        "stocks": st.session_state.stocks,
        "price_alerts": st.session_state.price_alerts,
        "trade_history": st.session_state.trade_history
    }

    with open(portfolio_file(username), "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


# =========================
# STOCK DATA
# =========================
TICKER_NAME_MAP = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "META": "Meta Platforms Inc.",
    "NVDA": "NVIDIA Corporation",
    "NFLX": "Netflix Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "V": "Visa Inc."
}


def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        fast_info = stock.fast_info
        price = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice")
        if price:
            return round(float(price), 2)
    except Exception:
        pass

    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if not data.empty:
            return round(float(data["Close"].iloc[-1]), 2)
    except Exception:
        pass

    return None


def get_chart_data(ticker):
    try:
        data = yf.download(ticker, period="30d", interval="1d", progress=False)
        if data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.reset_index()
        return data
    except Exception:
        return pd.DataFrame()


# =========================
# SESSION INIT
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "AAPL"

if "quantity" not in st.session_state:
    st.session_state.quantity = 15

if "last_price" not in st.session_state:
    st.session_state.last_price = None

if "bid_price" not in st.session_state:
    st.session_state.bid_price = None

if "ask_price" not in st.session_state:
    st.session_state.ask_price = None


# =========================
# LOGIN PAGE
# =========================
def show_login_page():
    st.markdown("<div class='main-title'>📉 Fusion Stock Trading</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Trade Smarter. Grow Faster.</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("### 🍃 Please Enter Your Information")

        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        with tab_login:
            username = st.text_input("Login ID", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("🔍 Login", key="login_button"):
                users = load_users()

                if username not in users or users[username] != password:
                    st.error("Invalid username or password.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username

                    portfolio = load_portfolio(username)
                    st.session_state.cash = portfolio["cash"]
                    st.session_state.stocks = portfolio["stocks"]
                    st.session_state.price_alerts = portfolio["price_alerts"]
                    st.session_state.trade_history = portfolio["trade_history"]

                    st.success("Login successful!")
                    st.rerun()

        with tab_signup:
            new_username = st.text_input("Create Login ID", key="signup_username")
            new_password = st.text_input("Create Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")

            if st.button("📝 Sign Up", key="signup_button"):
                users = load_users()

                if not new_username or not new_password:
                    st.error("Please fill all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif new_username in users:
                    st.error("Username already exists.")
                else:
                    users[new_username] = new_password
                    save_users(users)
                    st.success("Account created successfully! You can now login.")


# =========================
# TRADING FUNCTIONS
# =========================
def add_trade_history(ticker, trade_type, quantity, price, amount, fee=0.0, note=""):
    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "type": trade_type,
        "quantity": quantity,
        "price": round(float(price), 2) if price else 0,
        "amount": round(float(amount), 2),
        "fee": round(float(fee), 2),
        "note": note
    }

    st.session_state.trade_history.insert(0, record)
    st.session_state.trade_history = st.session_state.trade_history[:500]


def refresh_price(ticker):
    price = get_stock_price(ticker)

    if price is None:
        st.session_state.last_price = None
        st.session_state.bid_price = None
        st.session_state.ask_price = None
        return None

    st.session_state.last_price = price
    st.session_state.bid_price = round(price - 0.03, 2)
    st.session_state.ask_price = round(price + 0.03, 2)
    return price


def buy_by_market(ticker, quantity):
    ask_price = st.session_state.ask_price

    if ask_price is None:
        st.error("No live price available yet.")
        return

    total_cost = ask_price * quantity

    if st.session_state.cash < total_cost:
        st.error("Insufficient funds.")
        return

    st.session_state.cash -= total_cost

    if ticker not in st.session_state.stocks:
        st.session_state.stocks[ticker] = {
            "quantity": 0,
            "buy_price": ask_price,
            "buy_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stop_loss": None,
            "take_profit": None
        }

    old_qty = st.session_state.stocks[ticker]["quantity"]
    old_avg = st.session_state.stocks[ticker]["buy_price"]
    new_qty = old_qty + quantity
    new_avg = ((old_qty * old_avg) + (quantity * ask_price)) / new_qty

    st.session_state.stocks[ticker]["quantity"] = new_qty
    st.session_state.stocks[ticker]["buy_price"] = round(new_avg, 2)
    st.session_state.stocks[ticker]["buy_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if st.session_state.stocks[ticker].get("stop_loss") is None:
        st.session_state.stocks[ticker]["stop_loss"] = round(max(0, ask_price - 1), 2)

    if st.session_state.stocks[ticker].get("take_profit") is None:
        st.session_state.stocks[ticker]["take_profit"] = round(ask_price + 1, 2)

    add_trade_history(ticker, "Buy (Open)", quantity, ask_price, -total_cost, 0.0, "Open position")
    save_portfolio(st.session_state.current_user)
    st.success(f"Bought {quantity} shares of {ticker} at ${ask_price:.2f} each.")


def sell_by_market(ticker, quantity, note="Manual close"):
    bid_price = st.session_state.bid_price

    if bid_price is None:
        st.error("No live price available yet.")
        return

    if ticker not in st.session_state.stocks:
        st.error("You do not have this stock in your portfolio.")
        return

    holding_qty = st.session_state.stocks[ticker].get("quantity", 0)

    if holding_qty < quantity:
        st.error(f"Not enough shares to sell. You currently hold {holding_qty} shares.")
        return

    buy_price = st.session_state.stocks[ticker]["buy_price"]
    proceeds = bid_price * quantity
    pnl = (bid_price - buy_price) * quantity

    st.session_state.cash += proceeds
    st.session_state.stocks[ticker]["quantity"] -= quantity

    add_trade_history(ticker, "Sell (Close)", quantity, bid_price, proceeds, 0.0, note)

    if st.session_state.stocks[ticker]["quantity"] <= 0:
        del st.session_state.stocks[ticker]

    save_portfolio(st.session_state.current_user)
    st.success(f"Sold {quantity} shares of {ticker} at ${bid_price:.2f}. P/L: ${pnl:.2f}")


def check_stop_loss_take_profit(ticker):
    if ticker not in st.session_state.stocks:
        return

    current_price = st.session_state.last_price
    if current_price is None:
        return

    data = st.session_state.stocks[ticker]
    quantity = data.get("quantity", 0)
    stop_loss = data.get("stop_loss")
    take_profit = data.get("take_profit")

    if quantity <= 0:
        return

    if stop_loss is not None and current_price <= stop_loss:
        st.warning(f"Stop Loss triggered at ${current_price:.2f}")
        sell_by_market(ticker, quantity, "Stop Loss triggered")
        return

    if take_profit is not None and current_price >= take_profit:
        st.info(f"Take Profit triggered at ${current_price:.2f}")
        sell_by_market(ticker, quantity, "Take Profit triggered")
        return


def check_manual_alert(ticker):
    if ticker not in st.session_state.price_alerts:
        return

    current_price = st.session_state.last_price
    if current_price is None:
        return

    alert_data = st.session_state.price_alerts[ticker]
    alert_price = alert_data.get("price")
    alert_type = alert_data.get("type")
    triggered = alert_data.get("triggered", False)

    if triggered:
        return

    if alert_type == "Above" and current_price >= alert_price:
        st.session_state.price_alerts[ticker]["triggered"] = True
        add_trade_history(ticker, "Manual Alert", 0, current_price, 0, 0, f"Above ${alert_price:.2f}")
        save_portfolio(st.session_state.current_user)
        st.warning(f"🔔 Alert triggered: {ticker} is above ${alert_price:.2f}")

    elif alert_type == "Below" and current_price <= alert_price:
        st.session_state.price_alerts[ticker]["triggered"] = True
        add_trade_history(ticker, "Manual Alert", 0, current_price, 0, 0, f"Below ${alert_price:.2f}")
        save_portfolio(st.session_state.current_user)
        st.warning(f"🔔 Alert triggered: {ticker} is below ${alert_price:.2f}")


# =========================
# MAIN APP PAGE
# =========================
def show_main_app():
    ticker = st.sidebar.selectbox(
        "Select Stock:",
        list(TICKER_NAME_MAP.keys()),
        index=list(TICKER_NAME_MAP.keys()).index(st.session_state.selected_ticker)
    )
    st.session_state.selected_ticker = ticker

    price = refresh_price(ticker)
    check_stop_loss_take_profit(ticker)
    check_manual_alert(ticker)

    st.sidebar.markdown(f"<div class='main-title'>{ticker} ▼</div>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<div class='subtitle'>{TICKER_NAME_MAP[ticker]}</div>", unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Market Execution / Quantity")

    q1, q2, q3, q4, q5 = st.sidebar.columns(5)

    with q1:
        if st.button("-5"):
            st.session_state.quantity = max(1, st.session_state.quantity - 5)
    with q2:
        if st.button("-1"):
            st.session_state.quantity = max(1, st.session_state.quantity - 1)
    with q3:
        st.markdown(f"<h2 style='text-align:center'>{st.session_state.quantity}</h2>", unsafe_allow_html=True)
    with q4:
        if st.button("+1"):
            st.session_state.quantity += 1
    with q5:
        if st.button("+5"):
            st.session_state.quantity += 5

    quantity = st.session_state.quantity

    st.sidebar.markdown("---")

    current_holding = st.session_state.stocks.get(ticker, {})
    default_sl = current_holding.get("stop_loss")
    default_tp = current_holding.get("take_profit")

    stop_loss_input = st.sidebar.number_input(
        "Stop Loss",
        min_value=0.0,
        value=float(default_sl) if default_sl is not None else 0.0,
        step=1.0
    )

    take_profit_input = st.sidebar.number_input(
        "Take Profit",
        min_value=0.0,
        value=float(default_tp) if default_tp is not None else 0.0,
        step=1.0
    )

    if st.sidebar.button("Save SL/TP"):
        if ticker in st.session_state.stocks:
            st.session_state.stocks[ticker]["stop_loss"] = stop_loss_input if stop_loss_input > 0 else None
            st.session_state.stocks[ticker]["take_profit"] = take_profit_input if take_profit_input > 0 else None
            save_portfolio(st.session_state.current_user)
            st.sidebar.success("SL/TP saved.")
        else:
            st.sidebar.warning("Buy this stock first before setting SL/TP.")

    st.sidebar.markdown("---")

    if price is None:
        st.sidebar.markdown("<div class='status-box'>Unable to fetch live price now.</div>", unsafe_allow_html=True)
    else:
        holding = st.session_state.stocks.get(ticker)
        if holding:
            pnl = (st.session_state.bid_price - holding.get("buy_price", 0)) * holding.get("quantity", 0)
            st.sidebar.markdown(
                f"<div class='status-box'>{ticker} live: {price:.2f}<br>Holding: {holding.get('quantity', 0)} | Avg Buy: {holding.get('buy_price', 0):.2f} | P/L: {pnl:.2f}</div>",
                unsafe_allow_html=True
            )
        else:
            st.sidebar.markdown(
                f"<div class='status-box'>{ticker} live market price: {price:.2f}</div>",
                unsafe_allow_html=True
            )

    c1, c2 = st.sidebar.columns(2)
    with c1:
        st.markdown(f"<div class='sell-price'>{st.session_state.bid_price if st.session_state.bid_price else '--.--'}</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;color:#ff8a80'>Bid</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='buy-price'>{st.session_state.ask_price if st.session_state.ask_price else '--.--'}</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;color:#90caf9'>Ask</div>", unsafe_allow_html=True)

    s1, s2 = st.sidebar.columns(2)
    with s1:
        if st.button("Sell by Market"):
            sell_by_market(ticker, quantity)
            st.rerun()
    with s2:
        if st.button("Buy by Market"):
            buy_by_market(ticker, quantity)
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Manual Alert")
    alert_price = st.sidebar.number_input("Alert Price", min_value=0.0, step=0.01)
    alert_type = st.sidebar.selectbox("Alert Type", ["Above", "Below"])

    if st.sidebar.button("Set Alert"):
        if alert_price <= 0:
            st.sidebar.error("Please enter a valid alert price.")
        else:
            st.session_state.price_alerts[ticker] = {
                "price": alert_price,
                "type": alert_type,
                "triggered": False
            }
            save_portfolio(st.session_state.current_user)
            st.sidebar.success(f"Price alert set for {ticker}: {alert_type} ${alert_price:.2f}")

    st.sidebar.markdown("<p class='small-note'>SL/TP will be monitored automatically while holding.<br>You can also set a manual price alert.</p>", unsafe_allow_html=True)

    # Main area
    top1, top2, top3 = st.columns([1, 1, 0.4])

    with top1:
        st.markdown(f"<div class='metric-box'><div class='metric-label'>Balance</div><div class='metric-value'>${st.session_state.cash:.2f}</div></div>", unsafe_allow_html=True)
    with top2:
        price_text = f"${price:.2f}" if price is not None else "$0.00"
        st.markdown(f"<div class='metric-box'><div class='metric-label'>Stock Price</div><div class='metric-value'>{price_text}</div></div>", unsafe_allow_html=True)
    with top3:
        if st.button("Logout"):
            save_portfolio(st.session_state.current_user)
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.rerun()

    st.markdown("### Current Holdings")
    holdings_rows = []

    for stock_ticker, data in st.session_state.stocks.items():
        if data.get("quantity", 0) <= 0:
            continue

        current_price = get_stock_price(stock_ticker) or data.get("buy_price", 0)
        shares = data.get("quantity", 0)
        avg_cost = data.get("buy_price", 0)
        market_value = current_price * shares
        pnl_amount = (current_price - avg_cost) * shares
        entry_time = data.get("buy_time", "Unknown")

        holdings_rows.append({
            "Ticker": stock_ticker,
            "Stock Name": TICKER_NAME_MAP.get(stock_ticker, stock_ticker),
            "Shares": shares,
            "Average Cost": f"${avg_cost:.2f}",
            "Current Price": f"${current_price:.2f}",
            "Market Value": f"${market_value:.2f}",
            "PnL Amount": f"${pnl_amount:.2f}",
            "SL": f"${data.get('stop_loss'):.2f}" if data.get("stop_loss") is not None else "not set",
            "TP": f"${data.get('take_profit'):.2f}" if data.get("take_profit") is not None else "not set",
            "Entry Time": entry_time
        })

    if holdings_rows:
        st.dataframe(pd.DataFrame(holdings_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No holdings yet.")

    st.markdown("### Trade History")

    history_col1, history_col2 = st.columns([1, 0.25])
    with history_col2:
        if st.session_state.trade_history:
            history_df_for_download = pd.DataFrame(st.session_state.trade_history)
            csv_data = history_df_for_download.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Export History (CSV)",
                data=csv_data,
                file_name="trade_history.csv",
                mime="text/csv"
            )

    if st.session_state.trade_history:
        st.dataframe(pd.DataFrame(st.session_state.trade_history), use_container_width=True, hide_index=True)
    else:
        st.info("No trade history yet.")

    st.markdown("### Chart")

    chart_data = get_chart_data(ticker)
    if chart_data.empty:
        st.warning("No chart data available.")
    else:
        if "Date" in chart_data.columns and "Close" in chart_data.columns:
            st.line_chart(chart_data.set_index("Date")["Close"], use_container_width=True)
        else:
            st.line_chart(chart_data["Close"], use_container_width=True)

    st.markdown("### Graphical Comparison of Multiple Stocks")
    compare_text = st.text_input("Enter tickers separated by comma", "AAPL,MSFT,GOOGL")

    if st.button("📊 Compare Stocks"):
        tickers = [item.strip().upper() for item in compare_text.split(",") if item.strip()]
        comparison_df = pd.DataFrame()

        for compare_ticker in tickers:
            data = get_chart_data(compare_ticker)
            if not data.empty and "Close" in data.columns:
                if "Date" in data.columns:
                    comparison_df[compare_ticker] = data.set_index("Date")["Close"]
                else:
                    comparison_df[compare_ticker] = data["Close"]

        if comparison_df.empty:
            st.warning("Unable to fetch comparison data.")
        else:
            st.line_chart(comparison_df, use_container_width=True)


# =========================
# RUN APP
# =========================
if not st.session_state.logged_in:
    show_login_page()
else:
    if "cash" not in st.session_state:
        portfolio = load_portfolio(st.session_state.current_user)
        st.session_state.cash = portfolio["cash"]
        st.session_state.stocks = portfolio["stocks"]
        st.session_state.price_alerts = portfolio["price_alerts"]
        st.session_state.trade_history = portfolio["trade_history"]

    show_main_app()

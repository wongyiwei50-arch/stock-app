import streamlit as st
import yfinance as yf
import json
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# =========================
# 用户 & 投资组合
# =========================
USERS_FILE = "users.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def default_portfolio():
    return {"cash": 10000.0, "stocks": {}}

def portfolio_file(user):
    return f"portfolio_{user}.json"

def load_portfolio(user):
    file = portfolio_file(user)
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default_portfolio()

def save_portfolio_data(portfolio_data, current_user):
    file = portfolio_file(current_user)
    with open(file, "w") as f:
        json.dump(portfolio_data, f, indent=4)

# =========================
# 核心交易逻辑（保持原函数）
# =========================
def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d", interval="1m")
        if not data.empty:
            return float(data["Close"].iloc[-1])
    except:
        return None

def buy_stock(portfolio_data, ticker, qty, price):
    total_cost = price * qty
    if portfolio_data.get("cash",0) >= total_cost:
        portfolio_data["cash"] -= total_cost
        if ticker not in portfolio_data["stocks"]:
            portfolio_data["stocks"][ticker] = {"quantity": 0, "buy_price": price, "stop_loss": None, "take_profit": None}
        old_qty = portfolio_data["stocks"][ticker]["quantity"]
        old_avg = portfolio_data["stocks"][ticker]["buy_price"]
        new_qty = old_qty + qty
        new_avg = ((old_qty * old_avg) + (qty * price)) / new_qty
        portfolio_data["stocks"][ticker]["quantity"] = new_qty
        portfolio_data["stocks"][ticker]["buy_price"] = round(new_avg,2)
        # 设置默认SL/TP
        if portfolio_data["stocks"][ticker]["stop_loss"] is None:
            portfolio_data["stocks"][ticker]["stop_loss"] = round(max(0, price-1),2)
        if portfolio_data["stocks"][ticker]["take_profit"] is None:
            portfolio_data["stocks"][ticker]["take_profit"] = round(price+1,2)
        return f"Bought {qty} shares of {ticker} at ${price}", portfolio_data
    else:
        return "Insufficient funds", portfolio_data

def sell_stock(portfolio_data, ticker, qty, price):
    holding_qty = portfolio_data["stocks"].get(ticker,{}).get("quantity",0)
    if holding_qty >= qty:
        proceeds = price * qty
        portfolio_data["stocks"][ticker]["quantity"] -= qty
        portfolio_data["cash"] += proceeds
        return f"Sold {qty} shares of {ticker} at ${price}", portfolio_data
    else:
        return f"You only have {holding_qty} shares", portfolio_data

# =========================
# Streamlit UI
# =========================
st.title("Fusion Trading App - Streamlit 1:1 Version")

mode = st.radio("Mode", ["Login", "Sign Up"])
users = load_users()
current_user = None

# 登录/注册
if mode=="Login":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in users and users[username] == password:
            st.success(f"Welcome {username}")
            current_user = username
        else:
            st.error("Invalid username or password")
else:
    new_user = st.text_input("New Username")
    new_pass = st.text_input("Password", type="password")
    confirm_pass = st.text_input("Confirm Password", type="password")
    if st.button("Sign Up"):
        if new_user in users:
            st.error("Username exists")
        elif new_pass != confirm_pass:
            st.error("Passwords do not match")
        else:
            users[new_user] = new_pass
            save_users(users)
            st.success("Account created! Please login.")

# =========================
# 主交易界面
# =========================
if current_user:
    portfolio_data = load_portfolio(current_user)
    st.subheader(f"Cash: ${portfolio_data.get('cash',10000):.2f}")

    tickers = ["AAPL","MSFT","TSLA","NVDA","AMZN"]
    selected_ticker = st.selectbox("Select Stock", tickers)
    qty = st.number_input("Quantity", min_value=1, value=15)

    # 当前价格
    price = get_stock_price(selected_ticker)
    st.write(f"Current price: ${price}")

    # 买卖操作
    if st.button(f"Buy {qty} shares of {selected_ticker}"):
        msg, portfolio_data = buy_stock(portfolio_data, selected_ticker, qty, price)
        save_portfolio_data(portfolio_data, current_user)
        st.success(msg)
    if st.button(f"Sell {qty} shares of {selected_ticker}"):
        msg, portfolio_data = sell_stock(portfolio_data, selected_ticker, qty, price)
        save_portfolio_data(portfolio_data, current_user)
        st.success(msg)

    # 投资组合
    st.subheader("Portfolio")
    df_portfolio = pd.DataFrame(portfolio_data["stocks"]).T
    st.dataframe(df_portfolio)

    # SL/TP
    st.subheader("Stop Loss / Take Profit")
    if selected_ticker in portfolio_data["stocks"]:
        sl = st.number_input("Stop Loss", value=portfolio_data["stocks"][selected_ticker].get("stop_loss",0.0))
        tp = st.number_input("Take Profit", value=portfolio_data["stocks"][selected_ticker].get("take_profit",0.0))
        portfolio_data["stocks"][selected_ticker]["stop_loss"] = sl
        portfolio_data["stocks"][selected_ticker]["take_profit"] = tp
        save_portfolio_data(portfolio_data, current_user)

    # 手动提醒
    st.subheader("Manual Alert")
    alert_price = st.number_input("Alert Price", min_value=0.0)
    alert_type = st.selectbox("Alert Type", ["Above","Below"])
    if st.button("Set Manual Alert"):
        if "manual_alerts" not in portfolio_data:
            portfolio_data["manual_alerts"] = {}
        portfolio_data["manual_alerts"][selected_ticker] = {"price": alert_price,"type": alert_type}
        save_portfolio_data(portfolio_data, current_user)
        st.success(f"Manual alert set for {selected_ticker}")

    # 多股对比
    st.subheader("Compare Multiple Stocks")
    compare_tickers = st.text_input("Enter tickers separated by comma", value="AAPL,MSFT,TSLA")
    if st.button("Compare"):
        tickers_list = [t.strip().upper() for t in compare_tickers.split(",") if t.strip()]
        all_data = {}
        for t in tickers_list:
            data = yf.download(t, period="30d", interval="1d", progress=False)
            if not data.empty:
                all_data[t] = data["Close"]
        plt.figure(figsize=(10,4))
        for t, series in all_data.items():
            plt.plot(series.index, series.values, label=t)
        plt.legend()
        st.pyplot(plt)

    # K线图
    st.subheader(f"{selected_ticker} Price History (30d)")
    stock_data = yf.download(selected_ticker, period="30d", interval="1d", progress=False)
    plt.figure(figsize=(10,4))
    plt.plot(stock_data["Close"])
    plt.title(f"{selected_ticker} Close Price (30d)")
    st.pyplot(plt)

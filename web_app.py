import streamlit as st
import yfinance as yf
import json
import os
import csv
from datetime import datetime
from PIL import Image
import matplotlib.pyplot as plt
import pandas as pd

# =========================
# 页面配置
# =========================
st.set_page_config(page_title="Fusion Trading App", layout="wide", page_icon="📈")

# 深色主题样式
st.markdown("""
<style>
    body { background-color: #111111; color: white; }
    .stApp { background-color: #111111; }
    .css-18e3th9 { padding-top: 1rem; }
    .css-1d391kg { padding: 1rem; }
    .stButton>button { 
        background-color: #2196F3; color: white; border: none;
        border-radius: 4px; padding: 8px 16px; font-weight: bold;
    }
    .stButton>button:hover { background-color: #1976D2; }
    .dataframe { background-color: #1d1f27; color: white; }
</style>
""", unsafe_allow_html=True)

# =========================
# 用户管理
# =========================
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# =========================
# 投资组合管理
# =========================
def default_portfolio():
    return {"cash": 10000.0, "stocks": {}}

def portfolio_file(user):
    return f"portfolio_{user}.json"

def load_portfolio(user):
    file = portfolio_file(user)
    if not os.path.exists(file):
        return default_portfolio()
    with open(file, "r") as f:
        return json.load(f)

def save_portfolio_data(portfolio_data, current_user):
    file = portfolio_file(current_user)
    with open(file, "w") as f:
        json.dump(portfolio_data, f, indent=4)

# =========================
# 数据获取
# =========================
def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        try:
            fast_info = stock.fast_info
            if fast_info:
                price = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice")
                if price:
                    return float(price)
        except Exception:
            pass
        data = stock.history(period="1d", interval="1m")
        if data is not None and not data.empty:
            return float(data["Close"].iloc[-1])
        data = stock.history(period="5d", interval="5m")
        if data is not None and not data.empty:
            return float(data["Close"].iloc[-1])
    except Exception as e:
        print("Price fetch error:", e)
    return None

def get_stock_data(ticker, period="30d"):
    return yf.download(ticker, period=period, interval="1d", progress=False)

# =========================
# 主应用
# =========================
def main_app():
    st.title("📉 Fusion Trading Panel")
    
    # 初始化数据
    if 'portfolio_data' not in st.session_state:
        st.session_state.portfolio_data = load_portfolio(st.session_state.current_user)
    
    portfolio_data = st.session_state.portfolio_data
    balance = portfolio_data.get("cash", 10000.0)
    portfolio = portfolio_data.get("stocks", {})
    
    # 股票选择
    ticker_name_map = {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corp.",
        "TSLA": "Tesla Inc.",
        "NVDA": "NVIDIA Corp.",
        "AMZN": "Amazon.com Inc.",
    }
    
    selected_ticker = st.selectbox("Select Stock", list(ticker_name_map.keys()), index=0)
    st.subheader(f"{selected_ticker} - {ticker_name_map.get(selected_ticker, 'Unknown')}")
    
    # 价格显示
    current_price = get_stock_price(selected_ticker)
    if current_price:
        st.metric("Current Price", f"${current_price:.2f}")
        bid_price = round(current_price - 0.03, 2)
        ask_price = round(current_price + 0.03, 2)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Bid Price", f"${bid_price:.2f}", delta_color="inverse")
        with col2:
            st.metric("Ask Price", f"${ask_price:.2f}")
    
    # 交易数量
    quantity = st.number_input("Quantity", min_value=1, value=15, step=1)
    
    # 买卖按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sell by Market", type="secondary"):
            st.success(f"Sold {quantity} shares of {selected_ticker} at ${bid_price:.2f}")
    with col2:
        if st.button("Buy by Market", type="primary"):
            st.success(f"Bought {quantity} shares of {selected_ticker} at ${ask_price:.2f}")
    
    # K线图
    if st.button("Show Candlestick Chart"):
        data = get_stock_data(selected_ticker)
        if not data.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.set_facecolor("#1d1f27")
            fig.patch.set_facecolor("#1d1f27")
            
            up = data[data["Close"] >= data["Open"]]
            down = data[data["Close"] < data["Open"]]
            
            ax.bar(up.index, up["Close"] - up["Open"], width=0.6, bottom=up["Open"], color="green")
            ax.bar(up.index, up["High"] - up["Close"], width=0.08, bottom=up["Close"], color="green")
            ax.bar(up.index, up["Low"] - up["Open"], width=0.08, bottom=up["Open"], color="green")
            
            ax.bar(down.index, down["Close"] - down["Open"], width=0.6, bottom=down["Open"], color="red")
            ax.bar(down.index, down["High"] - down["Open"], width=0.08, bottom=down["Open"], color="red")
            ax.bar(down.index, down["Low"] - down["Close"], width=0.08, bottom=down["Close"], color="red")
            
            ax.set_xlabel("Date", color="white")
            ax.set_ylabel("Price ($)", color="white")
            ax.set_title(f"{selected_ticker} Stock Price", color="white")
            ax.tick_params(colors="white")
            for spine in ax.spines.values():
                spine.set_color("white")
            
            st.pyplot(fig)
    
    # 持仓显示
    st.subheader("Current Holdings")
    if portfolio:
        holdings_data = []
        for ticker, data in portfolio.items():
            if data.get("quantity", 0) > 0:
                price = get_stock_price(ticker) or data.get("buy_price", 0)
                pnl = (price - data["buy_price"]) * data["quantity"]
                holdings_data.append({
                    "Ticker": ticker,
                    "Name": ticker_name_map.get(ticker, ticker),
                    "Shares": data["quantity"],
                    "Avg Cost": f"${data['buy_price']:.2f}",
                    "Current Price": f"${price:.2f}",
                    "P&L": f"${pnl:.2f}"
                })
        st.dataframe(holdings_data, use_container_width=True)
    else:
        st.info("No holdings yet")

# =========================
# 登录注册页面
# =========================
def login_page():
    st.title("📉 MARKET EDGE")
    st.subheader("Trade Smarter. Grow Faster.")
    
    menu = ["Login", "Sign Up"]
    choice = st.selectbox("Menu", menu)
    
    if choice == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            users = load_users()
            if username in users and users[username] == password:
                st.session_state.current_user = username
                st.session_state.page = "main"
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
    
    else:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Sign Up"):
            if password != confirm_password:
                st.error("Passwords do not match")
            else:
                users = load_users()
                if username in users:
                    st.error("Username already exists")
                else:
                    users[username] = password
                    save_users(users)
                    st.success("Account created successfully! Please login")

# =========================
# 主逻辑
# =========================
if 'page' not in st.session_state:
    st.session_state.page = "login"

if st.session_state.page == "login":
    login_page()
else:
    main_app()

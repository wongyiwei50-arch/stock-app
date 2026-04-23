import streamlit as st
import yfinance as yf
import json
import os
import csv
import random
import string
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import smtplib
from email.mime.text import MIMEText

# =========================
# 页面配置
# =========================
st.set_page_config(page_title="Fusion Trading App", layout="wide", page_icon="📉")

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
    .metric-container {
        background-color: #1d1f27;
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
    }
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
    return {
        "cash": 10000.0,
        "stocks": {},
        "price_alerts": {},
        "alert_history": [],
        "trade_history": []
    }

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
# 邮件发送
# =========================
def send_reset_email(to_email, link):
    sender_email = "wongyiwei50@gmail.com"
    sender_password = "iiuxouzznppouqak"
    try:
        msg = MIMEText(f"""
        Hello,
        
        You requested to reset your password.
        
        Please click the link below to reset your password:
        {link}
        
        If you did not request this, please ignore this email.
        
        Regards,
        Market Edge Team
        """)
        msg["Subject"] = "Reset Your Password - Market Edge"
        msg["From"] = sender_email
        msg["To"] = to_email

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email error:", e)
        return False

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
    price_alerts = portfolio_data.get("price_alerts", {})
    alert_history = portfolio_data.get("alert_history", [])
    trade_history = portfolio_data.get("trade_history", [])

    # 显示余额
    st.metric("💰 Balance", f"${balance:.2f}")

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
        bid_price = round(current_price - 0.03, 2)
        ask_price = round(current_price + 0.03, 2)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Bid Price", f"${bid_price:.2f}", delta_color="inverse")
        with col2:
            st.metric("Ask Price", f"${ask_price:.2f}")
    else:
        st.warning("Unable to fetch price")
        bid_price = ask_price = None

    # 交易数量
    quantity = st.number_input("Quantity", min_value=1, value=15, step=1)

    # SL/TP 设置
    st.subheader("Stop Loss / Take Profit")
    col1, col2 = st.columns(2)
    with col1:
        sl_price = st.number_input("Stop Loss", value=round(current_price*0.95, 2) if current_price else 0.0)
    with col2:
        tp_price = st.number_input("Take Profit", value=round(current_price*1.05, 2) if current_price else 0.0)

    # 买卖按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sell by Market", type="secondary"):
            if bid_price and balance >= bid_price * quantity:
                balance -= bid_price * quantity
                if selected_ticker in portfolio:
                    portfolio[selected_ticker]["quantity"] -= quantity
                    if portfolio[selected_ticker]["quantity"] <= 0:
                        del portfolio[selected_ticker]
                trade_history.insert(0, {
                    "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "ticker": selected_ticker,
                    "type": "Sell",
                    "quantity": quantity,
                    "price": bid_price,
                    "amount": bid_price * quantity
                })
                st.success(f"Sold {quantity} shares at ${bid_price:.2f}")
            else:
                st.error("Insufficient funds or price not available")
    with col2:
        if st.button("Buy by Market", type="primary"):
            if ask_price and balance >= ask_price * quantity:
                balance -= ask_price * quantity
                if selected_ticker not in portfolio:
                    portfolio[selected_ticker] = {
                        "quantity": 0,
                        "buy_price": 0,
                        "stop_loss": sl_price,
                        "take_profit": tp_price
                    }
                old_qty = portfolio[selected_ticker]["quantity"]
                old_avg = portfolio[selected_ticker]["buy_price"]
                new_qty = old_qty + quantity
                new_avg = ((old_qty * old_avg) + (quantity * ask_price)) / new_qty
                portfolio[selected_ticker]["quantity"] = new_qty
                portfolio[selected_ticker]["buy_price"] = round(new_avg, 2)
                portfolio[selected_ticker]["stop_loss"] = sl_price
                portfolio[selected_ticker]["take_profit"] = tp_price
                trade_history.insert(0, {
                    "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "ticker": selected_ticker,
                    "type": "Buy",
                    "quantity": quantity,
                    "price": ask_price,
                    "amount": -ask_price * quantity
                })
                st.success(f"Bought {quantity} shares at ${ask_price:.2f}")
            else:
                st.error("Insufficient funds or price not available")

    # 手动提醒
    st.subheader("Manual Price Alert")
    alert_price = st.number_input("Alert Price", value=current_price if current_price else 0.0)
    alert_type = st.selectbox("Alert When", ["Above", "Below"])
    if st.button("Set Alert"):
        price_alerts[selected_ticker] = {"price": alert_price, "type": alert_type}
        st.success(f"Alert set for {selected_ticker}")

    # 显示历史
    st.subheader("Alert History")
    if alert_history:
        st.dataframe(alert_history, use_container_width=True)
    else:
        st.info("No alerts yet")

    st.subheader("Trade History")
    if trade_history:
        st.dataframe(trade_history, use_container_width=True)
    else:
        st.info("No trades yet")

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

    # 多股票对比
    st.subheader("Compare Stocks")
    compare_tickers = st.text_input("Enter tickers separated by comma", "AAPL,MSFT")
    if st.button("Compare"):
        tickers = [t.strip().upper() for t in compare_tickers.split(",") if t.strip()]
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_facecolor("#1d1f27")
        fig.patch.set_facecolor("#1d1f27")
        for ticker in tickers:
            data = get_stock_data(ticker)
            if not data.empty:
                ax.plot(data.index, data["Close"], label=ticker)
        ax.set_xlabel("Date", color="white")
        ax.set_ylabel("Price ($)", color="white")
        ax.set_title("Stock Comparison", color="white")
        ax.tick_params(colors="white")
        ax.legend()
        for spine in ax.spines.values():
            spine.set_color("white")
        st.pyplot(fig)

    # 当前持仓
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

    # 保存数据
    portfolio_data["cash"] = balance
    portfolio_data["stocks"] = portfolio
    portfolio_data["price_alerts"] = price_alerts
    portfolio_data["alert_history"] = alert_history
    portfolio_data["trade_history"] = trade_history
    save_portfolio_data(portfolio_data, st.session_state.current_user)

# =========================
# 登录注册页面
# =========================
def login_page():
    st.title("📉 MARKET EDGE")
    st.subheader("Trade Smarter. Grow Faster.")
    
    menu = ["Login", "Sign Up", "Forgot Password"]
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
    
    elif choice == "Sign Up":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        email = st.text_input("Email")
        
        if st.button("Sign Up"):
            if password != confirm_password:
                st.error("Passwords do not match")
            else:
                users = load_users()
                if username in users:
                    st.error("Username already exists")
                else:
                    users[username] = {"password": password, "email": email}
                    save_users(users)
                    st.success("Account created successfully! Please login")
    
    elif choice == "Forgot Password":
        email = st.text_input("Enter your registered email")
        if st.button("Send Reset Link"):
            users = load_users()
            found = False
            for user, data in users.items():
                if data.get("email") == email:
                    found = True
                    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                    reset_link = f"http://localhost:8501/reset?token={token}"
                    if send_reset_email(email, reset_link):
                        st.success(f"Reset link sent to {email}")
                    else:
                        st.error("Failed to send email")
                    break
            if not found:
                st.error("Email not registered")

# =========================
# 主逻辑
#

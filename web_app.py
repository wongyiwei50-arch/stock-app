import streamlit as st
import yfinance as yf
import json
import os
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# =========================
# CONFIG
# =========================
USERS_FILE = "users.json"
PORTFOLIO_FILE = "portfolio_{}.json"

# =========================
# USER MANAGEMENT
# =========================
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_portfolio(user):
    file = PORTFOLIO_FILE.format(user)
    if not os.path.exists(file):
        return {"cash": 10000.0, "stocks": {}, "price_alerts": [], "alert_history": [], "trade_history": []}
    with open(file, "r") as f:
        return json.load(f)

def save_portfolio(user, data):
    file = PORTFOLIO_FILE.format(user)
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# INIT
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.portfolio = None

# =========================
# LOGIN / SIGNUP PAGE
# =========================
def show_login_page():
    # 设置页面样式
    st.markdown("""
    <style>
    .stApp {
        background-image: url('login_bg.jpg');
        background-size: cover;
        background-position: center;
    }
    .login-box {
        background-color: white;
        padding: 40px;
        border-radius: 10px;
        max-width: 400px;
        margin: auto;
        margin-top: 100px;
    }
    </style>
    """, unsafe_allow_html=True)

    # 顶部 Logo 和标题
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: white;'>📈 MARKET EDGE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: white; font-size: 18px;'>Trade Smarter. Grow Faster.</p>", unsafe_allow_html=True)

    # 登录框
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("🍃 Please Enter Your Information", unsafe_allow_html=True)
    st.markdown("---")

    menu = st.radio("", ["Login", "Sign Up"], horizontal=True)

    if menu == "Login":
        username = st.text_input("👤 Login ID")
        password = st.text_input("🔒 Password", type="password")

        if st.button("🔍 Login"):
            users = load_users()
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.portfolio = load_portfolio(username)
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")

    else:
        username = st.text_input("👤 Login ID")
        password = st.text_input("🔒 Password", type="password")
        confirm = st.text_input("🔐 Confirm Password", type="password")

        if st.button("📝 Sign Up"):
            if not username or not password:
                st.error("Please fill all fields.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                users = load_users()
                if username in users:
                    st.error("Username already exists.")
                else:
                    users[username] = password
                    save_users(users)
                    st.success("Account created! You can now login.")

    st.markdown("</div>", unsafe_allow_html=True)

    # 忘记密码
    st.markdown("<p style='text-align: center; color: white; margin-top: 30px;'>⬅️ I forgot my password</p>", unsafe_allow_html=True)

# =========================
# MAIN APP
# =========================
def show_main_app():
    st.set_page_config(layout="wide")
    st.title("📊 Fusion Trading Panel")
    
    portfolio = st.session_state.portfolio
    user = st.session_state.username
    
    # Sidebar
    st.sidebar.header(f"Welcome, {user}")
    st.sidebar.metric("Balance", f"${portfolio['cash']:.2f}")
    
    # Select stock
    tickers_list = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN"]
    ticker = st.sidebar.selectbox("Select Stock", tickers_list)
    
    quantity = st.sidebar.number_input("Quantity", min_value=1, value=15)
    
    # Get price
    def get_price(t):
        try:
            return float(yf.Ticker(t).fast_info['lastPrice'])
        except:
            return None
    
    price = get_price(ticker)
    if price:
        st.sidebar.metric("Current Price", f"${price:.2f}")
    
    # Buy / Sell
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Buy"):
        if price and portfolio['cash'] >= price * quantity:
            portfolio['cash'] -= price * quantity
            if ticker not in portfolio['stocks']:
                portfolio['stocks'][ticker] = {"quantity": 0, "buy_price": 0, "buy_time": ""}
            old = portfolio['stocks'][ticker]
            new_qty = old['quantity'] + quantity
            new_avg = ((old['quantity'] * old['buy_price']) + (quantity * price)) / new_qty
            portfolio['stocks'][ticker] = {
                "quantity": new_qty,
                "buy_price": round(new_avg, 2),
                "buy_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            portfolio['trade_history'].insert(0, {
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "ticker": ticker,
                "type": "Buy",
                "quantity": quantity,
                "price": price,
                "amount": -price*quantity
            })
            save_portfolio(user, portfolio)
            st.success(f"Bought {quantity} {ticker} at ${price:.2f}")
    
    if col2.button("Sell"):
        if price and ticker in portfolio['stocks']:
            holding = portfolio['stocks'][ticker]
            if holding['quantity'] >= quantity:
                portfolio['cash'] += price * quantity
                portfolio['stocks'][ticker]['quantity'] -= quantity
                if portfolio['stocks'][ticker]['quantity'] == 0:
                    del portfolio['stocks'][ticker]
                portfolio['trade_history'].insert(0, {
                    "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "ticker": ticker,
                    "type": "Sell",
                    "quantity": quantity,
                    "price": price,
                    "amount": price*quantity
                })
                save_portfolio(user, portfolio)
                st.success(f"Sold {quantity} {ticker} at ${price:.2f}")
    
    # Current Holdings
    st.subheader("📋 Current Holdings")
    if portfolio['stocks']:
        data = []
        for t, info in portfolio['stocks'].items():
            current_p = get_price(t) or info['buy_price']
            value = current_p * info['quantity']
            pnl = (current_p - info['buy_price']) * info['quantity']
            data.append([t, info['quantity'], f"${info['buy_price']:.2f}", f"${current_p:.2f}", f"${value:.2f}", f"${pnl:.2f}"])
        df = pd.DataFrame(data, columns=["Ticker", "Shares", "Avg Cost", "Current Price", "Market Value", "P/L"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No holdings yet.")
    
    # Trade History
    st.subheader("📜 Trade History")
    if portfolio['trade_history']:
        df_hist = pd.DataFrame(portfolio['trade_history'])
        st.dataframe(df_hist, use_container_width=True)
    
    # =========================
    # COMPARISON CHART
    # =========================
    st.subheader("📊 Compare Stocks")
    compare_list = st.text_input("Enter tickers (comma separated)", "AAPL,MSFT,GOOGL")
    if st.button("Compare"):
        tickers = [t.strip().upper() for t in compare_list.split(",") if t.strip()]
        if len(tickers) >= 2:
            fig, ax = plt.subplots(figsize=(4, 2.2))
            ax.set_facecolor("#1d1f27")
            fig.patch.set_facecolor("#1d1f27")
            
            for t in tickers:
                try:
                    df = yf.download(t, period="30d", interval="1d", progress=False)
                    if not df.empty:
                        ax.plot(df.index, df["Close"], label=t, linewidth=1.2)
                except:
                    pass
            
            ax.set_title("Graphical Comparison of Multiple Stocks", color="white", fontsize=7)
            ax.set_xlabel("Date", color="white", fontsize=6)
            ax.set_ylabel("Price ($)", color="white", fontsize=6)
            ax.tick_params(axis='both', colors='white', labelsize=5)
            ax.legend(fontsize=6)
            
            for spine in ax.spines.values():
                spine.set_color("white")
            
            fig.autofmt_xdate()
            fig.subplots_adjust(left=0.12, right=0.93, top=0.86, bottom=0.22)
            st.pyplot(fig, use_container_width=True)
        else:
            st.warning("Enter at least 2 tickers.")
    
    # Logout
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.portfolio = None
        st.experimental_rerun()

# =========================
# ROUTING
# =========================
if st.session_state.logged_in:
    show_main_app()
else:
    show_login_page()

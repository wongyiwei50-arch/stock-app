import streamlit as st
import yfinance as yf
import json
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# =========================
# User & Portfolio Management
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
# Streamlit App UI
# =========================
st.title("Fusion Stock Trading Panel - Streamlit Version")

# Login
st.subheader("Login")
username = st.text_input("Username")
password = st.text_input("Password", type="password")
login_btn = st.button("Login")

if login_btn:
    users = load_users()
    if username in users and users[username] == password:
        st.success(f"Welcome, {username}!")
        current_user = username
        portfolio_data = load_portfolio(username)

        # Select ticker
        tickers = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN"]
        ticker = st.selectbox("Select Stock", tickers)

        qty = st.number_input("Quantity", min_value=1, value=15)

        # Show current portfolio table
        st.subheader("Portfolio")
        st.write(portfolio_data.get("stocks", {}))

        # Fetch current stock price
        def get_price(ticker):
            try:
                stock = yf.Ticker(ticker)
                data = stock.history(period="1d", interval="1m")
                if data is not None and not data.empty:
                    return float(data["Close"].iloc[-1])
            except:
                return None

        price = get_price(ticker)
        st.write(f"Current price of {ticker}: ${price}")

        # Buy / Sell buttons
        if st.button(f"Buy {qty} shares of {ticker}"):
            total_cost = price * qty
            if portfolio_data.get("cash", 0) >= total_cost:
                portfolio_data["cash"] -= total_cost
                if ticker not in portfolio_data["stocks"]:
                    portfolio_data["stocks"][ticker] = {"quantity": 0, "buy_price": price}
                old_qty = portfolio_data["stocks"][ticker]["quantity"]
                old_avg = portfolio_data["stocks"][ticker]["buy_price"]
                new_qty = old_qty + qty
                new_avg = ((old_qty * old_avg) + (qty * price)) / new_qty
                portfolio_data["stocks"][ticker]["quantity"] = new_qty
                portfolio_data["stocks"][ticker]["buy_price"] = round(new_avg, 2)
                save_portfolio_data(portfolio_data, current_user)
                st.success(f"Bought {qty} shares of {ticker} at ${price}")

        if st.button(f"Sell {qty} shares of {ticker}"):
            holding_qty = portfolio_data["stocks"].get(ticker, {}).get("quantity", 0)
            if holding_qty >= qty:
                portfolio_data["stocks"][ticker]["quantity"] -= qty
                proceeds = price * qty
                portfolio_data["cash"] += proceeds
                save_portfolio_data(portfolio_data, current_user)
                st.success(f"Sold {qty} shares of {ticker} at ${price}")

        # Plot historical chart
        st.subheader(f"{ticker} Price History")
        stock_data = yf.download(ticker, period="30d", interval="1d", progress=False)
        plt.figure(figsize=(10, 4))
        plt.plot(stock_data['Close'])
        plt.title(f"{ticker} Stock Price (30d)")
        st.pyplot(plt)
    else:
        st.error("Invalid credentials")

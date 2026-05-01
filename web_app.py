# Importing necessary libraries
import tkinter as tk # Tkinter for GUI
from tkinter import ttk, messagebox, simpledialog, filedialog # Additional Tkinter components
import streamlit as st # Streamlit for web app support
import yfinance as yf # Yahoo Finance for financial data
import json # For working with JSON files
import shutil # For file operations like copying or moving
import os # For interacting with the operating system
import csv # For working with CSV files
from datetime import datetime # For date and time operations
from PIL import Image, ImageTk # For image processing (Pillow)
import random
import time
import winsound
import ctypes

# Importing Matplotlib and setting the backend to TkAgg for compatibility with Tkinter
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt # For plotting graphs
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # For embedding Matplotlib figures in Tkinter
import pandas as pd # For data manipulation and analysis
import matplotlib.dates as mdates # For handling date formatting in plots

# Try to import the Plyer library for notifications; handle import errors gracefully
try:
    from plyer import notification # Plyer for desktop notifications
    PLYER_AVAILABLE = True # If Plyer is available, set the flag to True
except Exception:
    PLYER_AVAILABLE = False # If Plyer is not available, set the flag to False

# 🔔 Function to show popup message
def show_message(title, text):
    ctypes.windll.user32.MessageBoxW(0, text, title, 0)

# =========================
# USER MANAGEMENT
# =========================

# File where user data is stored
USERS_FILE = "users.json"

# Function to load users from the USERS_FILE
def load_users():
    # Check if the users file does not exist, return an empty dictionary
    if not os.path.exists(USERS_FILE):
        return {}

    # If the file exists, open and load the user data from the file
    with open(USERS_FILE, "r") as f:
        return json.load(f)# Return the data as a dictionary
    
# Function to save user data to USERS_FILE
def save_users(users):
    # Open the USERS_FILE in write mode and save the users data in JSON format
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def check_and_alert(target_price, condition):
    # DELETE THIS LINE: current_price = self.last_price
    
    # JUST WRITE THE NUMBER YOU SEE ON SCREEN MANUALLY
    current_price = self.last_price
    
    print("Checking:", current_price, "vs", target_price)

    triggered = False
    if condition == "Above" and current_price > target_price:
        triggered = True
    elif condition == "Below" and current_price < target_price:
        triggered = True

    if triggered:
        print("✅ TRIGGERED!")
        # THIS WILL POP UP 100%
        ctypes.windll.user32.MessageBoxW(0, f"Price reached {current_price}", "Alert", 0)
        winsound.Beep(1000, 500)

# This is the function that runs when you click Set Alert
def on_set_alert_clicked():
    # Get data from your input
    target_price = float(price_input.text())
    condition = condition_selector.currentText()  # "Above" or "Below"

    # This loop runs in the background
    def background_monitor():
        while True:
            check_and_alert(target_price, condition)
            time.sleep(1)  # Check every 1 second

    # Start the background task
    thread = threading.Thread(target=background_monitor)
    thread.daemon = True
    thread.start()
    
    print("Alert has been set! ✅") # Optional message


# =========================
# PORTFOLIO
# =========================

# Function to return the default portfolio structure
def default_portfolio():
    # The default portfolio contains cash balance and an empty dictionary for stocks
    return {"cash": 10000.0, "stocks": {}}

# Function to generate the file path for the portfolio based on the user's name
def portfolio_file(user):
    # The file is named with the user's name (e.g., portfolio_username.json)
    return f"portfolio_{user}.json"

# Function to load the portfolio data for a specific user
def load_portfolio(user):
    # Get the file path for the user's portfolio
    file = portfolio_file(user)

    # If the portfolio file doesn't exist, return a default portfolio structure
    if not os.path.exists(file):
        return {
            "cash": 10000.0,     # Default cash balance
            "stocks": {},        # Empty stocks dictionary
            "price_alerts": {},  # Empty dictionary for price alerts
            "trade_history": []  # Empty list for trade history
        }

    # If the portfolio file exists, open it and load the data
    with open(file, "r") as f:
        return json.load(f) # Return the portfolio data as a dictionary

# Function to save the portfolio data for a specific user
def save_portfolio_data(portfolio_data, current_user):
    # Get the file path for the user's portfolio
    file = portfolio_file(current_user)

    # Open the file in write mode and save the portfolio data in JSON format
    with open(file, "w") as f:
        json.dump(portfolio_data, f, indent=4) # Save the data with indentation for readability

# Function to save the portfolio data for a specific user
def save_portfolio_data(portfolio_data, current_user):
    # Get the file path for the user's portfolio
    file = portfolio_file(current_user)

    # Open the file in write mode and save the portfolio data in JSON format
    with open(file, "w") as f:
        json.dump(portfolio_data, f, indent=4) # Save the data with indentation for readability


# =========================
# MAIN APP CLASS
# =========================
class FusionTradingApp:
    def __init__(self, root, portfolio_data):
        # Initialize the main window
        self.root = root
        self.root.title("Fusion Stock Trading Panel") # Set the window title
        self.root.geometry("1400x860") # Set the window size
        self.root.configure(bg="#111111") # Set the background color of the window

        # ===== Basic Data =====
        self.default_balance = portfolio_data.get("cash", 10000.0) # Default cash balance, if not provided
        self.balance = self.default_balance # Set the current balance
        self.portfolio = portfolio_data.get("stocks", {}) # Stocks portfolio, defaults to empty if not provided
        self.price_alerts = portfolio_data.get("price_alerts", {}) # Price alerts data, defaults to empty if not provided
        self.trade_history = portfolio_data.get("trade_history", []) # Trade history, defaults to empty if not provided

        # ===== Ticker Data =====
        self.ticker_var = tk.StringVar(value="AAPL") # Set the default ticker symbol to AAPL
        # A dictionary mapping ticker symbols to full company names
        self.ticker_name_map = {
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

        # ===== Other Variables =====
        self.quantity_var = tk.IntVar(value=15) # Default quantity of shares set to 15
        self.manual_alert_type = tk.StringVar(value="Above") # Default alert type set to "Above"

        # ===== Trading Parameters =====
        self.stop_loss = None # Stop loss value (initially not set)
        self.take_profit = None # Take profit value (initially not set)
        self.last_price = None # Last fetched market price (initially not set)
        self.bid_price = None # Bid price (initially not set)
        self.ask_price = None # Ask price (initially not set)
        self.chart = None # Chart object (initially not set)

        # ===== Build UI =====
        self.build_ui() # Build the user interface
        self.change_ticker(self.ticker_var.get())# Change the ticker symbol based on the initial value
        self.update_market_price()# Fetch and update the current market price for the selected ticker

    # ==============================================
    # New addition: Multi-stock comparison function
    # ==============================================
    def get_multiple_stock_data(self, tickers, period="30d"):
        all_data = {} # Dictionary to store the stock data for each ticker

        # Loop through each ticker symbol in the list
        for ticker in tickers:
            try:
                # Download the stock data using the yfinance library
                # period specifies the duration (default is 30 days)
                # interval="1d" fetches data at daily intervals
                data = yf.download(ticker, period=period, interval="1d", progress=False)

                # If the data is not empty, store the closing prices for the ticker
                if not data.empty:
                    all_data[ticker] = data["Close"]
            except Exception as e:
                # If an error occurs while fetching data for the ticker, print the error message
                print(f"Error fetching {ticker}: {e}")
        return all_data # Return the dictionary containing the stock data for all tickers

    def plot_comparison_chart(self, all_data):
        # Create a figure and axes for plotting the first comparison chart (small size)
        fig, ax = plt.subplots(figsize=(5, 2.5))

        # Set the background color of the plot and figure
        ax.set_facecolor("#1d1f27") # Dark background for the chart
        fig.patch.set_facecolor("#1d1f27") # Dark background for the figure
        
        # Plot the data for each stock ticker in the all_data dictionary
        for ticker, close_prices in all_data.items():
            ax.plot(close_prices.index, close_prices, label=ticker, linewidth=1) # Plot closing prices with ticker as label

        # Set chart labels and title with white text
        ax.set_xlabel("Date", color="white", fontsize=8) # Label for the x-axis
        ax.set_ylabel("Price ($)", color="white", fontsize=8) # Label for the y-axis
        ax.set_title("Graphical Comparison of Multiple Stocks", color="white", fontsize=10) # Title of the chart
        ax.tick_params(colors="white", labelsize=7) # Set tick mark colors to white and small size
        ax.legend(fontsize=7) # Display legend with small font size
        
        # Adjust x-axis date formatting and layout
        fig.autofmt_xdate() # Rotate x-axis labels for better readability
        fig.tight_layout() # Adjust the layout to prevent overlap
        
        # Adjust the margins of the figure
        fig.subplots_adjust(left=0.12, right=0.93, top=0.85, bottom=0.22)
        
        # If a comparison canvas already exists, destroy it and create a new one
        if hasattr(self, 'comparison_canvas'):
            self.comparison_canvas.get_tk_widget().destroy()

        # Create a new FigureCanvasTkAgg for the small chart and pack it inside the right panel
        self.comparison_canvas = FigureCanvasTkAgg(fig, master=self.right_panel)
        self.comparison_canvas.get_tk_widget().pack(padx=10, pady=5) # Add padding around the canvas
        self.comparison_canvas.draw() #Draw the canvas

        # Clear out old contents from the chart container
        for widget in self.chart_container.winfo_children():
            widget.destroy()
            
        # Create a second, larger comparison chart (for the full view)
        fig, ax = plt.subplots(figsize=(5, 3)) # Larger chart size
        ax.set_facecolor("#1d1f27") # Dark background for the chart
        fig.patch.set_facecolor("#1d1f27") # Dark background for the figure

        # Plot the data for each stock ticker in the all_data dictionary
        for ticker, close_prices in all_data.items():
            ax.plot(close_prices.index, close_prices, label=ticker, linewidth=1.5)# Plot with thicker lines

        # Set chart labels and title with white text
        ax.set_xlabel("Date", color="white", labelpad=5) # Label for the x-axis
        ax.set_ylabel("Price ($)", color="white", labelpad=5) # Label for the y-axis
        ax.set_title("Graphical Comparison of Multiple Stocks", color="white", fontsize=10, pad=10) # Title of the chart
        ax.tick_params(colors="white") # Set tick mark colors to white and small size
        ax.legend()# Display legend
        for spine in ax.spines.values():
            spine.set_color("white")

        # ===== Key: Set Date Format =====
        import matplotlib.dates as mdates # Import the date formatter module
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d')) # Format the x-axis dates as MM-DD
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))  # Show a tick every 7 days

        # Customize the appearance of the spines (borders)
        for spine in ax.spines.values():
            spine.set_color("white") # Set spine color to white
            spine.set_linewidth(0.5) # Set the thickness of the spine lines

        # Adjust x-axis date formatting and layout
        fig.autofmt_xdate() # Rotate x-axis labels for better readability
        fig.tight_layout() # Adjust the layout to prevent overlap

        # Draw Inside a Fixed Container
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        

    def open_comparison_window(self):
        # Create a new Toplevel window (a new window on top of the main window)
        win = tk.Toplevel(self.root)
        win.title("Select Stocks to Compare") # Set the title of the window
        win.geometry("400x300") # Set the size of the window (width x height)
        win.configure(bg="#1d1f27") # Set the background color of the window

        # Create a label asking the user to enter tickers, and place it inside the window
        tk.Label(win, text="Enter tickers (separated by comma):", bg="#1d1f27", fg="white").pack(pady=10)

        # Create an entry widget for the user to input stock tickers
        entry = tk.Entry(win, width=30, font=("Arial", 12))
        entry.pack(pady=5)

        # Pre-fill the entry widget with default tickers (e.g., "AAPL,MSFT,GOOGL")
        entry.insert(0, "AAPL,MSFT,GOOGL")

        def start_compare():
            # Get the tickers entered by the user in the entry widget, clean up spaces, and convert to uppercase
            tickers = [t.strip().upper() for t in entry.get().split(",") if t.strip()]

            # Check if the user entered fewer than 2 tickers
            if len(tickers) < 2:
                # Show a warning message if fewer than 2 tickers are entered
                messagebox.showwarning("Warning", "Please enter at least 2 tickers.")
                return # Exit the function if there are less than 2 tickers

            # Fetch data for the entered tickers using the get_multiple_stock_data function
            data = self.get_multiple_stock_data(tickers)

             # Plot the comparison chart for the fetched data
            self.plot_comparison_chart(data)

            # Close the comparison window after completing the comparison
            win.destroy()
            
        # Create a "Compare" button in the comparison window
        tk.Button(
            win,
            text="Compare", # Text on the button
            command=start_compare, # The function to call when the button is clicked
            bg="#2196F3", # Button background color (blue)
            fg="white", # Button text color (white)
            font=("Arial", 12, "bold") # Button font style (Arial, size 12, bold)
        ).pack(pady=20) # Add padding around the button for spacing
        
    # =========================
    # UI
    # =========================
    def build_ui(self):
        # Create the main frame for the root window, set background color and add padding
        main = tk.Frame(self.root, bg="#111111")
        main.pack(fill="both", expand=True, padx=12, pady=12) # Fill the entire window and add padding around

        # Create the left panel (side panel) with a black background, set width, and prevent it from resizing
        self.left_panel = tk.Frame(main, bg="black", width=430)
        self.left_panel.pack(side="left", fill="y", padx=(0, 10)) # Place the left panel to the left side with vertical filling
        self.left_panel.pack_propagate(False) # Prevent the left panel from resizing to fit its contents

        # Create the right panel (main content area) with a dark background, set it to fill remaining space
        self.right_panel = tk.Frame(main, bg="#0d1420")
        self.right_panel.pack(side="right", fill="both", expand=True) # Place the right panel to the right side with filling

        # Call methods to build the contents of the left and right panels
        self.build_left_panel()
        self.build_right_panel()

    def line(self, parent):
        # Create a horizontal line (a small frame) with a gray color, used to separate sections visually
        tk.Frame(parent, bg="#333333", height=1).pack(fill="x", pady=5) # Pack the frame as a horizontal line

    def build_left_panel(self):
        # Create the header frame in the left panel with a black background
        header = tk.Frame(self.left_panel, bg="black")
        header.pack(fill="x", pady=(12, 6)) # The header fills horizontally and has vertical padding

        # Create a frame to hold the title and subtitle inside the header
        title_frame = tk.Frame(header, bg="black")
        title_frame.pack()

        # Create the main title label with the stock ticker and an arrow (▼) next to it
        self.title_label = tk.Label(
            title_frame, text=f"{self.ticker_var.get()} ▼", fg="white", bg="black",
            font=("Arial", 24, "bold") # Large, bold font for the title
        )
        self.title_label.pack()

        # Create the subtitle label with the company name based on the selected ticker
        self.subtitle_label = tk.Label(
            title_frame,
            text=self.ticker_name_map.get(self.ticker_var.get(), "Unknown"), # Get the company name from the map
            fg="#bfbfbf", bg="black", font=("Arial", 12) # Lighter gray color for subtitle
        )
        self.subtitle_label.pack()
        
        # Create a frame below the header for the stock selection dropdown
        choose_frame = tk.Frame(self.left_panel, bg="black")
        choose_frame.pack(pady=(10, 10)) # Vertical padding for spacing

        # Create a label prompting the user to select a stock
        tk.Label(
            choose_frame, text="Select Stock:", fg="white", bg="black", font=("Arial", 10)
        ).pack(side="left", padx=5) # The label is placed on the left side of the frame with padding on the right

        # Create a dropdown menu for selecting the stock ticker
        ticker_menu = tk.OptionMenu(
            choose_frame, self.ticker_var, *self.ticker_name_map.keys(), command=self.change_ticker
        ) # The menu will display the tickers from the ticker_name_map dictionary
        ticker_menu.config(
            bg="#1a1a1a", fg="white", activebackground="#333333", activeforeground="white",
            highlightthickness=0, bd=0, width=10
        )
        ticker_menu["menu"].config(bg="#1a1a1a", fg="white")
        ticker_menu.pack(side="left", padx=5) # Place the dropdown menu to the left of the frame

        # Add a horizontal separator line before the quantity section
        self.line(self.left_panel)
        
        # Create the first row for the section title
        row1 = tk.Frame(self.left_panel, bg="black")
        row1.pack(fill="x", padx=20, pady=(8, 0))

        # Display the title for the market execution and quantity control section
        tk.Label(row1, text="Market Execution / Quantity", fg="white", bg="black", font=("Arial", 12)).pack(side="left")

        # Add another horizontal separator line after the title
        self.line(self.left_panel)

        # Create a frame to hold the quantity adjustment buttons and quantity display
        exec_frame = tk.Frame(self.left_panel, bg="black")
        exec_frame.pack(fill="x", padx=10, pady=(8, 10))

        # Define a reusable button style for the quantity control buttons
        btn_style_blue = {
            "bg": "black", "fg": "#2196f3", "activebackground": "black",
            "activeforeground": "#64b5f6", "bd": 1, "relief": "solid",
            "font": ("Arial", 12, "bold"), "width": 5
        }

        # Set the default trading quantity to 15 shares
        self.quantity_var = tk.IntVar(value=15)

        # Button to decrease the trading quantity by 5
        tk.Button(exec_frame, text="-5", command=lambda: self.adjust_quantity(-5), **btn_style_blue).pack(side="left", expand=True)

        # Button to decrease the trading quantity by 1
        tk.Button(exec_frame, text="-1", command=lambda: self.adjust_quantity(-1), **btn_style_blue).pack(side="left", expand=True)

        # Label to display the current selected quantity
        self.execution_value_label = tk.Label(
            exec_frame, text=str(self.quantity_var.get()), fg="white", bg="black",
            font=("Arial", 18, "bold"), width=6
        )
        self.execution_value_label.pack(side="left", expand=True)

        # Button to increase the trading quantity by 1
        tk.Button(exec_frame, text="+1", command=lambda: self.adjust_quantity(1), **btn_style_blue).pack(side="left", expand=True)

        # Button to increase the trading quantity by 5
        tk.Button(exec_frame, text="+5", command=lambda: self.adjust_quantity(5), **btn_style_blue).pack(side="left", expand=True)
        
        # Add a horizontal separator line before the settings section
        self.line(self.left_panel)

        # Build the Stop Loss and Take Profit setting rows
        self.build_setting_row("Stop Loss", "sl")
        self.build_setting_row("Take Profit", "tp")

        # Create a label to show the status message for market price
        self.status_label = tk.Label(
            self.left_panel, text="Waiting for market price...", fg="#cfcfcf", bg="black",
            font=("Arial", 10), wraplength=380, justify="center"
        )
        self.status_label.pack(pady=(15, 15))# Add vertical padding around the label
        
        # Create a frame to hold the buy and sell price labels
        price_frame = tk.Frame(self.left_panel, bg="black")
        price_frame.pack(fill="x", padx=20, pady=(10, 0)) # Horizontal fill, with padding around it

        # Label to display the sell price, with red color for visibility
        self.sell_price_label = tk.Label(
            price_frame, text="--.--", fg="#ff3b30", bg="black", font=("Arial", 28, "bold"), width=8
        )
        self.sell_price_label.pack(side="left", expand=True) # Align it to the left of the frame, with expansion

        # Label to display the buy price, with blue color to indicate buying action
        self.buy_price_label = tk.Label(
            price_frame, text="--.--", fg="#1e90ff", bg="black", font=("Arial", 28, "bold"), width=8
        )
        self.buy_price_label.pack(side="right", expand=True) # Align it to the right of the frame, with expansion

        # Create a frame to hold the bid and ask labels
        spread_frame = tk.Frame(self.left_panel, bg="black")
        spread_frame.pack(fill="x", padx=20, pady=(4, 12)) # Horizontal fill, with padding around it

        # Label to display the "Bid" information with a light red color
        tk.Label(spread_frame, text="Bid", fg="#ff8a80", bg="black", font=("Arial", 11)).pack(side="left", expand=True)

        # Label to display the "Ask" information with a light blue color
        tk.Label(spread_frame, text="Ask", fg="#90caf9", bg="black", font=("Arial", 11)).pack(side="right", expand=True)

        # Create a frame to hold action buttons or controls
        action_frame = tk.Frame(self.left_panel, bg="black")
        action_frame.pack(fill="x", padx=20, pady=(10, 0))  # Horizontal fill, with padding around it
        
        # Sell Button: Initiates the "Sell by Market" action when clicked
        self.sell_button = tk.Button(
            action_frame, text="Sell by Market", bg="#ff3b30", fg="white", font=("Arial", 12, "bold"),
            bd=0, activebackground="#ff5c55", width=18, height=2, command=self.sell_by_market
        )
        self.sell_button.pack(side="left", padx=(0, 5)) # Position the button on the left with padding to the right

        # Buy Button: Initiates the "Buy by Market" action when clicked
        self.buy_button = tk.Button(
            action_frame, text="Buy by Market", bg="#1e90ff", fg="white", font=("Arial", 12, "bold"),
            bd=0, activebackground="#4aa8ff", width=18, height=2, command=self.buy_by_market
        )
        self.buy_button.pack(side="right", padx=(5, 0)) # Position the button on the right with padding to the left

        # Alert Box: A frame for displaying the manual alert section
        alert_box = tk.Frame(self.left_panel, bg="black")
        alert_box.pack(fill="x", padx=20, pady=(18, 0)) # Fill horizontally, with padding on sides and top

        # Label for the alert section
        tk.Label(alert_box, text="Manual Alert", fg="white", bg="black", font=("Arial", 11, "bold")).pack(anchor="w")

        # Alert Row: A frame for the user input area for alert settings
        alert_row = tk.Frame(alert_box, bg="black")
        alert_row.pack(fill="x", pady=(8, 0))# Fill horizontally, with padding on top

        # Entry for user to input price for the alert
        self.alert_price_entry = tk.Entry(alert_row, bg="#1a1a1a", fg="white", insertbackground="white", width=10)
        self.alert_price_entry.pack(side="left", padx=(0, 8))
        
        # Dropdown menu for selecting the type of alert (Above or Below)
        alert_type_menu = tk.OptionMenu(alert_row, self.manual_alert_type, "Above", "Below")
        alert_type_menu.config(bg="#1a1a1a", fg="white", activebackground="#333333", activeforeground="white", bd=0)
        alert_type_menu["menu"].config(bg="#1a1a1a", fg="white") # Configure the dropdown's menu appearance
        alert_type_menu.pack(side="left", padx=(0, 8)) # Position the entry on the left with padding to the right

        # Button to set a manual alert
        tk.Button(
            alert_row, text="Set Alert", command=self.set_manual_alert, # Triggers the 'set_manual_alert' function
            bg="#FFC107", fg="black", bd=0, font=("Arial", 10, "bold"), width=12
        ).pack(side="left") # Positions the button on the left of the row
        
        # Tip label providing instructions for the user about automatic monitoring and manual alerts
        self.tip_label = tk.Label(
            self.left_panel,
            text="SL/TP will be monitored automatically while holding.\nYou can also set a manual price alert.",
            fg="#bcbcbc", bg="black", wraplength=380, justify="center", font=("Arial", 9) # Center-aligned with word wrapping
        )
        self.tip_label.pack(pady=(16, 0)) # Positions the label with padding on top (16) and no padding on the bottom

# =========================
# Price Setting UI Elements
# =========================

    # Function to build a setting row for stop loss or take profit
    def build_setting_row(self, label_text, key):
        frame = tk.Frame(self.left_panel, bg="black") # Create a frame for each setting row
        frame.pack(fill="x", padx=20, pady=5) # Fill horizontally, with padding on sides and top/bottom

        # Label for the setting (e.g., Stop Loss, Take Profit)
        tk.Label(frame, text=label_text, fg="white", bg="black", font=("Arial", 12), width=12, anchor="w").pack(side="left")

        # Button to decrease the price setting value
        tk.Button(frame, text="-", bg="black", fg="#2196f3", bd=1, relief="solid",
                  font=("Arial", 14, "bold"), width=3,
                  command=lambda: self.adjust_price_setting(key, -1)).pack(side="left")

        # Value label to show the current value (initially "not set")
        value_label = tk.Label(frame, text="not set", fg="#9e9e9e", bg="#1a1a1a", font=("Arial", 12), width=12)
        value_label.pack(side="left", expand=True, padx=8)

        # Button to increase the price setting value
        tk.Button(frame, text="+", bg="black", fg="#2196f3", bd=1, relief="solid",
                  font=("Arial", 14, "bold"), width=3,
                  command=lambda: self.adjust_price_setting(key, 1)).pack(side="right")

        # Save the value label based on the key (stop loss or take profit)
        if key == "sl":
            self.stop_loss_value_label = value_label # Store the stop loss value label
        else:
            self.take_profit_value_label = value_label # Store the take profit value label

# =========================
# Build Right Panel Function
# =========================

# Function to build the right panel with a specific style
    def build_right_panel(self):
        style = ttk.Style() # Initialize style object
        style.theme_use("default") # Set the theme to default

        # Configure custom treeview style
        style.configure("Dark.Treeview",
                        background="#081321", # Set background color for the treeview
                        foreground="white", # Set text color for the treeview
                        fieldbackground="#081321", # Set field background color
                        rowheight=40, # Set row height in the treeview
                        borderwidth=0, # Set border width to 0 (flat look)
                        font=("Arial", 10))# Set font style and size for treeview items

        # Customize selection appearance in the treeview
        style.map("Dark.Treeview",
                  background=[("selected", "#13304d")], # Set background color when selected
                  foreground=[("selected", "white")])# Set text color when selected
        
        # Configure heading style for treeview columns
        style.configure("Dark.Treeview.Heading",
                        background="#122235", # Set background color for treeview headings
                        foreground="white", # Set text color for headings
                        relief="flat", # Set flat relief for headings
                        font=("Arial", 10, "bold")) # Set font style for headings
        style.map("Dark.Treeview.Heading",
                  background=[("active", "#18314a")]) # Set active background color for headings

        # =========================
        # Top Bar UI Elements
        # =========================
        
        # Top bar frame containing balance information
        top_bar = tk.Frame(self.right_panel, bg="#1d1f27")
        top_bar.pack(fill="x", padx=14, pady=(12, 8)) # Position the top bar with padding

        # Label displaying the current balance
        self.balance_label = tk.Label(
            top_bar, text=f"Balance: ${self.balance:.2f}", # Format the balance to two decimal places
            font=("Helvetica", 16, "bold"), fg="#ffffff", bg="#1d1f27" # Set font and colors
        )
        self.balance_label.pack(side="left") # Position the balance label on the left side of the top bar

        # Label displaying the current stock price
        self.price_label = tk.Label(
            top_bar, text="Stock Price: $0.00", # Placeholder for stock price
            font=("Helvetica", 15), fg="#ffffff", bg="#1d1f27" # Set font and colors
        )
        self.price_label.pack(side="right") # Position the price label on the right side of the top bar

        # =========================
        # Content Area UI Elements
        # =========================
        
        # Vertically distributed main container (content area)
        content_area = tk.Frame(self.right_panel, bg="#0d1420")
        content_area.pack(fill="both", expand=True, padx=14, pady=(0, 0)) # Fill the area and expand

        # ============================
        # Current Holdings UI Elements
        # ============================
        
        # Label frame for displaying current holdings
        holdings_wrap = tk.LabelFrame(
            content_area, text="Current Holdings", fg="white", bg="#06111d", # Set background and text color
            font=("Helvetica", 12, "bold"), bd=1, relief="solid" # Set border style and font
        )
        holdings_wrap.pack(fill="both", expand=False, padx=0, pady=(0, 8)) # Position the holdings frame
        holdings_wrap.pack_propagate(False) # Prevent the frame from resizing to fit content
        holdings_wrap.configure(height=190) # Set a fixed height for the holdings section

        # Define the columns for the holdings treeview
        columns = ("Ticker", "Stock Name", "Shares", "Average Cost", "Current Price",
           "Market Value", "PnL Amount", "SL", "TP", "Entry Time")

        # Create the treeview to display holdings information
        self.holdings_tree = ttk.Treeview(holdings_wrap, columns=columns, show="headings", style="Dark.Treeview", height=4)
        for col in columns:
            self.holdings_tree.heading(col, text=col) # Set the column headers
            self.holdings_tree.column(col, width=100, anchor="center") # Set column width and alignment
        self.holdings_tree.pack(fill="both", expand=True, padx=8, pady=8) # Position the treeview inside the holdings frame

        # Button frame for actions related to holdings
        btn_frame = tk.Frame(holdings_wrap, bg="#06111d")
        btn_frame.pack(fill="x", padx=8, pady=(0, 8)) # Position the button frame

        # Button to close the selected position
        tk.Button(btn_frame, text="Close Selected Position", command=self.close_selected_position,
                  bg="#e53935", fg="white", bd=0, font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))

        # Button to modify selected SL/TP (Stop Loss / Take Profit)
        tk.Button(btn_frame, text="Modify Selected SL/TP", command=self.modify_selected_sltp,
                  bg="#1976d2", fg="white", bd=0, font=("Arial", 10, "bold")).pack(side="left")

        # =========================
        # Trade History UI Elements
        # =========================

        # Label frame for displaying trade history
        history_wrap = tk.LabelFrame(
            content_area, text="Trade History", fg="white", bg="#06111d", # Set background and text color
            font=("Helvetica", 12, "bold"), bd=1, relief="solid" # Set border style and font
        )
        history_wrap.pack(fill="both", expand=False, padx=0, pady=(0, 8)) # Position the trade history frame
        history_wrap.pack_propagate(False) # Prevent the frame from resizing to fit content
        history_wrap.configure(height=150) # Set a fixed height for the trade history section

        # Top frame for the trade history section
        history_top = tk.Frame(history_wrap, bg="#06111d")
        history_top.pack(fill="x", padx=8, pady=(8, 0)) # Position the top frame for trade history

        # Button to export the trade history to CSV
        tk.Button(
            history_top, text="Export History (CSV)",
            command=self.export_trade_history_csv, # Trigger the export function
            bg="#2f3b52", fg="white", bd=0, font=("Arial", 10, "bold"), width=18
        ).pack(side="right") # Position the button on the right side

        # Define the columns for the trade history treeview
        history_columns = ("Time", "Ticker", "Type", "Quantity", "Price", "Amount", "Fee", "Note")

        # Create the treeview to display trade history
        self.history_tree = ttk.Treeview(history_wrap, columns=history_columns, show="headings", style="Dark.Treeview", height=4)
        for col in history_columns:
            self.history_tree.heading(col, text=col) # Set the column headers
            self.history_tree.column(col, width=100, anchor="center") # Set column width and alignment
        self.history_tree.pack(fill="both", expand=True, padx=8, pady=8) # Position the treeview inside the history frame

        # =========================
        # Chart UI Elements
        # =========================

        # Label frame for displaying the chart section
        chart_wrap = tk.LabelFrame(
            content_area, text="Chart", fg="white", bg="#1d1f27", # Set background and text color
            font=("Helvetica", 12, "bold"), bd=1, relief="solid" # Set border style and font
         )
        chart_wrap.pack(fill="both", expand=True, padx=0, pady=(0, 0)) # Position the chart frame

        # Button frame positioned at the top-right corner of the chart section
        btn_frame = tk.Frame(chart_wrap, bg="#1d1f27")
        btn_frame.pack(side="top", anchor="ne", padx=10, pady=5)  # Anchor to the top-right corner with padding

        # Button to show the chart
        tk.Button(btn_frame, text="⬇ Show Chart", command=self.show_chart, 
                  bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        # Button to compare stocks
        tk.Button(btn_frame, text="📊 Compare Stocks", command=self.open_comparison_window,
                  bg="#9c27b0", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

         # =================================
         # Chart Container with Tooltip Text
         # =================================

        # Frame to hold the chart content
        self.chart_container = tk.Frame(chart_wrap, bg="#1d1f27")
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=10) # Position the container with padding

        # Tooltip label inside the chart container
        hint_label = tk.Label(self.chart_container, 
                              text='Click "Show Chart" to view the chart.', # Instruction text for the user
                              fg="#AAAAAA", bg="#1d1f27", # Set text and background color
                              font=("Arial", 12)) # Set font style
        hint_label.pack(pady=50) # Position the label with padding on top
        
        
    # ==========
    # Core Logic
    # ==========

    # Function to change the selected ticker and update related information
    def change_ticker(self, value):
        ticker = value # Assign the new ticker value
        self.ticker_var.set(value) # Update the ticker variable with the new value
        self.title_label.config(text=f"{value} ▼") # Update the title label with the ticker symbol
        self.subtitle_label.config(text=self.ticker_name_map.get(value, "Unknown Company")) # Update subtitle with the company name or default text if not found

        # Retrieve the holding information for the selected ticker
        holding = self.portfolio.get(value, {}) # Get the holding data for the selected ticker
        self.stop_loss = holding.get("stop_loss") # Get the stop loss value
        self.take_profit = holding.get("take_profit") # Get the take profit value

        # ====================
        # Update SL/TP Display
        # ====================
        
        # Update the stop loss display if it's set, or show "not set"
        if self.stop_loss:
            self.stop_loss_value_label.config(text=f"{self.stop_loss:.2f}", fg="white") # Show stop loss with two decimals
        else:
            self.stop_loss_value_label.config(text="not set", fg="#9e9e9e") # Show "not set" if no stop loss is defined

        # Update the take profit display if it's set, or show "not set"
        if self.take_profit:
            self.take_profit_value_label.config(text=f"{self.take_profit:.2f}", fg="white") # Show take profit with two decimals
        else:
            self.take_profit_value_label.config(text="not set", fg="#9e9e9e") # Show "not set" if no take profit is defined

        # ==============================
        # Refresh Data and Market Price
        # ==============================

        # Refresh the selected price, show chart, and update market price
        self.refresh_selected_price()# Call method to refresh the selected price
        self.show_chart() # Display the updated chart
        self.update_market_price() # Update the market price for the selected ticker
       
    # ==============================
    # Adjust Quantity Function
    # ==============================
    
    # Function to adjust the quantity of stocks
    def adjust_quantity(self, delta):
        qty = self.quantity_var.get() + delta # Adjust the quantity by the delta value
        if qty < 1:
            qty = 1 # Ensure the quantity doesn't go below 1
        self.quantity_var.set(qty) # Update the quantity variable
        self.execution_value_label.config(text=str(qty)) # Update the label with the new quantity

    # ==============================
    # Adjust Price Setting Function
    # ==============================

    # Function to adjust stop loss or take profit values based on setting type
    def adjust_price_setting(self, setting_type, delta):
        if self.last_price is None: # Check if there is no live price available
            self.status_label.config(text="No live price yet, please wait...") # Inform the user
            return

        ticker = self.ticker_var.get() # Get the current ticker
        current_holding = self.portfolio.get(ticker, {}) # Get current holding for the selected ticker
        base_price = round(self.last_price, 2) #Get the base price rounded to two decimal places

        # ==========================
        # Adjust Stop Loss (SL)
        # ==========================
        
        if setting_type == "sl": # If the setting type is "stop loss"
            if self.stop_loss is None:
                self.stop_loss = max(0, base_price - 1) # Set stop loss to 1 below base price if not set
            else:
                self.stop_loss += delta # Otherwise, adjust the stop loss by the delta value
            self.stop_loss = max(0, round(self.stop_loss, 2)) # Ensure stop loss is not less than 0
            self.stop_loss_value_label.config(text=f"{self.stop_loss:.2f}", fg="white") # Update stop loss label
            if ticker in self.portfolio: # If the ticker is in the portfolio
                current_holding["stop_loss"] = self.stop_loss # Update the stop loss in the portfolio

        # ==========================
        # Adjust Take Profit (TP)
        # ==========================
        
        elif setting_type == "tp": # If the setting type is "take profit"
            if self.take_profit is None:
                self.take_profit = base_price + 1 # Set take profit to 1 above base price if not set
            else:
                self.take_profit += delta # Otherwise, adjust the take profit by the delta value
            self.take_profit = max(0, round(self.take_profit, 2)) # Ensure take profit is not less than 0
            self.take_profit_value_label.config(text=f"{self.take_profit:.2f}", fg="white") # Update take profit label
            if ticker in self.portfolio: # If the ticker is in the portfolio
                current_holding["take_profit"] = self.take_profit # Update the take profit in the portfolio

        # Save the updated portfolio after adjustments
        self.save_portfolio() # Call the method to save portfolio data

    # ==================================
    # Get Stock Price from Yahoo Finance
    # ==================================
    def get_stock_price(self, ticker):
        try:
            stock = yf.Ticker(ticker) # Fetch the stock data using Yahoo Finance API
            fast_info = stock.fast_info # Get the fast information of the stock
            if fast_info:
                price = fast_info.get("lastPrice") or fast_info.get("regularMarketPrice") # Get last price or regular market price
                if price:
                    return float(price) # Return the price as a float
        except Exception as e:
            print("Price fetch error:", e) # Print the error if unable to fetch the price
        return None # Return None if the price couldn't be fetched

    # ==========================
    # Refresh Selected Price
    # ==========================
    def refresh_selected_price(self):
        ticker = self.ticker_var.get() # Get the current selected ticker
        price = self.get_stock_price(ticker) # Fetch the stock price for the ticker
        if price is not None:
            fluctuation = random.uniform(-0.02, 0.02)
            self.last_price = round(price + fluctuation, 2) # Update last price
            self.bid_price = round(self.last_price - 0.03, 2) # Set bid price (3 cents below last price)
            self.ask_price = round(self.last_price + 0.03, 2) # Set ask price (3 cents above last price)
            self.price_label.config(text=f"Stock Price: ${self.last_price:.2f}") # Display the stock price
            self.sell_price_label.config(text=f"{self.bid_price:.2f}") # Display the bid price
            self.buy_price_label.config(text=f"{self.ask_price:.2f}") # Display the ask price
            self.last_price = price  
            
        else:
            self.status_label.config(text=f"{ticker}: unable to fetch live price now.") # Show error message if price is unavailable

        print(f"Updated price for {ticker}: {self.last_price}")
        # ==========================
        # Check Stop Loss and Take Profit
        # ==========================
        self.check_sl_tp() # Call method to check if stop loss or take profit has been hit
                    
    # ==========================
    # Update Market Price
    # ==========================
    def update_market_price(self):
        try:
            self.refresh_selected_price() # Refresh the selected price to get the latest market price
            ticker = self.ticker_var.get() # Get the currently selected ticker

            if self.last_price is not None: # If the last price is available
                holding = self.portfolio.get(ticker) # Get the current holding for the ticker
                if holding and holding.get("quantity", 0) > 0: # If there's a holding and quantity is greater than 0
                    buy_price = holding.get("buy_price", 0) # Get the average buy price of the stock
                    qty = holding.get("quantity", 0) # Get the quantity of the holding
                    pnl = (self.bid_price - buy_price) * qty if self.bid_price is not None else 0 # Calculate the profit/loss
                    self.status_label.config(
                        text=f"{ticker} live: {self.last_price:.2f} | Holding: {qty} | Avg Buy: {buy_price:.2f} | P/L: {pnl:.2f}"
                    ) # Update the status label with live price, holding quantity, average buy price, and profit/loss
                else:
                    self.status_label.config(text=f"{ticker} live market price: {self.last_price:.2f}") # Update status if no holdings

                self.check_alerts_for_ticker(ticker) # Check for alerts for the current ticker
                self.check_all_manual_alerts() # Check all manual alerts
            else:
                 self.status_label.config(text=f"{ticker}: unable to fetch live price now, retrying...") # Show message if price fetch fails

            # ==================================
            # Update Holdings and History Tables
            # ==================================
            
            # Update the holdings and history tables with the latest data
            self.update_holdings_table() # Refresh the holdings table with the latest portfolio data
            self.update_history_table() # Refresh the history table with the latest transaction history
            self.balance_label.config(text=f"Balance: ${self.balance:.2f}") # Update the balance display with the current balance

        # ==========================
        # Error Handling and Recursion
        # ==========================
        except Exception as e:
            print("Update error:", e) # Print any errors without stopping the program

        # ==========================
        # Scheduling Next Update
        # ==========================
        finally:
            # Ensures that the function will run again after 1 second
            self.root.after(1000, self.update_market_price) # Schedule the next update in 1 second

    # ==========================
    # Buy by Market Function
    # ==========================
    def buy_by_market(self):
        ticker = self.ticker_var.get() # Get the selected ticker
        qty = self.quantity_var.get() # Get the quantity of shares to buy

        if self.ask_price is None:
            self.status_label.config(text="No live price available yet.") # Show error if the ask price is not available
            return

        total_cost = self.ask_price * qty # Calculate the total cost for the purchase
        if self.balance < total_cost:
            messagebox.showerror("Error", "Insufficient funds.") # Show error if there's not enough balance
            return

        self.balance -= total_cost # Deduct the total cost from the balance

        # If the ticker is not already in the portfolio, add it
        if ticker not in self.portfolio:
            self.portfolio[ticker] = {
                "quantity": 0, # Initialize quantity to 0
                "buy_price": self.ask_price, # Set the buy price to the ask price
                "buy_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # Record the purchase time
                "stop_loss": None, # Initialize stop loss as None
                "take_profit": None, # Initialize take profit as None
            }

        # Get the old quantity and average price of the ticker in the portfolio
        old_qty = self.portfolio[ticker]["quantity"]
        old_avg = self.portfolio[ticker]["buy_price"]
        new_qty = old_qty + qty # New quantity is the old quantity plus the quantity being bought
        new_avg = ((old_qty * old_avg) + (qty * self.ask_price)) / new_qty # Calculate the new average buy price

        # ======================================
        # Update Portfolio and Execute Buy Order
        # ======================================
        # Update the portfolio with the new quantity and average buy price
        self.portfolio[ticker]["quantity"] = new_qty # Update the quantity in the portfolio
        self.portfolio[ticker]["buy_price"] = round(new_avg, 2) # Round the new average buy price to two decimal places
        self.portfolio[ticker]["buy_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Update the purchase time

        # =============================
        # Set Stop Loss and Take Profit
        # =============================

        # If stop loss is not set, initialize it to 1 below the ask price
        if self.stop_loss is None:
            self.stop_loss = round(max(0, self.ask_price - 1), 2) # Ensure stop loss is not less than 0
            self.stop_loss_value_label.config(text=f"{self.stop_loss:.2f}", fg="white") # Update stop loss display

        # If take profit is not set, initialize it to 1 above the ask price
        if self.take_profit is None:
            self.take_profit = round(self.ask_price + 1, 2) # Set take profit to 1 above ask price
            self.take_profit_value_label.config(text=f"{self.take_profit:.2f}", fg="white") # Update take profit display

        # Update the portfolio with the stop loss and take profit values
        self.portfolio[ticker]["stop_loss"] = self.stop_loss # Store the stop loss in the portfolio
        self.portfolio[ticker]["take_profit"] = self.take_profit # Store the take profit in the portfolio

        # ==========================
        # Add Trade History Entry
        # ==========================

        # Record the trade history of the buy transaction
        self.add_trade_history(
            ticker=ticker,
            trade_type="Buy (Open)", # Specify the trade type
            quantity=qty, # Set the quantity of the trade
            price=self.ask_price, # Set the price at which the trade occurred
            amount=-total_cost, # Record the total cost as a negative value (outflow)
            fee=0.00, # No fee for the trade (can be updated later if needed)
            note="Open position" # Add a note for the trade
        )

        # ============================
        # Save Portfolio and Update UI
        # ============================
        self.save_portfolio() # Save the updated portfolio data
        self.update_holdings_table() # Refresh the holdings table with updated data
        self.update_history_table() # Refresh the trade history table with the new trade
        self.balance_label.config(text=f"Balance: ${self.balance:.2f}") # Update the balance display

        # Show status and success message
        self.status_label.config(text=f"BUY {ticker} x{qty} at {self.ask_price:.2f}") # Update the status label with the trade details
        messagebox.showinfo("Success", f"Bought {qty} shares of {ticker} at ${self.ask_price:.2f} each.") # Show success message

    # ==========================
    # Sell by Market Function
    # ==========================
    def sell_by_market(self):
        ticker = self.ticker_var.get() # Get the selected ticker
        qty = self.quantity_var.get() # Get the quantity to sell

        if self.bid_price is None:
            self.status_label.config(text="No live price available yet.") # Show error if bid price is not available
            return

        holding_qty = self.portfolio.get(ticker, {}).get("quantity", 0) # Get the quantity of shares currently held in the portfolio
        if holding_qty < qty:
            messagebox.showerror("Error", f"Not enough shares to sell. You currently hold {holding_qty} shares.") # Show error if trying to sell more than owned
            return

        buy_price = self.portfolio[ticker]["buy_price"] # Get the buy price of the stock
        proceeds = self.bid_price * qty # Calculate the proceeds from the sale (bid price * quantity)
        pnl = (self.bid_price - buy_price) * qty # Calculate the profit or loss from the sale (difference between bid and buy price)

        self.balance += proceeds # Add the proceeds to the balance
        self.portfolio[ticker]["quantity"] -= qty # Reduce the quantity of the stock in the portfolio

        # Record the trade history for the sale
        self.add_trade_history(
            ticker=ticker,
            trade_type="Sell (Close)", # Specify the trade type
            quantity=qty, # Set the quantity of the trade
            price=self.bid_price, # Set the price at which the trade occurred
            amount=proceeds, # Set the proceeds (outflow from balance)
            fee=0.00, # No fee for the trade (can be updated later if needed)
            note="Manual close" # Add a note for the trade
        )

        # If there are no more shares of this ticker in the portfolio, delete it
        if self.portfolio[ticker]["quantity"] == 0:
            del self.portfolio[ticker] # Remove the ticker from the portfolio
            # If the current ticker matches the one being sold, reset the stop loss and take profit
            if self.ticker_var.get() == ticker:
                self.stop_loss = None # Clear stop loss
                self.take_profit = None # Clear take profit
                # Update the UI to reflect the reset values
                self.stop_loss_value_label.config(text="not set", fg="#9e9e9e")
                self.take_profit_value_label.config(text="not set", fg="#9e9e9e")

        # Save the updated portfolio
        self.save_portfolio() # Save portfolio data to the system

        # Update the holdings and history tables with the latest data
        self.update_holdings_table() # Refresh the holdings table
        self.update_history_table() # Refresh the trade history table

        # Update balance display
        self.balance_label.config(text=f"Balance: ${self.balance:.2f}") # Show updated balance

        # Show status and success message
        self.status_label.config(text=f"SELL {ticker} x{qty} at {self.bid_price:.2f} | P/L: {pnl:.2f}") # Display the trade details 

        # Display a success message with profit/loss
        messagebox.showinfo(
            "Position Closed",
            f"Sold {qty} shares of {ticker} at {self.bid_price:.2f}\nP/L: {pnl:.2f}"
        )

    # ==========================
    # Sell by Market (Custom Quantity)
    # ==========================
    def sell_by_market_custom(self, quantity):
        ticker = self.ticker_var.get() # Get the selected ticker
        if ticker not in self.portfolio or self.portfolio[ticker]["quantity"] <= 0:
            return # Exit if no position exists for the selected ticker

        buy_price = self.portfolio[ticker]["buy_price"] # Get the buy price for the ticker
        proceeds = self.bid_price * quantity # Calculate the total proceeds from the sale
        pnl = (self.bid_price - buy_price) * quantity # Calculate the profit or loss from the sale

        self.balance += proceeds # Add the proceeds to the balance
        self.portfolio[ticker]["quantity"] -= quantity # Reduce the quantity in the portfolio

        # If all shares of this ticker are sold, remove it from the portfolio
        if self.portfolio[ticker]["quantity"] <= 0:
            del self.portfolio[ticker]

        # ============================
        # Save Portfolio and Update UI
        # ============================
        
        # Save the updated portfolio
        self.save_portfolio() # Save portfolio data

        # Update the holdings and history tables with the latest data
        self.update_holdings_table() # Refresh the holdings table
        self.update_history_table() # Refresh the trade history table

        # Update balance display
        self.balance_label.config(text=f"Balance: ${self.balance:.2f}") # Show updated balance

    # ==========================
    # Set Stop Loss Function
    # ==========================   
    def set_stop_loss(self):
        ticker = self.ticker_var.get() # Get the selected ticker
        try:
            # Get the stop loss price entered by the user
            sl_price = float(self.sl_entry.get())

            # Validate the stop loss price
            if sl_price <= 0:
                messagebox.showerror("Error", "Please enter a valid price.") # Show error if price is not positive
                return

            # If the ticker is in the portfolio, update the stop loss value
            if ticker in self.portfolio:
                self.portfolio[ticker]["stop_loss"] = round(sl_price, 2) # Set the stop loss to the entered value (rounded)
                self.save_portfolio() # Save the updated portfolio
                self.update_holdings_table() # Refresh the holdings table to reflect the new stop loss
                self.stop_loss_value_label.config(text=f"{sl_price:.2f}", fg="white") # Update the stop loss display in the UI
                messagebox.showinfo("Success", f"Stop Loss set to ${sl_price:.2f}") # Show success message

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.") # Show error if the entered value is not a valid number

    # =================================================================
    # Set Take Profit Function (Placeholder for further implementation)
    # =================================================================
    def set_take_profit(self):
        ticker = self.ticker_var.get() # Get the selected ticker
        try:
            # Get the take profit price entered by the user
            tp_price = float(self.tp_entry.get())

            # Validate the take profit price to ensure it’s positive
            if tp_price <= 0:
                messagebox.showerror("Error", "Please enter a valid price.") # Show error if price is not valid
                return

            # If the ticker is in the portfolio, update the take profit value
            if ticker in self.portfolio:
                self.portfolio[ticker]["take_profit"] = round(tp_price, 2) # Set the take profit to the entered value (rounded)
                self.save_portfolio() # Save the updated portfolio
                self.update_holdings_table() # Refresh the holdings table to reflect the new take profit
                self.take_profit_value_label.config(text=f"{tp_price:.2f}", fg="white") # Update the take profit display in the UI
                messagebox.showinfo("Success", f"Take Profit set to ${tp_price:.2f}") # Show success message

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.") # Show error if the entered value is not a valid number

    # =================================================================
    # Check Stop Loss and Take Profit (Triggers Sell)
    # =================================================================
    def check_sl_tp(self):
         ticker = self.ticker_var.get()
         if ticker not in self.portfolio:
             return

         data = self.portfolio[ticker]
         current_price = self.last_price  # ✅ Fixed variable name
         sl_price = data.get("stop_loss")
         tp_price = data.get("take_profit")
         qty = data.get("quantity", 0)

         print(f"Checking {ticker}: Price={current_price}, SL={sl_price}, TP={tp_price}")
        
        # ==========================
        # Check Stop Loss Trigger
        # ==========================
         if sl_price is not None and current_price <= sl_price:
            msg = f"Stop Loss triggered at ${current_price:.2f}"
            print("✅ " + msg)
            self.notify_user(ticker, msg)  
            messagebox.showwarning("Stop Loss Triggered", f"Price hit ${sl_price:.2f}. Selling all {qty} shares.")
            self.sell_by_market_custom(qty)
            return

        # ==========================
        # Check Take Profit Trigger
        # ==========================
         if tp_price is not None and current_price >= tp_price:
            msg = f"Take Profit triggered at ${current_price:.2f}"
            print("✅ " + msg)
            self.notify_user(ticker, msg)  
            messagebox.showinfo("Take Profit Triggered", f"Price hit ${tp_price:.2f}. Selling all {qty} shares.")
            self.sell_by_market_custom(qty)
            return
        
    # ==========================
    # Close Selected Position
    # ==========================
    def close_selected_position(self):
        selected = self.holdings_tree.selection() # Get the selected holding from the holdings tree
        if not selected:
            messagebox.showwarning("Warning", "Please select a holding first.") # Show warning if no holding is selected
            return

        item = self.holdings_tree.item(selected[0], "values") # Get the details of the selected holding
        ticker = item[0] # Get the ticker of the selected position

        # Check if the ticker exists in the portfolio
        if ticker not in self.portfolio:
            messagebox.showerror("Error", "Selected position no longer exists.") # Show error if the ticker doesn't exist in the portfolio
            return

        qty = self.portfolio[ticker]["quantity"] # Get the quantity of shares for the selected ticker
        self.ticker_var.set(ticker) # Set the ticker variable to the selected ticker
        self.change_ticker(ticker) # Call the change_ticker function to update related UI elements
        self.quantity_var.set(qty) # Set the quantity variable to the number of shares to sell
        self.execution_value_label.config(text=str(qty)) # Update the execution value label with the quantity
        self.sell_by_market() # Call the function to sell the selected position by market

    # =======================================
    # Modify Selected Stop Loss / Take Profit
    # =======================================
    def modify_selected_sltp(self):
        selected = self.holdings_tree.selection() # Get the selected holding from the holdings tree
        if not selected:
            messagebox.showwarning("Warning", "Please select a holding first.") # Show warning if no holding is selected
            return

        item = self.holdings_tree.item(selected[0], "values") # Get the details of the selected holding
        ticker = item[0] # Get the ticker of the selected position
        
        # Check if the ticker exists in the portfolio
        if ticker not in self.portfolio:
            messagebox.showerror("Error", "Selected position no longer exists.") # Show error if the ticker doesn't exist in the portfolio
            return

        current_sl = self.portfolio[ticker].get("stop_loss") # Get the current stop loss value for the ticker
        current_tp = self.portfolio[ticker].get("take_profit") # Get the current take profit value for the ticker

        # Ask user to enter a new stop loss value
        new_sl = simpledialog.askfloat(
            "Modify Stop Loss",
            f"Enter new Stop Loss for {ticker}:",
            initialvalue=current_sl if current_sl is not None else 0.0 # Set initial value to current SL or 0.0
        )
        if new_sl is None:
            return # Exit if the user cancels the input

        # Ask user to enter a new take profit value
        new_tp = simpledialog.askfloat(
            "Modify Take Profit",
            f"Enter new Take Profit for {ticker}:",
            initialvalue=current_tp if current_tp is not None else 0.0 # Set initial value to current TP or 0.0
        )
        if new_tp is None:
            return # Exit if the user cancels the input
         
        # Update the stop loss and take profit in the portfolio
        self.portfolio[ticker]["stop_loss"] = round(new_sl, 2) # Round and set the new stop loss
        self.portfolio[ticker]["take_profit"] = round(new_tp, 2) # Round and set the new take profit

        # If the selected ticker matches the one being modified, update the UI elements for SL/TP
        if self.ticker_var.get() == ticker:
            self.stop_loss = round(new_sl, 2)
            self.take_profit = round(new_tp, 2)
            self.stop_loss_value_label.config(text=f"{self.stop_loss:.2f}", fg="white") # Update the stop loss label
            self.take_profit_value_label.config(text=f"{self.take_profit:.2f}", fg="white") # Update the take profit label

        self.save_portfolio() # Save the updated portfolio
        self.update_holdings_table() # Refresh the holdings table with updated data
        messagebox.showinfo("Success", f"{ticker} SL/TP updated successfully.") # Show success message

    # ==========================
    # Update Holdings Table
    # ==========================
    def update_holdings_table(self):
        # Clear existing rows in the holdings table
        for item in self.holdings_tree.get_children():
            self.holdings_tree.delete(item)

        # Defining Colors for the UI
        self.holdings_tree.tag_configure("profit", foreground="#00FFAA")  # Green for Profit
        self.holdings_tree.tag_configure("loss", foreground="#FF4444")   # Red for Loss

        # Iterate through the portfolio to populate the holdings table
        for ticker, data in self.portfolio.items():
            if isinstance(data, dict) and data.get("quantity", 0) > 0: # Only consider items with quantity > 0
                current_price = self.get_stock_price(ticker) or data.get("buy_price", 0) # Get the current price or buy price
                shares = data["quantity"] # Get the quantity of shares
                avg_cost = data["buy_price"] # Get the average cost of the stock
                market_value = current_price * shares # Calculate market value (current price * quantity)
                pnl_amount = (current_price - avg_cost) * shares # Calculate profit/loss amount
                pnl_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost else 0 # Calculate profit/loss percentage
                entry_time = data.get("buy_time", "Unknown") # Get the time when the stock was bought
                stock_name = self.ticker_name_map.get(ticker, ticker) # Get the stock name from the ticker map
                stop_loss = data.get("stop_loss", "not set") # Get stop loss value
                take_profit = data.get("take_profit", "not set") # Get take profit value

                # Determine Profit and Loss and Set Label
                if pnl_amount >= 0:
                    tag = "profit" # If the profit/loss amount is positive, tag as profit
                    pnl_amount_text = f"${pnl_amount:.2f}" # Format profit/loss amount
                    pnl_pct_text = f"{pnl_pct:.2f}%" # Format profit/loss percentage
                    
                else:
                    tag = "loss" # If the profit/loss amount is negative, tag as loss
                    pnl_amount_text = f"${pnl_amount:.2f}" # Format profit/loss amount
                    pnl_pct_text = f"{pnl_pct:.2f}%" # Format profit/loss percentage

                # Format SL/TP
                sl_text = f"${stop_loss:.2f}" if isinstance(stop_loss, (int, float)) else str(stop_loss)
                tp_text = f"${take_profit:.2f}" if isinstance(take_profit, (int, float)) else str(take_profit)

                # Insert the stock data into the holdings table with the appropriate tags (profit or loss)
                self.holdings_tree.insert(
                    "", "end", # Insert at the end of the table
                    values=(
                        ticker, # Stock ticker
                        stock_name, # Stock name
                        shares, # Quantity of shares
                        f"${avg_cost:.2f}", # Average cost
                        f"${current_price:.2f}", # Current market price
                        f"${market_value:.2f}", # Market value
                        f"${pnl_amount:.2f}", # Profit/loss amount
                        f"${data.get('stop_loss', 0):.2f}" if data.get('stop_loss') is not None else "not set", #Stop Loss
                        f"${data.get('take_profit', 0):.2f}" if data.get('take_profit') is not None else "not set", #Take profit
                        entry_time # Buy time
                    ),
                    tags=(tag,) # Apply the appropriate tag (profit or loss) to the row
                )

    # ==========================
    # Update Price Function
    # ==========================
    def update_price():
        stock = yf.Ticker(stock_symbol) # Create a Ticker object using the stock symbol
        stock_info = stock.history(period="1d") # Get the stock's historical data for the last 1 day
        latest_price = stock_info['Close'].iloc[-1] # Get the latest closing price
        print(f"Fetched new price: {latest_price}") # Print the fetched price for debugging purposes
        price_label.config(text=f"Latest Price: ${latest_price:.2f}") # Update the price label with the new price
    
        # Update the price every second
        root.after(1000, update_price) # Schedule the update_price function to run again after 1 second (1000 milliseconds)

    # ==========================
    # Add Trade History Function
    # ==========================
    def add_trade_history(self, ticker, trade_type, quantity, price, amount, fee=0.0, note=""):
        # Create a record for the trade
        record = {
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # Get the current timestamp in the format (YYYY-MM-DD HH:MM:SS)
            "ticker": ticker, # Stock ticker
            "type": trade_type, # Type of the trade (Buy, Sell, etc.)
            "quantity": quantity, # Number of shares bought/sold
            "price": round(price, 2), # Price of the stock (rounded to two decimal places)
            "amount": round(amount, 2), # Total amount of the trade (rounded to two decimal places)
            "fee": round(fee, 2), # Fee for the trade (rounded to two decimal places)
            "note": note # Additional note for the trade (e.g., "Open position", "Close position")
        }
        self.trade_history.insert(0, record) # Insert the new record at the beginning of the trade history list
        self.trade_history = self.trade_history[:500] # Keep only the latest 500 records, remove older ones

    # ==========================
    # Update Trade History Table
    # ==========================
    def update_history_table(self):
        # Clear existing rows in the history table
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # Iterate through the trade history and insert each record into the table
        for record in self.trade_history:
            trade_type = record.get("type", "") # Get the trade type (Buy, Sell, Alert, etc.)
     
            # Assign appropriate tag based on the trade type
            if "Buy" in trade_type:
                tag = "buy" # Tag as 'buy' if the trade type is 'Buy'
            elif "Sell" in trade_type:
                tag = "sell" # Tag as 'sell' if the trade type is 'Sell'
            else:
                tag = "alert" # Tag as 'alert' for other types of trades (e.g., alerts)

            # Insert the trade record into the history table with formatted values
            self.history_tree.insert(
                "", "end", # Insert at the end of the table
                values=(
                    record.get("time", ""), # Trade time
                    record.get("ticker", ""), # Stock ticker
                    record.get("type", ""), # Trade type (Buy/Sell/Alert)
                    record.get("quantity", ""), # Quantity of shares traded
                    f"{record.get('price', 0):.2f}" if isinstance(record.get("price", 0), (int, float)) else record.get("price", ""), # Price, formatted to two decimal places
                    f"{record.get('amount', 0):.2f}" if isinstance(record.get("amount", 0), (int, float)) else record.get("amount", ""), # Amount, formatted to two decimal places
                    f"{record.get('fee', 0):.2f}" if isinstance(record.get("fee", 0), (int, float)) else record.get("fee", ""), # Fee, formatted to two decimal places
                    record.get("note", "") # Note (additional information about the trade)
                ),
                tags=(tag,) # Apply the appropriate tag (buy, sell, or alert)
            )

    # ===========================
    # Export Trade History to CSV
    # ===========================
    def export_trade_history_csv(self):
        # Check if there is any trade history to export
        if not self.trade_history:
            messagebox.showwarning("Warning", "No trade history to export.") # Show a warning if no trade history is available
            return
        
        # Prompt the user to choose a file location to save the CSV
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", # Set the default file extension to CSV
            filetypes=[("CSV files", "*.csv")], # Allow only CSV files to be saved
            title="Save Trade History" # Set the dialog window title
        )

        # If no file path is provided (user cancels the save), return
        if not file_path:
            return

        try:
            # Open the file in write mode with UTF-8 encoding (including BOM for compatibility with Excel)
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f) # Create a CSV writer object
                # Write the header row
                writer.writerow(["Time", "Ticker", "Type", "Quantity", "Price", "Amount", "Fee", "Note"])
                # Write each trade record into the CSV file
                for record in self.trade_history:
                    writer.writerow([
                        record.get("time", ""), # Get the trade time
                        record.get("ticker", ""), # Get the ticker symbol
                        record.get("type", ""), # Get the trade type (Buy, Sell, etc.)
                        record.get("quantity", ""), # Get the quantity of shares traded
                        record.get("price", ""), # Get the price at which the trade occurred
                        record.get("amount", ""), # Get the total amount of the trade
                        record.get("fee", ""), # Get the fee for the trade
                        record.get("note", "") # Get any additional notes about the trade
                    ])
            # Show a success message after exporting the history
            messagebox.showinfo("Success", "Trade history exported successfully.")
        except Exception as e:
            # If an error occurs during export, show an error message
            messagebox.showerror("Error", f"Export failed:\n{e}")

    # =========================
    # Alerts
    # =========================
    def set_manual_alert(self):
        ticker = self.ticker_var.get() # Get the selected ticker
        try:
            # Get the alert price entered by the user
            alert_price = float(self.alert_price_entry.get().strip()) # Strip any extra spaces and convert to float
        except ValueError:
            # Show error if the input is not a valid number
            messagebox.showerror("Error", "Please enter a valid alert price.")
            return

        # Get the alert type (Above or Below)
        alert_type = self.manual_alert_type.get()

        # Store the alert in the price_alerts dictionary
        self.price_alerts[ticker] = {"price": alert_price, "type": alert_type}

        # Save the updated portfolio with the new alert
        self.save_portfolio()

        # Show success message
        messagebox.showinfo("Success", f"Price alert set for {ticker}: {alert_type} ${alert_price:.2f}")

# ======================================
# Check Stop Loss and Take Profit Alerts
# ======================================
    def check_alerts_for_ticker(self, ticker):
        # Check if the ticker exists in the portfolio and if the last price is available
        if ticker not in self.portfolio or self.last_price is None:
            return # Exit if no ticker is found or no live price is available

        holding = self.portfolio[ticker] # Get the portfolio data for the selected ticker

        # Get the current stop loss and take profit values
        current_sl = holding.get("stop_loss")
        current_tp = holding.get("take_profit")

        # ==========================
        # Check Stop Loss Trigger
        # ==========================
        if current_sl is not None and self.last_price <= current_sl:
            # If the stop loss is triggered (current price is less than or equal to stop loss)
            self.add_trade_history(ticker, "Stop Loss Alert", holding.get("quantity", 0), current_sl, 0.0, 0.0, "Triggered stop loss alert") # Add trade history for SL alert
            self.notify_user(ticker, f"Stop Loss triggered at ${self.last_price:.2f} (SL: {current_sl:.2f})") # Notify the user about the SL trigger
            holding["stop_loss"] = None # Reset stop loss after triggering
            # If the current ticker is the one triggered, reset the stop loss UI values
            if self.ticker_var.get() == ticker:
                self.stop_loss = None
                self.stop_loss_value_label.config(text="not set", fg="#9e9e9e") # Update the UI to show that stop loss is not set

        # ==========================
        # Check Take Profit Trigger
        # ==========================
        if current_tp is not None and self.last_price >= current_tp:
            # If the take profit is triggered (current price is greater than or equal to take profit)
            self.add_alert_history(ticker, "Take Profit", current_tp, self.last_price, "TP triggered") # Add alert history for TP
            self.add_trade_history(ticker, "Take Profit Alert", holding.get("quantity", 0), current_tp, 0.0, 0.0, "Triggered take profit alert") # Add trade history for TP alert
            self.notify_user(ticker, f"Take Profit triggered at ${self.last_price:.2f} (TP: {current_tp:.2f})") # Notify the user about the TP trigger
            holding["take_profit"] = None # Reset take profit after triggering
            # If the current ticker is the one triggered, reset the take profit UI values
            if self.ticker_var.get() == ticker:
                self.take_profit = None
                self.take_profit_value_label.config(text="not set", fg="#9e9e9e") # Update the UI to show that take profit is not set

        # Save the updated portfolio after checking alerts
        self.save_portfolio() # Save the portfolio with the updated values (SL and TP)

    # =================================================
    # Check All Manual Alerts (Stop Loss / Take Profit)
    # =================================================
    def check_all_manual_alerts(self):
        current_price = self.last_price # Get the current price (latest price)
        if current_price is None:
            return # Exit if there is no live price available

        # Iterate through all positions in the portfolio
        for ticker, data in self.portfolio.items():
            shares = data.get("shares", 0) # Get the number of shares for the ticker
            if shares <= 0:
                continue # Skip if there are no shares held
            
            sl_price = data.get("stop_loss") # Get the stop loss price
            tp_price = data.get("take_profit") # Get the take profit price

            # ===== Check for Stop Loss Trigger =====
            if sl_price is not None and current_price <= sl_price:
                # If the current price is less than or equal to the stop loss, trigger stop loss
                self.sell_by_market(ticker, shares, reason="Stop Loss") # Sell the position (market order)
                # Clear the triggered stop loss and take profit
                data["stop_loss"] = None
                data["take_profit"] = None
                self.save_portfolio() # Save the portfolio after the trade
                self.update_holdings_table() # Refresh the holdings table to reflect the changes

            # ===== Check for Take Profit Trigger =====
            elif tp_price is not None and current_price >= tp_price:
                # If the current price is greater than or equal to the take profit, trigger take profit
                self.sell_by_market(ticker, shares, reason="Take Profit")  # Sell the position (market order)
                # Clear the triggered stop loss and take profit
                data["stop_loss"] = None
                data["take_profit"] = None
                self.save_portfolio() # Save the portfolio after the trade
                self.update_holdings_table() # Refresh the holdings table to reflect the changes
                
        # Save the portfolio data after all checks
        self.save_portfolio()# Ensure portfolio data is saved after processing all alerts

    # ==========================
    # Notify User (Price Alert)
    # ==========================
    def notify_user(self, ticker, message):
         print(f"🔔 NOTIFICATION: {ticker} - {message}")
         self.root.bell()  
         winsound.Beep(1000, 500)
        
         ctypes.windll.user32.MessageBoxW(0, message, f"Price Alert: {ticker}", 0)

    # =======================================
    # Persistence (Backup and Save Portfolio)
    # =======================================
    def backup_data(self):
        # Check if the portfolio data file exists
        if os.path.exists("portfolio.json"):
            # If the file exists, create a backup of the portfolio file
            shutil.copy("portfolio.json", "portfolio_backup.json") # Copy the file to a backup file

    def save_portfolio(self):
        # Prepare the data to be saved into the portfolio file
        payload = {
            "cash": self.balance, # User's current balance
            "stocks": self.portfolio, # User's stock portfolio
            "price_alerts": self.price_alerts, # User's price alerts
            "trade_history": self.trade_history, # User's trade history
        }

        # Use the username as the filename to avoid permission issues
        filename = f"portfolio_{current_user}.json" # Create a filename based on the current user's name

        # Open the file in write mode and save the data in JSON format
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2) # Write the data to the file with indented formatting

    # =============================
    # Load Portfolio Data from File
    # =============================
    def load_portfolio(self):
        # Generate the filename based on the current user's name
        filename = f"portfolio_{current_user}.json"

        # Check if the portfolio file exists
        if os.path.exists(filename):
            try:
                # Open and read the portfolio file
                with open(filename, "r", encoding="utf-8") as file:
                    # Load the data from the JSON file
                    data = json.load(file)

                    # Load individual data fields from the file or set default values if they are missing
                    self.balance = data.get("balance", self.default_balance) # User's balance, or default if not found
                    self.portfolio = data.get("portfolio", {}) # User's stock portfolio, or empty if not found
                    self.price_alerts = data.get("price_alerts", {}) # User's price alerts, or empty if not found
                    self.trade_history = data.get("trade_history", []) # User's trade history, or empty if not found

            except Exception as e:
                # If there's an error loading the file, print the error and reset data to default values
                print("Load error:", e)
                self.balance = self.default_balance
                self.portfolio = {}
                self.price_alerts = {}
                self.trade_history = []
                
        else:
            # If the file doesn't exist, initialize the portfolio with default values
            self.balance = self.default_balance
            self.portfolio = {}
            self.price_alerts = {}
            self.trade_history = []

    # ==========================
    # Get Stock Data for Chart
    # ==========================
    def get_stock_data(self, ticker):
        # Download the stock data for the last 30 days with a daily interval using yfinance
        return yf.download(ticker, period="30d", interval="1d", progress=False) # Fetch stock data for charting

    # ==========================
    # Plot Candlestick Chart
    # ==========================
    def plot_candlestick_chart(self, stock_data, ticker):
        # Check if stock data is available and not empty
        if stock_data is None or stock_data.empty:
            messagebox.showerror("Error", f"No chart data available for {ticker}.") # Show error if no data is available
            return

        # If stock data has a MultiIndex, flatten the columns
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_data.columns = stock_data.columns.get_level_values(0)

        # Clean up column names by stripping extra spaces
        stock_data.columns = stock_data.columns.str.strip()

        # Define the required columns for the candlestick chart
        required_columns = ["Open", "Close", "High", "Low"]

        # Check if any required columns are missing
        missing_columns = [col for col in required_columns if col not in stock_data.columns]
        if missing_columns:
            messagebox.showerror("Error", f"Missing columns: {', '.join(missing_columns)}") # Show error if columns are missing
            return

        # Drop rows with missing values in the required columns
        stock_data = stock_data.dropna(subset=required_columns)

        # Check if data is empty after cleaning
        if stock_data.empty:
            messagebox.showerror("Error", "Chart data is empty after cleaning.") # Show error if data is empty
            return
        
        # Separate data into 'up' (bullish) and 'down' (bearish) days
        up = stock_data[stock_data["Close"] >= stock_data["Open"]] # Bullish days where closing price is higher than opening
        down = stock_data[stock_data["Close"] < stock_data["Open"]] # Bearish days where closing price is lower than opening

        # Create a figure and axis for plotting the candlestick chart
        fig, ax = plt.subplots(figsize=(8.5, 4.5)) # Set the size of the chart
        ax.set_facecolor("#1d1f27") # Set the background color of the plot area
        fig.patch.set_facecolor("#1d1f27") # Set the background color of the figure

        # Plot bullish candlesticks (green)
        ax.bar(up.index, up["Close"] - up["Open"], width=0.6, bottom=up["Open"], color="green") # Plot the body of the candlestick
        ax.bar(up.index, up["High"] - up["Close"], width=0.08, bottom=up["Close"], color="green") # Plot the upper wick
        ax.bar(up.index, up["Low"] - up["Open"], width=0.08, bottom=up["Open"], color="green") # Plot the lower wick

        # Plot bearish candlesticks (red)
        ax.bar(down.index, down["Close"] - down["Open"], width=0.6, bottom=down["Open"], color="red") # Plot the body of the candlestick
        ax.bar(down.index, down["High"] - down["Open"], width=0.08, bottom=down["Open"], color="red") # Plot the upper wick
        ax.bar(down.index, down["Low"] - down["Close"], width=0.08, bottom=down["Close"], color="red") # Plot the lower wick

        # Add labels and title to the chart
        ax.set_xlabel("Date", color="white") # X-axis label (Date)
        ax.set_ylabel("Price ($)", color="white")# Y-axis label (Price in dollars)
        ax.set_title(f"{ticker} Stock Price Over Last 30 Days", color="white") # Title of the chart

        # Customize tick parameters (color)
        ax.tick_params(colors="white") # Set the color of the ticks

        # Set the color of the plot spines (edges of the chart)
        for spine in ax.spines.values():
            spine.set_color("white") # Set the spine color to white for consistency with the theme

        # ===== Key: Set Date Format =====
        import matplotlib.dates as mdates # Import matplotlib's date formatting utilities

        # Set the major formatter for the x-axis to display dates in "MM-DD" format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

        # Set the major locator for the x-axis to display a tick every 7 days
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=7)) # Display a tick every 7 days

        # Automatically format the x-axis labels to avoid overlapping
        fig.autofmt_xdate()

        # Adjust the layout of the figure to prevent clipping of labels
        fig.tight_layout()

        # ===========================================
        # Handling Existing Chart and Drawing New One
        # ===========================================
        
        # If there is already a chart displayed, destroy the existing widget before drawing a new one
        if self.chart:
            self.chart.get_tk_widget().destroy() # Remove the existing chart widget from the container

        # Create a new FigureCanvasTkAgg widget to display the chart in the tkinter window
        self.chart = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.chart.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8) # Pack the new chart widget into the container
        self.chart.draw() # Draw the chart on the canvas

        # ==============================
        # Clear Old Widgets in Container
        # ==============================
        
        # Clear the old content in the container
        for widget in self.chart_container.winfo_children():
            widget.destroy() # Destroy each widget inside the chart container to prepare for the new chart

        # Finally, draw the chart in the fixed container again (this seems to be redundant, as it's already packed above)
        self.chart = FigureCanvasTkAgg(fig, master=self.chart_container) # Recreate the canvas
        self.chart.get_tk_widget().pack(fill="both", expand=True) # Pack it into the container again
        self.chart.draw() # Draw the chart again (probably redundant as it's already done earlier)

    # ================================
    # Show Chart (Handle User Request)
    # ================================
    def show_chart(self):
        ticker = self.ticker_var.get().upper() # Get the ticker symbol and convert it to uppercase
        if not ticker:
            messagebox.showerror("Error", "Please select a valid ticker.") # Show an error if no valid ticker is selected
            return

        # Fetch the stock data for the specified ticker
        stock_data = self.get_stock_data(ticker)

        # Plot the candlestick chart with the fetched stock data
        self.plot_candlestick_chart(stock_data, ticker)

# ==========================
# Login Functionality
# ==========================
def login_user():
    username = username_entry.get().strip() # Get and clean up the username input
    password = password_entry.get().strip() # Get and clean up the password input

    # Load users from the saved data
    users = load_users()

    # Check if the username exists and the password matches
    if username not in users or users[username] != password:
        messagebox.showerror("Error", "Invalid username or password.") # Show error if invalid
        return

    global current_user # Declare current_user as a global variable
    current_user = username # Set the current user to the logged-in username
    login_frame.destroy() # Destroy the login frame as user has logged in

    # Load portfolio data for the logged-in user
    portfolio_data = load_portfolio(username)

    # Create and initialize the main application window for the user with their portfolio data
    app = FusionTradingApp(root, portfolio_data)
       
# =============================
# Signup UI (User Registration)
# =============================
def signup():
    # Get the input values from the username, password, and password confirm fields
    username = username_entry.get().strip() # Get and clean up the username input
    password = password_entry.get().strip() # Get and clean up the password input
    password_confirm = password_confirm_entry.get().strip() # Get and clean up the password confirmation input

    # Check if any of the fields are empty
    if not username or not password:
        messagebox.showerror("Error", "Please fill all fields.") # Show an error if any fields are empty
        return

    # Check if the password and password confirmation match
    if password != password_confirm:
        messagebox.showerror("Error", "Passwords do not match.") # Show an error if the passwords don't match
        return

    # Load existing users from the data file
    users = load_users()

    # Check if the username already exists
    if username in users:
        messagebox.showerror("Error", "Username already exists.") # Show an error if the username is already taken

        return

    # If the username doesn't exist, add it to the users dictionary
    users[username] = password
    save_users(users)

    # Show a success message
    messagebox.showinfo("Success", "Account created successfully! You can now login.") # Inform the user that the account has been created

# =========================
# Login UI
# =========================
def show_login_screen():
    global login_frame, username_entry, password_entry, password_confirm_entry, email_entry

    # Load the background image and stretch it to cover the entire window
    bg_image = Image.open("login_bg.jpg") # Open the image
    bg_image = bg_image.resize((root.winfo_screenwidth(), root.winfo_screenheight()), Image.LANCZOS) # Resize it to fill the screen
    bg_photo = ImageTk.PhotoImage(bg_image) # Convert the image to a format that can be used in Tkinter

    # Create a frame to hold the login screen
    login_frame = tk.Frame(root)
    login_frame.pack(fill="both", expand=True) # Make the frame fill the entire window

    # Add the background image as a label
    bg_label = tk.Label(login_frame, image=bg_photo) # Create a label with the background image
    bg_label.image = bg_photo # Keep a reference to the image to prevent it from being garbage collected
    bg_label.place(x=0, y=0, relwidth=1, relheight=1) # Place the background label to cover the entire frame

    # =========================
    # Top Logo and Title
    # =========================
    top_frame = tk.Frame(login_frame, bg="black") # Create a top frame with a black background
    top_frame.place(relx=0.5, rely=0.16, anchor="center") # Position it at the top center of the login screen

    # Add a logo to the top frame (an emoji in this case)
    logo_label = tk.Label(top_frame, text="📉", font=("Arial", 48), bg="black", fg="#4A90E2") # Logo in blue
    logo_label.pack() # Pack the logo

    # Add the main title of the login screen
    title_label = tk.Label(top_frame, text="Fusion Stock Trading", font=("Arial", 28, "bold"), bg="black", fg="white")
    title_label.pack(pady=(8, 2)) # Add some padding around the title

    # Add a subtitle to describe the purpose of the application
    subtitle_label = tk.Label(top_frame, text="Trade Smarter. Grow Faster.", font=("Arial", 12), bg="black", fg="#E0E0E0")
    subtitle_label.pack() # Display the subtitle

    # =========================
    # Central Login Box
    # =========================
    login_box = tk.Frame(login_frame, bg="white", bd=0, relief="solid") # Create a white frame for the login form
    login_box.place(relx=0.5, rely=0.5, anchor="center") # Position the login box at the center of the screen
    login_box.config(padx=50, pady=40) # Add padding inside the login box

    # Title row with a green leaf emoji and bold text
    header_frame = tk.Frame(login_box, bg="white") # Create a header frame for the title
    header_frame.pack(fill="x", pady=(0, 20)) # Fill the width and add padding below the header
    tk.Label(header_frame, text="🍃", font=("Arial", 16), bg="white", fg="#2ECC71").pack(side="left") # Green leaf emoji
    tk.Label(header_frame, text="Please Enter Your Information", 
             font=("Arial", 16, "bold"), bg="white", fg="#2C3E50").pack(side="left", padx=(8, 0)) # Bold text for the header

    # Add a separator line below the header
    tk.Frame(login_box, height=1, bg="#BDC3C7").pack(fill="x", pady=(0, 25))

    # =========================================
    # Utility Function: Add Placeholder Effect
    # =========================================
    def add_placeholder(entry, placeholder_text, is_password=False):
        entry.insert(0, placeholder_text) # Insert the placeholder text
        entry.config(fg="#95A5A6") # Set the placeholder color to gray
        if is_password: # If it's a password field, ensure the input is hidden initially
            entry.config(show="")

        # Function to clear the placeholder text when the field is focused
        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END) # Clear the placeholder text
                entry.config(fg="#2C3E50") # Change text color to dark gray
                if is_password:
                    entry.config(show="*") # Show password input as asterisks

        # Function to restore the placeholder text if the field is empty and unfocused
        def on_focus_out(event):
            if entry.get().strip() == "": # If the field is empty
                entry.insert(0, placeholder_text) # Reinsert the placeholder text
                entry.config(fg="#95A5A6") # Change text color back to gray
                if is_password:
                    entry.config(show="") # Hide password input again

        # Bind focus events to trigger the placeholder logic
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
    # -------------------------------------------

    # Login ID input field
    id_frame = tk.Frame(login_box, bg="white") # Create a frame for the Login ID input
    id_frame.pack(fill="x", pady=(0, 20)) # Pack the frame with padding below it
    tk.Label(id_frame, text="👤", font=("Arial", 16), bg="white", fg="#3498DB").pack(side="left", padx=(0, 12)) # User icon
    username_entry = tk.Entry(id_frame, font=("Arial", 14), width=30, 
                              bd=1, relief="solid", bg="#F8F9FA") # Create an entry field for the Login ID
    username_entry.pack(side="left", fill="x", expand=True) # Pack the entry field to expand in the frame
    add_placeholder(username_entry, "Login ID") # Add placeholder text for the entry field
    username_entry.config(highlightbackground="#3498DB", highlightcolor="#3498DB", highlightthickness=2) # Add border color

    # =========================================
    # Password Section
    # =========================================
    pwd_frame = tk.Frame(login_box, bg="white") # Create a frame for the password input
    pwd_frame.pack(fill="x", pady=(0, 25)) # Pack the frame with padding below it
    tk.Label(pwd_frame, text="🔒", font=("Arial", 16), bg="white", fg="#7F8C8D").pack(side="left", padx=(0, 12)) # Lock icon
    password_entry = tk.Entry(pwd_frame, font=("Arial", 14), width=30, 
                              bd=1, relief="solid", bg="#F8F9FA") # Create an entry field for the password
    password_entry.pack(side="left", fill="x", expand=True) # Pack the entry field to expand in the frame
    add_placeholder(password_entry, "Password", is_password=True) # Add placeholder text for the password field
    password_entry.config(highlightbackground="#BDC3C7", highlightcolor="#BDC3C7", highlightthickness=2) # Set border color for the entry field

    # =========================================
    # Email Section (Visible During Sign Up)
    # =========================================
    email_frame = tk.Frame(login_box, bg="white") # Create a frame for the email input
    tk.Label(email_frame, text="📧", font=("Arial", 16), bg="white", fg="#3498DB").pack(side="left", padx=(0, 12)) # Email icon
    email_entry = tk.Entry(email_frame, font=("Arial", 14), width=30, 
                           bd=1, relief="solid", bg="#F8F9FA") # Create an entry field for the email
    email_entry.pack(side="left", fill="x", expand=True) # Pack the entry field to expand in the frame
    add_placeholder(email_entry, "Email") # Add placeholder text for the email field
    email_entry.config(highlightbackground="#BDC3C7", highlightcolor="#BDC3C7", highlightthickness=2) # Set border color for the entry field

    # ============================================
    # Confirm Password Section (Hidden By Default)
    # ============================================
    confirm_frame = tk.Frame(login_box, bg="white") # Create a frame for the confirm password input
    tk.Label(confirm_frame, text="🔐", font=("Arial", 16), bg="white", fg="#7F8C8D").pack(side="left", padx=(0, 12)) # Confirm lock icon
    password_confirm_entry = tk.Entry(confirm_frame, font=("Arial", 14), width=30, 
                                      bd=1, relief="solid", bg="#F8F9FA") # Create an entry field for confirm password
    password_confirm_entry.pack(side="left", fill="x", expand=True) # Pack the entry field to expand in the frame
    add_placeholder(password_confirm_entry, "Confirm Password", is_password=True) # Add placeholder text for the confirm password field
    password_confirm_entry.config(highlightbackground="#BDC3C7", highlightcolor="#BDC3C7", highlightthickness=2) # Set border color for the entry field

    # =========================================
    # Switch Between Signup and Login Mode
    # =========================================
    def show_signup_mode():
        email_frame.pack(fill="x", pady=(0, 25)) # Show email input field in sign-up mode
        confirm_frame.pack(fill="x", pady=(0, 25)) # Show confirm password field in sign-up mode

    def show_login_mode():
        email_frame.pack_forget() # Hide email input field in login mode
        confirm_frame.pack_forget() # Hide confirm password field in login mode

    # =========================================
    # Clear Input Fields
    # =========================================
    def clear_entries():
        username_entry.delete(0, tk.END) # Clear the username input field
        password_entry.delete(0, tk.END) # Clear the password input field
        email_entry.delete(0, tk.END) # Clear the email input field
        password_confirm_entry.delete(0, tk.END) # Clear the confirm password input field
        add_placeholder(username_entry, "Login ID") # Reset placeholder for username
        add_placeholder(password_entry, "Password", True) # Reset placeholder for password
        add_placeholder(email_entry, "Email") # Reset placeholder for email
        add_placeholder(password_confirm_entry, "Confirm Password", True) # Reset placeholder for confirm password

    

    # =========================================
    # Functionality Logic
    # =========================================
    # Login Functionality
    def login_user():
        username = username_entry.get().strip() # Get the username from the input field
        password = password_entry.get().strip() # Get the password from the input field

        users = load_users() # Load user data
        if username not in users or users[username] != password: # Check if the username and password match
            messagebox.showerror("Error", "Invalid username or password.") # Show error if invalid
            return
 
        global current_user # Declare a global variable for the current user
        current_user = username # Set the current user
        login_frame.destroy() # Destroy the login frame after successful login
        portfolio_data = load_portfolio(username) # Load portfolio data for the user
        app = FusionTradingApp(root, portfolio_data) # Create a new instance of the app with user portfolio
        
    # =========================================
    # Sign Up
    # =========================================
    def signup():
        username = username_entry.get().strip() # Get the username from the input field
        password = password_entry.get().strip() # Get the password from the input field
        password_confirm = password_confirm_entry.get().strip() # Get the confirm password from the input field
    
        # Check if any of the fields are empty
        if not username or not password:
            messagebox.showerror("Error", "Please fill all fields.") # Show error if any field is empty
            return

        # Check if passwords match
        if password != password_confirm:
            messagebox.showerror("Error", "Passwords do not match.") # Show error if passwords don't match
            return

        users = load_users() # Load existing users data
        if username in users: # Check if the username already exists
            messagebox.showerror("Error", "Username already exists.") # Show error if username already exists
            return

        users[username] = password # Add the new user with their password
        save_users(users) # Save the updated users data
        messagebox.showinfo("Success", "Account created successfully! You can now login.") # Show success message

    # =========================================
    # Check if User Exists
    # =========================================      
    def is_user_exists(user_id):
        try:
            with open("users.txt", "r") as f: # Try to open the users.txt file in read mode
                 for line in f:
                     parts = line.strip().split(",") # Split each line by comma
                     if len(parts) >= 1 and parts[0] == user_id: # Check if the user_id matches
                         return True # Return True if the user exists
        except:
            pass # Ignore any errors (e.g., file not found)
        return False # Return False if the user does not exist

    # =========================================
    # Save User Data to File
    # =========================================
    def save_user(user_id, password):
         with open("users.txt", "a") as f: # Open the users.txt file in append mode
             f.write(f"{user_id},{password}\n") # Write the user data to the file
             

    # =========================================
    # Buttons Section
    # =========================================
    btn_frame = tk.Frame(login_box, bg="white") # Create a frame for the buttons
    btn_frame.pack(fill="x", pady=(10, 0)) # Pack the button frame with some padding

    # Login Button
    login_btn = tk.Button(
        btn_frame,
        text="🔍 Login", # Text displayed on the login button
        command=lambda: [show_login_mode(), login_user()], # Action to show login mode and login the user
        font=("Arial", 14, "bold"),
        bg="#2166F3", # Button background color
        fg="white", # Button text color
        bd=0,
        relief="flat", # Flat style for the button
        width=22 # Button width
    )
    login_btn.pack(pady=(0, 12)) # Pack the login button with padding

    # Sign Up Button
    signup_btn = tk.Button(
        btn_frame,
        text="📝 Sign Up", # Text displayed on the sign-up button
        command=lambda: [show_signup_mode(), signup()], # Action to show sign-up mode and create a new user
        font=("Arial", 14, "bold"),
        bg="#28A745", # Button background color
        fg="white", # Button text color
        bd=0,
        relief="flat", # Flat style for the button
        width=22 # Button width
    )
    signup_btn.pack() # Pack the sign-up button

# =========================
# Main Entry Point
# =========================
if __name__ == "__main__": # Check if this script is being run directly
    root = tk.Tk() # Initialize the Tkinter root window
    root.title("Fusion Trading App") # Set the title of the window
    root.geometry("1400x860")  # Set the window size (make sure it's large enough for the interface)
    root.configure(bg="#111111") # Set the background color of the window

    show_login_screen() # Call the function to display the login screen

    root.mainloop() # Start the Tkinter event loop to display the window and handle user interactions


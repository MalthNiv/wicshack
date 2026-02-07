import yfinance as yf
import json

# Map company names to tickers
companies = {
    "The Trade Desk": "TTD",
    "Bumble": "BMBL",
    "CapitalOne": "COF",
    "DraftKings": "DKNG",
    "Chevron": "CVX",
    "Roblox": "RBLX",
    "Coinbase": "COIN",
    "JP Morgan": "JPM",
    "Spotify": "SPOT",
    "Macy’s": "M"
}

# Dictionary to store daily prices
stock_data = {}
sd_array = []

for name, ticker in companies.items():
    print(f"Fetching data for {name} ({ticker})...")
    stock = yf.Ticker(ticker)
    
    # Get 1 year of daily data
    hist = stock.history(period="1y")
    
    # Keep only 'Close' price
    daily_prices = hist['Close'].dropna().tolist()
    
    # Compute daily returns
    daily_returns = hist['Close'].pct_change().dropna()
    
    # Compute standard deviation of daily returns
    sd = daily_returns.std()
    sd_array.append({"name": name, "ticker": ticker, "standard_deviation": sd})
    
    # Store daily prices
    stock_data[name] = daily_prices

# Save results to JSON
output = {
    "daily_prices": stock_data,
    "standard_deviations": sd_array
}

with open("stocks_daily_prices.json", "w") as f:
    json.dump(output, f, indent=4)

print("Done! Daily prices and standard deviations saved to 'stocks_daily_prices.json'")

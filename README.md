# NOW YOU HEAR ME

A web app that turns stock price data into music and visualizes it. You can choose a stock from a spinning record, and its price history will draw itself on screen — synced to a generated audio track, created by analyzing the performance and volatility of the stock.

## How It Works

1. Choose a stock from the spinning record player on the home page
2. Hit PLAY & SYNC on the stock's detail page
3. Watch and listen as the price chart draws in real time, aligning with the music

The graph line glows brighter and gets thicker when the bass hits harder. Blue segments mean the price went up; pink means it went down.

## Tech Stack

- SerpAPI - Used to gather 1 year’s worth of pricing data for the 10 stocks on the record
- Yahoo Finance - Extract news for sentiment analysis
- TextBlob - NLP processing for sentiment analysis
- Soundfonts - Collection of synth and EDM sounds for the actual music
- NumPy - To perform all calculations to determine volatility, price changes, and stock return over rolling windows
- MIDIFile - Python library to write out soundfonts to a playable MIDI file
- React — Component-based UI (record player, floating notes, graph, cursor glow)
- TypeScript — Builds the actual components for the frontend
- Vite — Build tool and dev server

## Key Features

- Audio visualization — The `StockAnimator` analyzes audio in real time and matches audio with the graph.
- Synced playback — Chart progress is tied directly to the music progress
- Record UI — Stock tickers are arranged on a CSS-rendered record with groove lines, spinning animation, and sound wave ripples
- Consistent gradient theme — Light blue to dark blue to purple to pink, applied across titles, borders, floating notes, and glows

## Stocks Included

| Symbol | Company        |
|--------|----------------|
| TTD    | The Trade Desk |
| BMBL   | Bumble         |
| COF    | CapitalOne     |
| DKNG   | DraftKings     |
| CVX    | Chevron        |
| RBLX   | Roblox         |
| COIN   | Coinbase       |
| JPM    | JP Morgan      |
| SPOT   | Spotify        |
| WMT    | Walmart        |


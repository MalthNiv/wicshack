import yfinance as yf
from textblob import TextBlob

    
def main():
    all_tickers = ['TTD', 'BMBL', 'COF', 'DKNG', 'CVX', 'RBLX', 'COIN', 'JPM', 'SPOT', 'M']
    all_scales = []
    for i in range(len(all_tickers)):
        all_scales.append(generate_song_key(all_tickers[i]))
    print(all_scales)
    


def generate_song_key(ticker): 
    # getting the data from yahoo finance
    stock = yf.Ticker(ticker)
    news = []
    total_polarity = 0
    for i in range(len(stock.news)):
        news.append(stock.news[i]['content'])
    # doing sentiment analysis
    if not news:
        print("No news!")
        return
    for article in news:
        analysis = TextBlob(article['title'])
        total_polarity += analysis.sentiment.polarity
    total_polarity /= len(news)
    ch = get_tone(stock)
    if(total_polarity < 0.04):
        return ch + " Minor"
    else:
        return ch + " Major"

def get_tone(stock): 
    change = stock.history(period="2d")['Close'].pct_change().iloc[-1]
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return notes[int(abs(change * 100)) % 12]

if __name__ == "__main__":
    main()
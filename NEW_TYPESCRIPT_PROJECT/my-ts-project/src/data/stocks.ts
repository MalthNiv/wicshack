export type Stock = {
  symbol: string;
  name: string;
  audio: string;
};

export const stocks: Stock[] = [
  { symbol: "TTD", name: "The Trade Desk", audio: "/audio/aapl.mp3" },
  { symbol: "BMBL", name: "Bumble", audio: "/audio/tsla.mp3" },
  { symbol: "COF", name: "Capital One", audio: "/audio/nvda.mp3" },
  { symbol: "DKNG", name: "Draft Kings", audio: "/audio/amzn.mp3" },
  { symbol: "CVX", name: "Chevron", audio: "/audio/googl.mp3" },
  { symbol: "RBLX", name: "Roblox", audio: "/audio/meta.mp3" },
  { symbol: "COIN", name: "Coinbase", audio: "/audio/msft.mp3" },
  { symbol: "JPM", name: "JP Morgan", audio: "/audio/nflx.mp3" },
  { symbol: "SPOT", name: "Spotify", audio: "/audio/amd.mp3" },
  { symbol: "WMT", name: "Walmart", audio: "/audio/intc.mp3" },
];

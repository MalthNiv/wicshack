export type Stock = {
  symbol: string;
  name: string;
  audio: string;
};

export const stocks: Stock[] = [
  { symbol: "TTD", name: "The Trade Desk", audio: "/audio/WAV/TTD.wav" },
  { symbol: "BMBL", name: "Bumble", audio: "/audio/WAV/BMBL.wav" },
  { symbol: "COF", name: "CapitalOne", audio: "/audio/WAV/COF.wav" },
  { symbol: "DKNG", name: "DraftKings", audio: "/audio/WAV/DKNG.wav" },
  { symbol: "CVX", name: "Chevron", audio: "/audio/WAV/CVX.wav" },
  { symbol: "RBLX", name: "Roblox", audio: "/audio/WAV/RBLX.wav" },
  { symbol: "COIN", name: "Coinbase", audio: "/audio/WAV/COIN.wav" },
  { symbol: "JPM", name: "JP Morgan", audio: "/audio/WAV/JPM.wav" },
  { symbol: "SPOT", name: "Spotify", audio: "/audio/WAV/SPOT.wav" },
  { symbol: "WMT", name: "Walmart", audio: "/audio/WAV/WMT.wav" },
];

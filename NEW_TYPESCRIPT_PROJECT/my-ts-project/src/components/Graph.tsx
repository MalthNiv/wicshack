import React, { useEffect, useRef } from 'react';
import { StockAnimator } from '../pages/StockAnimator'; // Ensure this path is correct
import stockData from '/Users/sophiali/wicshack/NEW_TYPESCRIPT_PROJECT/my-ts-project/stocks_daily_prices.json';

type Props = {
  symbol: string;
};

export default function Graph({ symbol }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const animatorRef = useRef<StockAnimator | null>(null);

  useEffect(() => {
    // Initialize your animator when the component loads
    if (canvasRef.current && !animatorRef.current) {
      animatorRef.current = new StockAnimator(canvasRef.current);
    }

    // Cleanup: Stop audio/animation if the user leaves the page
    return () => {
      animatorRef.current?.stop();
    };
  }, []);

  const handleStart = () => {
    // Find the specific stock data using the symbol passed from StockPage.tsx
    const prices = (stockData.daily_prices as any)[symbol];

    if (prices && audioRef.current) {
      audioRef.current.play();
      animatorRef.current?.start(prices, audioRef.current);
    } else {
      console.warn(`No price data found for ${symbol} or audio missing.`);
    }
  };

  return (
    <div className="graph" style={{ textAlign: 'center' }}>
      <p>{symbol} price movement</p>
      
      {/* Replaced her <svg> with your <canvas>. 
        The style matches her original dimensions. 
      */}
      <canvas 
        ref={canvasRef} 
        style={{ width: '100%', maxWidth: '800px', height: 'auto', background: '#161a1e', borderRadius: '8px' }} 
      />

      <audio ref={audioRef} src="/music/track.mp3" />

      <div style={{ marginTop: '20px' }}>
        <button 
          onClick={handleStart}
          style={{
            padding: '10px 25px',
            background: 'transparent',
            color: '#fff',
            border: '2px solid #00ffcc',
            borderRadius: '30px',
            cursor: 'pointer',
            fontSize: '14px',
            letterSpacing: '1px'
          }}
        >
          PLAY & SYNC
        </button>
      </div>
    </div>
  );
}


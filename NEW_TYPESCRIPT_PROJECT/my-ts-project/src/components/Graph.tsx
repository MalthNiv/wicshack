import React, { useEffect, useRef } from 'react';
import { StockAnimator } from '../pages/StockAnimator';
import { stocks } from '../data/stocks';
import stockData from '../data/stocks_prices.json';

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

  const handleStart = async () => {
    const stock = stocks.find(s => s.symbol === symbol);
    if (!stock) {
      console.warn(`No stock config found for ${symbol}`);
      return;
    }

    const prices = (stockData.daily_prices as any)[stock.name];
    const audio = audioRef.current;

    if (!prices || !audio) {
      console.warn('Missing prices or audio element for', stock.name);
      return;
    }

    // Set the audio source dynamically
    audio.src = stock.audio;
    audio.currentTime = 0;

    try {
      await audio.play();
    } catch (err) {
      console.error('Audio play failed:', err);
      return;
    }

    animatorRef.current?.start(prices, audio);
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

      <audio
        ref={audioRef}
        crossOrigin="anonymous"
      />


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


import { useNavigate } from "react-router-dom";
import { stocks } from "../data/stocks";

// ... imports ...

export default function RecordPlayer() {
  const navigate = useNavigate();

  return (
    <div className="turntable">
      <div className="sound-wave-ring" />
      <div className="sound-wave-ring ring-2" />
      <div className="sound-wave-ring ring-3" />
      <div className="record spinning">
        {stocks.map((stock, index) => {
          // Calculate the angle for each spoke
          const angle = (360 / stocks.length) * index;

          return (
            <div
              key={stock.symbol}
              className="record-label-wrapper"
              style={{
                transform: `translateY(-50%) rotate(${angle}deg)`,
              }}
            >
              <button
                className="record-label"
                onClick={() => navigate(`/stock/${stock.symbol}`)}
              >
                {stock.symbol}
              </button>
            </div>
          );
        })}

        <div className="center-hole">
          <span className="center-text">choose <br /> your<br /> stock </span>
        </div>
      </div>
    </div>
  );
}

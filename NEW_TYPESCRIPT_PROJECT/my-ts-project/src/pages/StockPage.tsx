import { useParams, useNavigate } from "react-router-dom";
import Graph from "../components/Graph";
import AudioPlayer from "../components/AudioPlayer";

export default function StockPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();

  if (!symbol) return null;

  return (
    <div className="stock-page">
      <button className="back" onClick={() => navigate("/")}>
        ← back to record
      </button>

      <h2>{symbol}</h2>

      <AudioPlayer symbol={symbol} />
      <Graph symbol={symbol} />
    </div>
  );
}

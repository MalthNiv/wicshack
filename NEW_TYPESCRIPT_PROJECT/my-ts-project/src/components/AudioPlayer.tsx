import { stocks } from "../data/stocks";

type Props = {
  symbol: string;
};

export default function AudioPlayer({ symbol }: Props) {
  const stock = stocks.find((s) => s.symbol === symbol);

  if (!stock) return null;

  return (
    <div className="audio-player">
      <audio controls autoPlay src={stock.audio} />
    </div>
  );
}

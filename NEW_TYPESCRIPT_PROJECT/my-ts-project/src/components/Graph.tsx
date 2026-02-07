type Props = {
  symbol: string;
};

export default function Graph({ symbol }: Props) {
  return (
    <div className="graph">
      <p>{symbol} price movement</p>
      <svg width="400" height="200">
        <polyline
          fill="none"
          stroke="black"
          strokeWidth="2"
          points="0,120 50,100 100,140 150,80 200,90 250,60 300,100 350,40"
        />
      </svg>
    </div>
  );
}

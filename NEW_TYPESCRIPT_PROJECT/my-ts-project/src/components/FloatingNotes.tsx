const notes = ["♪", "♫", "♩", "♬"];
const colors = ["#5BB8F5", "#266298", "#7B2D8E", "#C4447A"];

export default function FloatingNotes() {
  const particles = Array.from({ length: 20 }, (_, i) => {
    const note = notes[i % notes.length];
    const color = colors[i % colors.length];
    // Keep notes away from the center where the record is
    const left = Math.random() < 0.5
      ? Math.random() * 25        // left 25%
      : 75 + Math.random() * 25;  // right 25%
    const delay = Math.random() * 12;
    const duration = 8 + Math.random() * 8;
    const size = 24 + Math.random() * 24;

    return (
      <span
        key={i}
        className="floating-note"
        style={{
          left: `${left}%`,
          animationDelay: `${delay}s`,
          animationDuration: `${duration}s`,
          fontSize: `${size}px`,
          color: color,
          textShadow: `0 0 8px ${color}, 0 0 20px ${color}`,
        }}
      >
        {note}
      </span>
    );
  });

  return <div className="floating-notes-container">{particles}</div>;
}

import { CARD_BACK, CARD_EFFECTS, cardImage, cardLabel } from "./cards";

interface CardProps {
  value: number | null | undefined;
  size?: "sm" | "md" | "lg";
  showInfo?: boolean;
}

const SIZES: Record<NonNullable<CardProps["size"]>, number> = {
  sm: 60,
  md: 100,
  lg: 160,
};

export function Card({ value, size = "md", showInfo = false }: CardProps) {
  const width = SIZES[size];
  const src = value == null ? CARD_BACK : cardImage(value);
  const label = value == null ? "Hidden" : cardLabel(value);

  return (
    <div style={{ position: "relative", display: "inline-block", width }}>
      <img
        src={src}
        alt={label}
        title={label}
        width={width}
        style={{ borderRadius: width * 0.06, boxShadow: "0 2px 8px rgba(0,0,0,0.4)", display: "block" }}
      />
      {showInfo && value != null && (
        <span
          title={CARD_EFFECTS[value]}
          style={{
            position: "absolute",
            top: 4,
            right: 4,
            width: 18,
            height: 18,
            borderRadius: "50%",
            background: "rgba(0,0,0,0.65)",
            color: "#fff",
            fontSize: 12,
            lineHeight: "18px",
            textAlign: "center",
            cursor: "help",
            fontFamily: "serif",
          }}
        >
          i
        </span>
      )}
    </div>
  );
}

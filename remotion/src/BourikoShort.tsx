import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  staticFile,
  useCurrentFrame,
  Video,
  interpolate,
} from "remotion";

type Line = {
  text: string;
  media_asset?: string;
  media_kind?: string;
  media_asset_2?: string;
  media_kind_2?: string;
  start: number;
  duration: number;
  visual?: string;
};

type Sfx = {
  time: number;
  file: string;
  volume?: number;
};

export type BourikoProps = {
  lines: Line[];
  durationSeconds: number;
  sfxEvents?: Sfx[];
};

const Caption = ({ text, visual, duration }: { text: string; visual?: string; duration: number }) => {
  const frame = useCurrentFrame();
  const words = text.trim().split(/\\s+/);
  const elapsed = frame / 30;
  const wordIndex = Math.min(
    words.length - 1,
    Math.floor((elapsed / Math.max(0.5, duration)) * words.length),
  );
  const chunkSize = words.length > 11 ? 4 : 3;
  const chunkIndex = Math.floor(wordIndex / chunkSize);
  const chunk = words.slice(chunkIndex * chunkSize, chunkIndex * chunkSize + chunkSize);
  const label = (visual || "TECH").toUpperCase();

  const palettes = ["#FFFFFF", "#FFD23F", "#2EA8FF", "#FF6B6B", "#7FF0C5", "#FF9F43"];
  const positions = [
    { top: 185, left: 55, right: 55 },
    { top: 390, left: 80, right: 80 },
    { top: 610, left: 55, right: 55 },
    { top: 820, left: 90, right: 90 },
    { bottom: 520, left: 55, right: 55 },
    { bottom: 360, left: 80, right: 80 },
    { bottom: 230, left: 55, right: 55 },
    { top: 1040, left: 70, right: 70 },
  ];
  const sizes = [88, 102, 116, 96, 108, 92];
  const styleSeed = text.length * 17 + chunkIndex * 31;
  const paletteIndex = Math.abs(styleSeed) % palettes.length;
  const positionIndex = Math.abs(styleSeed * 7) % positions.length;
  const size = sizes[Math.abs(styleSeed * 11) % sizes.length];
  const position = positions[positionIndex];
  const captionColor = palettes[paletteIndex];
  const activeColor = palettes[(paletteIndex + 2) % palettes.length];

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: 150,
          left: 56,
          padding: "9px 16px",
          borderRadius: 999,
          background: "rgba(20,20,20,.78)",
          color: "#fff",
          fontFamily: "Arial Black, Arial, sans-serif",
          fontSize: 24,
          fontWeight: 900,
          letterSpacing: 1.2,
        }}
      >
        {label}
      </div>

      <div
        style={{
          position: "absolute",
          ...position,
          display: "flex",
          justifyContent: "center",
          width: "calc(100% - 110px)",
        }}
      >
        <div
          style={{
            maxWidth: 1020,
            textAlign: "center",
            fontFamily: "Arial Black, Arial, sans-serif",
            fontWeight: 900,
            fontSize: size,
            lineHeight: 0.94,
            letterSpacing: -2.2,
            WebkitTextStroke: "3px rgba(0,0,0,.9)",
            textShadow: "0 6px 18px rgba(0,0,0,.85)",
            transform: `rotate(${((chunkIndex % 3) - 1) * 0.7}deg)`,
          }}
        >
          {chunk.map((word, i) => (
            <span
              key={i}
              style={{
                display: "inline-block",
                marginRight: 14,
                color: i === wordIndex % chunkSize ? activeColor : captionColor,
                transform: i === wordIndex % chunkSize ? "scale(1.08)" : "scale(1)",
              }}
            >
              {word}
            </span>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

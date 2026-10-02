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
  const words = text.trim().split(/\s+/);
  const elapsed = frame / 30;
  const wordIndex = Math.min(
    words.length - 1,
    Math.floor((elapsed / Math.max(0.5, duration)) * words.length),
  );
  const chunkSize = words.length > 11 ? 5 : 4;
  const chunkIndex = Math.floor(wordIndex / chunkSize);
  const chunk = words.slice(chunkIndex * chunkSize, chunkIndex * chunkSize + chunkSize);
  const label = (visual || "TECH").toUpperCase();

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
          left: 48,
          right: 48,
          bottom: 210,
          display: "flex",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            maxWidth: 980,
            textAlign: "center",
            fontFamily: "Arial Black, Arial, sans-serif",
            fontWeight: 900,
            fontSize: 72,
            lineHeight: 0.98,
            letterSpacing: -1.8,
            textTransform: "none",
            WebkitTextStroke: "2px rgba(0,0,0,.85)",
            textShadow: "0 5px 14px rgba(0,0,0,.75)",
          }}
        >
          {chunk.map((word, i) => (
            <span
              key={i}
              style={{
                display: "inline-block",
                marginRight: 16,
                color: i === wordIndex % chunkSize ? "#FFD23F" : "#FFFFFF",
                transform: i === wordIndex % chunkSize ? "translateY(-2px)" : "none",
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

const Scene = ({ line }: { line: Line }) => {
  const asset = line.media_asset?.replace(/^output\//, "");
  const kind = (line.media_kind || "").toLowerCase();

  let visual: React.ReactNode;

  if (asset && kind === "video") {
    visual = (
      <Video
        src={staticFile(asset)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
        muted
      />
    );
  } else if (asset) {
    visual = (
      <Img
        src={staticFile(asset)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
    );
  } else {
    visual = (
      <AbsoluteFill
        style={{
          background: "#111",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            color: "white",
            fontFamily: "Arial, sans-serif",
            fontWeight: 800,
            fontSize: 52,
            textAlign: "center",
            padding: 70,
          }}
        >
          {line.visual || "EXPLAINER"}
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill>
      {visual}
      <Caption text={line.text} visual={line.visual} duration={line.duration} />
    </AbsoluteFill>
  );
};

export const BourikoShort = ({
  lines,
  sfxEvents = [],
}: BourikoProps) => (
  <AbsoluteFill style={{ backgroundColor: "black" }}>
    {lines.map((line, index) => (
      <Sequence
        key={index}
        from={Math.round(line.start * 30)}
        durationInFrames={Math.max(1, Math.ceil(line.duration * 30))}
      >
        <Scene line={line} />
      </Sequence>
    ))}

    <Audio src={staticFile("generated/narration.wav")} />

    {sfxEvents.map((event, index) => (
      <Sequence key={`sfx-${index}`} from={Math.round(event.time * 30)}>
        <Audio
          src={staticFile(event.file.replace(/^output\//, ""))}
          volume={event.volume ?? 0.12}
        />
      </Sequence>
    ))}
  </AbsoluteFill>
);

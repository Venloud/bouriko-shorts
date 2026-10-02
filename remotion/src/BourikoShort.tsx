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

const Caption = ({ text }: { text: string }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [0, 5, 8],
    [0, 0.75, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    },
  );

  return (
    <div
      style={{
        position: "absolute",
        left: 54,
        right: 54,
        top: "42%",
        transform: "translateY(-50%)",
        display: "flex",
        justifyContent: "center",
        opacity,
      }}
    >
      <div
        style={{
          maxWidth: 940,
          padding: "18px 30px",
          borderRadius: 22,
          background: "rgba(0,0,0,.62)",
          color: "white",
          fontFamily: "Arial, sans-serif",
          fontWeight: 800,
          fontSize: 60,
          lineHeight: 1.08,
          textAlign: "center",
          textShadow: "0 3px 10px rgba(0,0,0,.9)",
        }}
      >
        {text}
      </div>
    </div>
  );
};

const Scene = ({ line }: { line: Line }) => {
  const asset = line.media_asset?.replace(/^output\\//, "");
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
      <Caption text={line.text} />
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
          src={staticFile(event.file.replace(/^output\\//, ""))}
          volume={event.volume ?? 0.12}
        />
      </Sequence>
    ))}
  </AbsoluteFill>
);

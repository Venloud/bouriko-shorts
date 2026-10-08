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
  spring,
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

const FONT_STYLES = [
  { family: '"Arial Black", "DejaVu Sans", sans-serif', weight: 900, spacing: -2.4 },
  { family: '"Impact", "Arial Black", "DejaVu Sans", sans-serif', weight: 900, spacing: -2.8 },
  { family: '"Trebuchet MS", "DejaVu Sans", sans-serif', weight: 900, spacing: -2.0 },
  { family: '"Courier New", "DejaVu Sans Mono", monospace', weight: 900, spacing: -1.4 },
  { family: '"Georgia", "DejaVu Serif", serif', weight: 900, spacing: -2.0 },
];

const STRONG_WORDS = new Set([
  "secret", "actually", "wait", "why", "how", "never", "always", "hidden",
  "free", "fast", "slow", "crazy", "million", "billion", "true", "real",
  "hack", "warning", "important", "boom", "but", "because", "really",
]);

const CaptionBurst = ({
  active,
  color,
  intensity,
}: {
  active: boolean;
  color: string;
  intensity: number;
}) => {
  const frame = useCurrentFrame();
  if (!active) return null;

  const burst = spring({
    frame,
    fps: 30,
    config: { damping: 10, stiffness: 230, mass: 0.55 },
  });
  const fade = interpolate(frame, [0, 5, 15, 25], [0, 1, 0.7, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = interpolate(burst, [0, 1], [0.35, 1.25 + intensity * 0.35]);
  const rotation = interpolate(frame, [0, 25], [-5, 8]);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        pointerEvents: "none",
        opacity: fade,
        transform: `scale(${scale}) rotate(${rotation}deg)`,
      }}
    >
      {Array.from({ length: 10 }).map((_, i) => {
        const angle = i * 36;
        const length = 95 + intensity * 35;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              width: length,
              height: 7,
              borderRadius: 99,
              background: color,
              boxShadow: `0 0 12px ${color}`,
              transform: `rotate(${angle}deg) translateX(150px)`,
              transformOrigin: "left center",
            }}
          />
        );
      })}
      <div
        style={{
          width: 24 + intensity * 12,
          height: 24 + intensity * 12,
          borderRadius: "50%",
          border: `7px solid ${color}`,
          boxShadow: `0 0 24px ${color}`,
        }}
      />
    </div>
  );
};

const Caption = ({
  text,
  visual,
  duration,
}: {
  text: string;
  visual?: string;
  duration: number;
}) => {
  const frame = useCurrentFrame();
  const words = text.trim().split(/\s+/).filter(Boolean);
  const elapsed = frame / 30;
  const safeDuration = Math.max(0.5, duration);
  const wordIndex = Math.min(
    Math.max(0, words.length - 1),
    Math.floor((elapsed / safeDuration) * words.length),
  );
  const chunkSize = words.length > 11 ? 4 : 3;
  const chunkIndex = Math.floor(wordIndex / chunkSize);
  const chunk = words.slice(chunkIndex * chunkSize, chunkIndex * chunkSize + chunkSize);
  const activeIndex = wordIndex % chunkSize;
  const activeWord = (words[wordIndex] || "").replace(/[^a-z0-9]/gi, "").toLowerCase();
  const strong = STRONG_WORDS.has(activeWord);
  const label = (visual || "TECH").toUpperCase();

  const palettes = ["#FFFFFF", "#FFD23F", "#2EA8FF", "#FF6B6B", "#7FF0C5", "#FF9F43"];
  const positions = [{ bottom: 230, left: 55, right: 55 }];
  const sizes = [68, 72, 76];
  const styleSeed = text.length * 17 + chunkIndex * 31;
  const paletteIndex = Math.abs(styleSeed) % palettes.length;
  const positionIndex = Math.abs(styleSeed * 7) % positions.length;
  const size = sizes[Math.abs(styleSeed * 11) % sizes.length];
  const position = positions[positionIndex];
  const captionColor = palettes[paletteIndex];
  const activeColor = palettes[(paletteIndex + 2) % palettes.length];
  const font = FONT_STYLES[Math.abs(styleSeed * 13) % FONT_STYLES.length];

  const chunkStart = (chunkIndex * chunkSize / Math.max(1, words.length)) * safeDuration;
  const chunkElapsed = Math.max(0, elapsed - chunkStart);
  const wordWindow = safeDuration / Math.max(1, words.length);
  const activeWordElapsed = chunkElapsed - activeIndex * wordWindow;
  const activeFrame = Math.max(0, Math.round(activeWordElapsed * 30));
  const pop = spring({
    frame: activeFrame,
    fps: 30,
    config: {
      damping: strong ? 8 : 12,
      stiffness: strong ? 300 : 220,
      mass: 0.5,
    },
  });
  const punch = interpolate(pop, [0, 1], [0.72, strong ? 1.2 : 1.08]);
  const shake = strong
    ? Math.sin(activeFrame * 1.7) * Math.max(0, 1 - activeFrame / 14) * 5
    : 0;
  const burstActive = activeFrame < (strong ? 18 : 11);

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
          fontFamily: '"Arial Black", "DejaVu Sans", sans-serif',
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
            position: "relative",
            maxWidth: 1020,
            textAlign: "center",
            fontFamily: font.family,
            fontWeight: font.weight,
            fontSize: size,
            lineHeight: 0.94,
            letterSpacing: font.spacing,
            WebkitTextStroke: "3px rgba(0,0,0,.9)",
            textShadow: "0 6px 18px rgba(0,0,0,.85)",
            transform: `rotate(${((chunkIndex % 3) - 1) * 0.7}deg)`,
          }}
        >
          <CaptionBurst
            active={burstActive}
            color={activeColor}
            intensity={strong ? 1 : 0}
          />

          {chunk.map((word, i) => {
            const isActive = i === activeIndex;
            const isStrong = isActive && STRONG_WORDS.has(
              word.replace(/[^a-z0-9]/gi, "").toLowerCase(),
            );
            return (
              <span
                key={`${chunkIndex}-${i}`}
                style={{
                  display: "inline-block",
                  marginRight: 14,
                  color: isActive ? activeColor : captionColor,
                  transform: isActive
                    ? `translateY(${-6 * pop}px) translateX(${shake}px) scale(${punch}) rotate(${isStrong ? shake * 0.7 : 0}deg)`
                    : "scale(1)",
                  transition: "none",
                  filter: isActive && isStrong ? `drop-shadow(0 0 12px ${activeColor})` : "none",
                }}
              >
                {word}
              </span>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Scene = ({ line }: { line: Line }) => {
  const primaryAsset = line.media_asset?.replace(/^output\//, "");
  const primaryKind = (line.media_kind || "").toLowerCase();
  const secondaryAsset = line.media_asset_2?.replace(/^output\//, "");
  const secondaryKind = (line.media_kind_2 || "").toLowerCase();
  const frame = useCurrentFrame();
  const splitFrame = Math.floor(Math.max(1, line.duration * 30) / 2);
  const progress = Math.min(1, frame / Math.max(1, line.duration * 30));
  const cameraScale = 1.04 + progress * 0.11;
  const cameraX = Math.sin(progress * Math.PI) * 22;
  const cameraY = (progress - 0.5) * 32;
  const cameraTransform = `scale(${cameraScale}) translate(${cameraX}px, ${cameraY}px)`;
  const useSecondary = Boolean(secondaryAsset && frame >= splitFrame);
  const asset = useSecondary ? secondaryAsset : primaryAsset;
  const kind = useSecondary ? secondaryKind : primaryKind;

  let visual: React.ReactNode;

  if (asset && kind === "video") {
    visual = (
      <Video
        src={staticFile(asset)}
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: cameraTransform }}
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
            fontFamily: '"Arial Black", "DejaVu Sans", sans-serif',
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

const BourikoShort = ({
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

export { BourikoShort };
export default BourikoShort;

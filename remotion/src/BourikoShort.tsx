import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  staticFile,
  useCurrentFrame,
  Video,
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

const Caption = ({
  text,
  duration,
}: {
  text: string;
  visual?: string;
  duration: number;
}) => {
  const frame = useCurrentFrame();
  const words = text.trim().split(/\s+/).filter(Boolean);
  const elapsed = frame / 30;
  const wordIndex = Math.min(Math.max(0, words.length - 1),
    Math.floor((elapsed / Math.max(duration, 0.2)) * words.length));
  const chunkSize = 3;
  const chunkIndex = Math.floor(wordIndex / chunkSize);
  const chunk = words.slice(chunkIndex * chunkSize, chunkIndex * chunkSize + chunkSize);
  const activeWord = wordIndex % chunkSize;
  const chunkStart = (chunkIndex * chunkSize / Math.max(1,words.length)) * Math.max(duration,0.2);
  const entryFrame = Math.max(0,Math.floor((elapsed-chunkStart)*30));
  const settle = spring({frame:entryFrame,fps:30,config:{damping:22,stiffness:150,mass:0.7}});
  return (
    <AbsoluteFill style={{pointerEvents:"none"}}>
      <div style={{
        position:"absolute",bottom:380,left:100,right:100,
        display:"flex",justifyContent:"center",alignItems:"center",
        gap:12,flexWrap:"wrap",textAlign:"center",
        fontFamily:'"DejaVu Sans", Arial, sans-serif',
        fontWeight:800,fontSize:58,lineHeight:1.2,
        textShadow:"0 3px 12px rgba(0,0,0,.95), 0 2px 3px #000",
        transform:`translateY(${(1-settle)*16}px)`,opacity:Math.min(1,entryFrame/5)
      }}>
        {chunk.map((word,i)=>(
          <span key={i} style={{color:i===activeWord?"#FFE18A":"#FFFFFF"}}>
            {word}
          </span>
        ))}
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
  const useSecondary = Boolean(secondaryAsset && frame >= splitFrame);
  const asset = useSecondary ? secondaryAsset : primaryAsset;
  const kind = useSecondary ? secondaryKind : primaryKind;

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

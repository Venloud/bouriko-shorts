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
  anime_visual_type?: string;
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
  visualType?: string;
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
  const positions = [{ bottom: 255, left: 65, right: 65 }];
  const sizes = [48, 52, 56];
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
          top: 170,
          left: 56,
          padding: "9px 16px",
          borderRadius: 999,
          background: "rgba(20,20,20,.78)",
          color: "#fff",
          fontFamily: '"Arial Black", "DejaVu Sans", sans-serif',
          fontSize: 21,
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

const NeonGraphic = ({ line }: { line: Line }) => {
  const frame = useCurrentFrame();
  const kind = line.anime_visual_type || "hero_motion";
  const pulse = 0.5 + 0.5 * Math.sin(frame / 11);
  const advance = interpolate(frame, [0, 38], [0, 1], { extrapolateRight: "clamp" });
  const isMap = kind === "animated_map";
  const isCounter = kind === "animated_counter";
  const isTimer = kind === "animated_timer";
  const isEnergy = kind === "energy_diagram";
  const number = parseInt(line.visual || "", 10) || 100;
  const main = isCounter ? String(Math.round(number * advance)) : isTimer ? String(Math.round(19 * advance)) : "";
  return (
    <AbsoluteFill style={{
      overflow: "hidden",
      background: "radial-gradient(ellipse at 28% 32%, #064fbf 0%, #092a7e 34%, #10145b 65%, #470b68 100%)",
      color: "#f5fbff", fontFamily: '"Arial Black", sans-serif',
    }}>
      <AbsoluteFill style={{
        opacity: .25, transform: `translateY(${frame % 80}px)`,
        backgroundImage: "linear-gradient(#1de6ff55 2px, transparent 2px), linear-gradient(90deg, #1de6ff55 2px, transparent 2px)",
        backgroundSize: "80px 80px",
      }}/>
      <div style={{ position: "absolute", top: 240, left: 76, fontSize: 28, letterSpacing: 8, color: "#5ceaff" }}>CULLING GAME // SYSTEM</div>
      <div style={{ position: "absolute", top: 305, left: 76, right: 76, height: 3, background: "#fa376d", boxShadow: "0 0 28px #ff1c60" }}/>
      {isMap ? (
        <svg viewBox="0 0 900 900" style={{position:"absolute",top:330,left:70,width:940,height:940,filter:"drop-shadow(0 0 18px #00dfff)"}}>
          <path d="M590 55 L645 98 L630 160 L688 196 L659 242 L616 251 L627 304 L584 356 L545 370 L541 423 L489 459 L452 512 L395 545 L365 613 L301 638 L259 706 L197 736 L144 793 L96 780 L132 721 L190 676 L229 624 L287 602 L330 551 L375 520 L419 464 L457 422 L487 365 L513 313 L539 252 L550 197 L571 145 Z" fill="#123fbd" stroke="#5bf2ff" strokeWidth="9" strokeLinejoin="round"/>
          {[[600,160],[575,245],[545,335],[485,415],[410,510],[345,575],[280,635],[220,695],[160,750],[500,460]].map(([x,y],i)=>(
            <g key={i}><circle cx={x} cy={y} r={17+pulse*13} fill="#f42162" fillOpacity=".35" stroke="#ff547e" strokeWidth="4"/><circle cx={x} cy={y} r="6" fill="#fff"/></g>
          ))}
          <text x="80" y="95" fill="#ffffff" fontSize="45" fontWeight="900">JAPAN</text>
          <text x="80" y="145" fill="#67edff" fontSize="26">10 ACTIVE COLONIES</text>
        </svg>
      ) : isCounter || isTimer ? (
        <div style={{position:"absolute",top:480,left:70,right:70,textAlign:"center"}}>
          <div style={{fontSize:250,lineHeight:1,color:"#fff",textShadow:"0 0 50px #00dcff, 0 0 90px #fc205d"}}>{main}</div>
          <div style={{fontSize:50,letterSpacing:12,color:"#64efff"}}>{isTimer?"DAYS REMAINING":"POINTS"}</div>
          <div style={{height:18,background:"#103d8c",marginTop:75,borderRadius:20}}>
            <div style={{height:"100%",width:`${Math.max(3,advance*100)}%`,background:"linear-gradient(90deg,#00dfff,#ff306a)",boxShadow:"0 0 30px #00dfff",borderRadius:20}}/>
          </div>
        </div>
      ) : (
        <div style={{position:"absolute",top:470,left:75,right:75,height:750,display:"flex",alignItems:"center",justifyContent:"center"}}>
          <div style={{position:"absolute",width:550,height:550,border:"8px solid #2fe9ff",borderRadius:"50%",boxShadow:"0 0 90px #04dfff, inset 0 0 85px #f02278",transform:`rotate(${frame*0.7}deg) scale(${0.95+pulse*0.06})`}}/>
          <div style={{position:"absolute",width:430,height:430,border:"7px dashed #ff376f",borderRadius:"50%",transform:`rotate(${-frame*1.3}deg)`}}/>
          <div style={{zIndex:2,fontSize:kind==="anime_reference"?80:65,textAlign:"center",maxWidth:800,lineHeight:1.12,textShadow:"0 0 32px #00dcff, 0 0 45px #ff236b"}}>{line.visual}</div>
          {isEnergy && <div style={{position:"absolute",bottom:5,fontSize:28,letterSpacing:7,color:"#75e9ff"}}>CURSED ENERGY → RITUAL</div>}
        </div>
      )}
      <div style={{position:"absolute",top:1370,left:80,right:80,height:3,background:"#42e5ff",boxShadow:"0 0 20px #32e4ff"}}/>
      <div style={{position:"absolute",top:1400,left:80,color:"#8befff",fontSize:24,letterSpacing:4}}>JUJUTSU KAISEN // EXPLAINED</div>
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
    visual = <NeonGraphic line={line} />;

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

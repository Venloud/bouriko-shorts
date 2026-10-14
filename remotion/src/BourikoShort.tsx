import React from 'react';
import {AbsoluteFill, Audio, Freeze, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Annotation, Annotations} from './Annotations';
import {CaptionChunk, Captions} from './Captions';
import {Diagram} from './Diagrams';
import {BOX, FONT, ORB, PURPLE, Theme, clamp01, easeOut, themeOf} from './theme';

// Narrator-led, evidence-first Short. Every beat (2-4 s, built by pipeline/remotion_prepare.py)
// is one visual: a framed image/clip, or a diagram that builds step by step, or (orb beats)
// nothing at all, when the voice ring takes the centre. Hard cuts between beats.

type Box = {x: number; y: number; w: number; h: number};

export type Beat = {
  start: number;
  end: number;
  key: string;
  kind: 'media' | 'diagram' | 'orb';
  media?: {
    src: string;
    kind: 'video' | 'image';
    startFrom?: number;
    fit?: 'cover' | 'contain';
    focus?: [number, number];
    backdrop?: string;
    credit?: string;
    frame?: 'red' | 'white';
  };
  diagram?: {name: string; params?: Record<string, any>; steps?: number[]};
  annotations?: Annotation[];
  box?: Box;
  tag?: string;
};

type Sfx = {time: number; file: string; volume?: number};
type Effect = {type: 'punch' | 'shake' | 'freeze'; time: number; dur?: number};
type Reaction = {time: number; dur: number; text: string};

export type BourikoProps = {
  durationSeconds: number;
  theme?: string;
  beats: Beat[];
  captions: CaptionChunk[];
  sfxEvents?: Sfx[];
  narration?: string;
  music?: string;
  musicVolume?: number;
  brand?: string;
  voiceEnv?: number[]; // narration loudness per frame, 0-1 (pipeline/remotion_prepare.py)
  effects?: Effect[];
  reactions?: Reaction[];
};

const FontLoader: React.FC = () => (
  <style>{`
    @font-face { font-family: 'Montserrat'; font-weight: 700; src: url('${staticFile('fonts/montserrat-latin-700-normal.woff2')}') format('woff2'); }
    @font-face { font-family: 'Montserrat'; font-weight: 800; src: url('${staticFile('fonts/montserrat-latin-800-normal.woff2')}') format('woff2'); }
    @font-face { font-family: 'Montserrat'; font-weight: 900; src: url('${staticFile('fonts/montserrat-latin-900-normal.woff2')}') format('woff2'); }
  `}</style>
);

// JJK: the approved blue -> purple gradient with a slowly moving cyan grid (kept from the
// experiment look). Tech: dark gradient, or the blurred media backdrop.
const Background: React.FC<{theme: Theme; backdrop?: string}> = ({theme, backdrop}) => {
  const frame = useCurrentFrame();
  if (theme.name === 'jjk') {
    return (
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 28% 32%, #064fbf 0%, #092a7e 34%, #10145b 65%, #470b68 100%)'}}>
        <AbsoluteFill style={{
          opacity: 0.25,
          backgroundImage: 'linear-gradient(#1de6ff55 2px, transparent 2px), linear-gradient(90deg, #1de6ff55 2px, transparent 2px)',
          backgroundSize: '80px 80px',
          backgroundPosition: `0 ${frame % 80}px`,
        }} />
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 30%, ${theme.bg2} 0%, ${theme.bg} 70%)`}}>
      {backdrop ? (
        <Img src={staticFile(backdrop)} style={{position: 'absolute', inset: -80, width: 1240, height: 2080, objectFit: 'cover', filter: 'blur(46px) brightness(0.32) saturate(1.2)'}} />
      ) : (
        <AbsoluteFill style={{
          backgroundImage: `linear-gradient(${theme.grid} 2px, transparent 2px), linear-gradient(90deg, ${theme.grid} 2px, transparent 2px)`,
          backgroundSize: '60px 60px',
          backgroundPosition: `0 ${(frame * 0.6) % 60}px`,
        }} />
      )}
    </AbsoluteFill>
  );
};

const BeatView: React.FC<{beat: Beat; theme: Theme}> = ({beat, theme}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const box = beat.box || BOX;
  if (beat.kind === 'orb') return null;
  const pop = Math.min(1, frame / 5);
  const scale = 0.97 + 0.03 * pop;
  const isMedia = beat.kind === 'media';

  return (
    <AbsoluteFill>
      <div style={{
        position: 'absolute', left: box.x, top: box.y, width: box.w, height: box.h,
        transform: `scale(${scale})`,
        borderRadius: isMedia ? 30 : 0,
        overflow: isMedia ? 'hidden' : 'visible',
        boxShadow: !isMedia ? 'none'
          : beat.media?.frame === 'red'
            ? '0 30px 80px rgba(0,0,0,.6), 0 0 0 6px #FF3B6B, 0 0 46px rgba(255,59,107,.55)'
            : '0 30px 80px rgba(0,0,0,.6), 0 0 0 5px rgba(255,255,255,.92)',
        background: isMedia ? '#000' : 'transparent',
      }}>
        {isMedia && beat.media && (
          beat.media.kind === 'video' ? (
            <OffthreadVideo src={staticFile(beat.media.src)} muted
              style={{width: '100%', height: '100%', objectFit: beat.media.fit || 'cover',
                objectPosition: `${(beat.media.focus?.[0] ?? 0.5) * 100}% ${(beat.media.focus?.[1] ?? 0.5) * 100}%`}} />
          ) : (
            <Img src={staticFile(beat.media.src)}
              style={{width: '100%', height: '100%', objectFit: beat.media.fit || 'cover',
                objectPosition: `${(beat.media.focus?.[0] ?? 0.5) * 100}% ${(beat.media.focus?.[1] ?? 0.5) * 100}%`}} />
          )
        )}
        {beat.kind === 'diagram' && beat.diagram && (
          <Diagram name={beat.diagram.name} params={beat.diagram.params} steps={beat.diagram.steps || [0]}
            t={t} dur={beat.end - beat.start} theme={theme} w={box.w} h={box.h} />
        )}
        {beat.annotations && beat.annotations.length > 0 && (
          <Annotations items={beat.annotations} t={t} w={box.w} h={box.h} theme={theme} />
        )}
        {beat.media?.credit && (
          <div style={{position: 'absolute', left: 16, bottom: 14, maxWidth: Math.min(260, box.w / 2 - 70), padding: '4px 10px', borderRadius: 8,
            background: 'rgba(0,0,0,.6)', color: 'rgba(255,255,255,.85)', fontFamily: FONT, fontWeight: 700, fontSize: 16, lineHeight: 1.25}}>
            {beat.media.credit}
          </div>
        )}
      </div>
      {beat.tag && (
        <div style={{position: 'absolute', left: box.x, top: box.y - 34 > 160 ? box.y - 34 : 164, fontFamily: FONT, fontWeight: 800,
          fontSize: 22, letterSpacing: 4, color: theme.accent}}>
          {beat.tag.toUpperCase()}
        </div>
      )}
    </AbsoluteFill>
  );
};

// The voice-monitor ring: big and centred when nothing is on screen (orb beats), small on the
// seam under the evidence box when media/graphics are showing. Swells with the voice.
const VoiceMonitor: React.FC<{env: number[]; beats: Beat[]}> = ({env, beats}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const idx = beats.findIndex((b) => t >= b.start && t < b.end);
  const cur = idx >= 0 ? beats[idx] : beats[beats.length - 1];
  const prev = idx > 0 ? beats[idx - 1] : undefined;
  const centre = (b?: Beat) => (b?.kind === 'orb' ? 1 : 0);
  const k = easeOut(clamp01((t - (cur?.start ?? 0)) / 0.3));
  const m = centre(prev) + (centre(cur) - centre(prev)) * k; // 1 = centre, 0 = out of the way
  const v = Math.max(env[frame] ?? 0, (env[Math.max(0, frame - 1)] ?? 0) * 0.85);
  const x = ORB.x;
  const y = ORB.y + (960 - ORB.y) * m;
  const base = 60 + (190 - 60) * m;
  const r = base * (0.9 + 0.22 * v);
  const spin = frame * 1.3;
  return (
    <div style={{position: 'absolute', left: x - r * 1.6, top: y - r * 1.6, width: r * 3.2, height: r * 3.2,
      display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none'}}>
      <div style={{position: 'absolute', width: r * 2, height: r * 2, borderRadius: '50%',
        border: `${Math.max(4, r * 0.05)}px solid #2fe9ff`,
        background: `radial-gradient(circle, rgba(139,92,246,${0.25 + 0.35 * v}) 0%, rgba(76,29,149,.15) 60%, transparent 72%)`,
        boxShadow: `0 0 ${20 + 60 * v}px #04dfff, inset 0 0 ${30 + 50 * v}px ${PURPLE}`}} />
      <div style={{position: 'absolute', width: r * 1.6, height: r * 1.6, borderRadius: '50%',
        border: `${Math.max(3, r * 0.035)}px dashed #ff376f`, transform: `rotate(${-spin}deg)`}} />
      <div style={{position: 'absolute', width: r * 0.55 * (1 + 0.5 * v), height: r * 0.55 * (1 + 0.5 * v), borderRadius: '50%',
        background: `radial-gradient(circle at 35% 30%, #E9DDFF 0%, #B794FF 35%, ${PURPLE} 70%)`,
        boxShadow: `0 0 ${16 + 40 * v}px ${PURPLE}`}} />
    </div>
  );
};

// Punch-in zoom / screen shake applied to the visual layer at the cue word.
const effectTransform = (effects: Effect[], t: number) => {
  let scale = 1, dx = 0, dy = 0;
  for (const e of effects) {
    const d = t - e.time;
    if (e.type === 'punch' && d >= 0 && d < 0.6) {
      const up = clamp01(d / 0.08), down = clamp01((d - 0.08) / 0.5);
      scale *= 1 + 0.09 * up * (1 - easeOut(down));
    }
    if (e.type === 'shake' && d >= 0 && d < 0.4) {
      const a = 14 * (1 - d / 0.4);
      dx += Math.sin(d * 95) * a;
      dy += Math.cos(d * 77) * a * 0.6;
    }
  }
  return `translate(${dx}px, ${dy}px) scale(${scale})`;
};

// Meme-style reaction sticker on the jokes (max 5 per video, enforced in qa.py).
const ReactionSticker: React.FC<{r: Reaction}> = ({r}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const s = easeOut(clamp01(t / 0.15));
  const out = clamp01((t - (r.dur - 0.2)) / 0.2);
  const size = Math.min(92, 820 / (Math.max(6, r.text.length) * 0.62));
  return (
    <div style={{position: 'absolute', left: 120, width: 840, top: 560, display: 'flex', justifyContent: 'center', pointerEvents: 'none'}}>
      <div style={{transform: `rotate(-4deg) scale(${(0.5 + 0.5 * s) * (1 - 0.1 * out)})`, opacity: 1 - out,
        background: '#FFE14D', color: '#0B0B0B', fontFamily: FONT, fontWeight: 900, fontSize: size, lineHeight: 1.05,
        padding: '18px 28px', borderRadius: 14, border: '6px solid #0B0B0B', boxShadow: '10px 10px 0 #0B0B0B',
        textAlign: 'center', maxWidth: 820, textTransform: 'uppercase'}}>
        {r.text}
      </div>
    </div>
  );
};

export const BourikoShort: React.FC<BourikoProps> = ({beats = [], captions = [], sfxEvents = [], theme: themeName,
  narration, music, musicVolume, voiceEnv, effects = [], reactions = []}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const theme = themeOf(themeName);
  const freeze = effects.find((e) => e.type === 'freeze' && t >= e.time && t < e.time + (e.dur ?? 0.8));
  const flash = freeze ? clamp01(1 - (t - freeze.time) / 0.12) : 0;
  const cur = beats.find((b) => t >= b.start && t < b.end);
  return (
    <AbsoluteFill style={{backgroundColor: theme.bg}}>
      <FontLoader />
      <Background theme={theme} backdrop={cur?.media?.backdrop} />
      <AbsoluteFill style={{transform: effectTransform(effects, t), transformOrigin: '540px 725px'}}>
        <Freeze frame={freeze ? Math.round(freeze.time * fps) : frame} active={Boolean(freeze)}>
          {beats.map((beat, i) => {
            const from = Math.round(beat.start * fps);
            const to = Math.round(beat.end * fps);
            return (
              <Sequence key={i} from={from} durationInFrames={Math.max(1, to - from)}>
                <BeatView beat={beat} theme={theme} />
              </Sequence>
            );
          })}
        </Freeze>
        {freeze && <AbsoluteFill style={{background: 'rgba(255,255,255,1)', opacity: flash * 0.6, mixBlendMode: 'screen'}} />}
        {freeze && <AbsoluteFill style={{backdropFilter: 'saturate(0.35)', WebkitBackdropFilter: 'saturate(0.35)'}} />}
      </AbsoluteFill>
      {voiceEnv && voiceEnv.length > 0 && <VoiceMonitor env={voiceEnv} beats={beats} />}
      {reactions.map((r, i) => (
        <Sequence key={`re-${i}`} from={Math.round(r.time * fps)} durationInFrames={Math.max(1, Math.round(r.dur * fps))}>
          <ReactionSticker r={r} />
        </Sequence>
      ))}
      <Captions chunks={captions} theme={theme} />
      <Audio src={staticFile(narration || 'generated/narration.wav')} />
      {music && <Audio src={staticFile(music)} volume={musicVolume ?? 1} />}
      {sfxEvents.map((e, i) => (
        <Sequence key={`sfx-${i}`} from={Math.round(e.time * fps)}>
          <Audio src={staticFile(e.file)} volume={e.volume ?? 1} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

export default BourikoShort;

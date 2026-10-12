import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Annotation, Annotations} from './Annotations';
import {CaptionChunk, Captions} from './Captions';
import {Diagram} from './Diagrams';
import {BOX, FONT, Theme, themeOf} from './theme';

// Narrator-led, evidence-first Short. Every beat (2-4 s, built by pipeline/remotion_prepare.py)
// is one visual: real footage/photo in a framed box, or a diagram that builds step by step.
// Hard cuts between beats; motion comes from the footage and the drawing itself (no Ken Burns).

type Box = {x: number; y: number; w: number; h: number};

export type Beat = {
  start: number;
  end: number;
  key: string;
  kind: 'media' | 'diagram';
  media?: {
    src: string;
    kind: 'video' | 'image';
    startFrom?: number;
    fit?: 'cover' | 'contain';
    focus?: [number, number];
    backdrop?: string;
    credit?: string;
  };
  diagram?: {name: string; params?: Record<string, any>; steps?: number[]};
  annotations?: Annotation[];
  box?: Box;
  tag?: string;
};

type Sfx = {time: number; file: string; volume?: number};

export type BourikoProps = {
  durationSeconds: number;
  theme?: string;
  beats: Beat[];
  captions: CaptionChunk[];
  sfxEvents?: Sfx[];
  narration?: string;
  brand?: string;
};

const FontLoader: React.FC = () => (
  <style>{`
    @font-face { font-family: 'Montserrat'; font-weight: 700; src: url('${staticFile('fonts/montserrat-latin-700-normal.woff2')}') format('woff2'); }
    @font-face { font-family: 'Montserrat'; font-weight: 800; src: url('${staticFile('fonts/montserrat-latin-800-normal.woff2')}') format('woff2'); }
    @font-face { font-family: 'Montserrat'; font-weight: 900; src: url('${staticFile('fonts/montserrat-latin-900-normal.woff2')}') format('woff2'); }
  `}</style>
);

const Background: React.FC<{theme: Theme; backdrop?: string}> = ({theme, backdrop}) => {
  const frame = useCurrentFrame();
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
  const pop = Math.min(1, frame / 5);
  const scale = 0.97 + 0.03 * pop;

  return (
    <AbsoluteFill>
      <Background theme={theme} backdrop={beat.media?.backdrop} />
      <div style={{
        position: 'absolute', left: box.x, top: box.y, width: box.w, height: box.h,
        transform: `scale(${scale})`,
        borderRadius: beat.kind === 'media' ? 30 : 0,
        overflow: beat.kind === 'media' ? 'hidden' : 'visible',
        boxShadow: beat.kind === 'media' ? '0 30px 80px rgba(0,0,0,.6), 0 0 0 5px rgba(255,255,255,.92)' : 'none',
        background: beat.kind === 'media' ? '#000' : 'transparent',
      }}>
        {beat.kind === 'media' && beat.media && (
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
          <div style={{position: 'absolute', left: 18, bottom: 14, padding: '4px 12px', borderRadius: 8,
            background: 'rgba(0,0,0,.55)', color: 'rgba(255,255,255,.8)', fontFamily: FONT, fontWeight: 700, fontSize: 18}}>
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

export const BourikoShort: React.FC<BourikoProps> = ({beats = [], captions = [], sfxEvents = [], theme: themeName, narration}) => {
  const {fps} = useVideoConfig();
  const theme = themeOf(themeName);
  return (
    <AbsoluteFill style={{backgroundColor: theme.bg}}>
      <FontLoader />
      {beats.map((beat, i) => {
        const from = Math.round(beat.start * fps);
        const to = Math.round(beat.end * fps);
        return (
          <Sequence key={i} from={from} durationInFrames={Math.max(1, to - from)}>
            <BeatView beat={beat} theme={theme} />
          </Sequence>
        );
      })}
      <Captions chunks={captions} theme={theme} />
      <Audio src={staticFile(narration || 'generated/narration.wav')} />
      {sfxEvents.map((e, i) => (
        <Sequence key={`sfx-${i}`} from={Math.round(e.time * fps)}>
          <Audio src={staticFile(e.file)} volume={e.volume ?? 1} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

export default BourikoShort;

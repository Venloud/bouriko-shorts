import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {CAPTION_LANE, FONT, SAFE, Theme} from './theme';

export type CaptionWord = {text: string; start: number; end: number};
export type CaptionChunk = {start: number; end: number; words: CaptionWord[]};

// 3-5 words per chunk (built in pipeline/remotion_prepare.py from real word timings),
// the word being spoken is highlighted. Always centred inside the caption lane, which sits
// inside the TikTok safe box (x 120-960) and below the evidence box.
export const Captions: React.FC<{chunks: CaptionChunk[]; theme: Theme}> = ({chunks, theme}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const chunk = chunks.find((c) => t >= c.start && t < c.end);
  if (!chunk) return null;

  const chars = chunk.words.reduce((n, w) => n + w.text.length + 1, 0);
  const size = Math.round(Math.max(60, Math.min(88, 96 - Math.max(0, chars - 12) * 1.7)));
  const enter = Math.min(1, (t - chunk.start) * fps / 4);
  let active = -1;
  chunk.words.forEach((w, i) => {
    if (t >= w.start - 0.02) active = i;
  });

  return (
    <div
      style={{
        position: 'absolute',
        left: SAFE.x0,
        width: SAFE.x1 - SAFE.x0,
        top: CAPTION_LANE.top,
        height: CAPTION_LANE.bottom - CAPTION_LANE.top,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          textAlign: 'center',
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: size,
          lineHeight: 1.08,
          letterSpacing: -1,
          textTransform: 'uppercase',
          transform: `scale(${0.92 + 0.08 * enter})`,
          opacity: 0.4 + 0.6 * enter,
        }}
      >
        {chunk.words.map((w, i) => {
          const isActive = i === active;
          return (
            <span
              key={i}
              style={{
                display: 'inline-block',
                margin: '0 10px',
                color: isActive ? theme.accent : '#FFFFFF',
                WebkitTextStroke: '10px #05070A',
                paintOrder: 'stroke fill',
                textShadow: '0 6px 18px rgba(0,0,0,.7)',
                transform: isActive ? 'scale(1.08) translateY(-4px)' : 'none',
              }}
            >
              {w.text}
            </span>
          );
        })}
      </div>
    </div>
  );
};

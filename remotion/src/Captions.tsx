import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {CAPTION_LANE, FONT, SAFE, Theme} from './theme';

export type CaptionWord = {text: string; start: number; end: number};
export type CaptionChunk = {start: number; end: number; words: CaptionWord[]; whole_sentence?: boolean};

// Plain, clean captions: white text, 3-5 words (built in pipeline/remotion_prepare.py from real
// word timings), the word being spoken gets a soft highlight. No bouncing, no colour cycling,
// no bursts. Centred in the caption lane, inside the TikTok safe box, below the evidence box.
export const Captions: React.FC<{chunks: CaptionChunk[]; theme: Theme}> = ({chunks}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const chunk = chunks.find((c) => t >= c.start && t < c.end);
  if (!chunk) return null;

  const chars = chunk.words.reduce((n, w) => n + w.text.length + 1, 0);
  const size = Math.round(Math.max(50, Math.min(68, 76 - Math.max(0, chars - 12) * 1.4)));
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
      <div style={{textAlign: 'center', fontFamily: FONT, fontWeight: 800, fontSize: size, lineHeight: 1.18, color: '#FFFFFF'}}>
        {chunk.words.map((w, i) => (
          <React.Fragment key={i}>
            <span
              style={{
                padding: '0 8px',
                borderRadius: 10,
                background: i === active ? 'rgba(255,255,255,0.22)' : 'transparent',
                WebkitTextStroke: '6px rgba(5,7,10,0.9)',
                paintOrder: 'stroke fill',
                textShadow: '0 4px 14px rgba(0,0,0,.6)',
                boxDecorationBreak: 'clone',
                WebkitBoxDecorationBreak: 'clone',
              }}
            >
              {w.text}
            </span>
            {i < chunk.words.length - 1 ? ' ' : null}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

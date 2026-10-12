import React from 'react';
import {FONT, Theme, progress} from './theme';

// Draw-on callouts in the brand blue, placed in the evidence box's own 0-1 coordinates
// (authored per shot in data/visual_plans/*.json, so they point at the real thing in the frame).
export type Annotation = {
  type: 'circle' | 'arrow' | 'label' | 'box' | 'underline';
  at: number; // seconds from beat start
  x?: number;
  y?: number;
  r?: number; // circle radius (fraction of box width)
  rx?: number;
  ry?: number;
  w?: number;
  h?: number;
  from?: [number, number];
  to?: [number, number];
  text?: string;
  color?: string;
};

const DRAW = 0.4; // seconds for a stroke to draw on

export const Annotations: React.FC<{
  items: Annotation[];
  t: number;
  w: number;
  h: number;
  theme: Theme;
}> = ({items, t, w, h, theme}) => (
  <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
    {items.map((a, i) => {
      if (t < a.at) return null;
      const p = progress(t, a.at, DRAW);
      const color = a.color || theme.accent;
      if (a.type === 'circle') {
        const rx = (a.rx ?? a.r ?? 0.12) * w;
        const ry = (a.ry ?? a.r ?? 0.12) * w;
        const len = Math.PI * (rx + ry) * 1.1;
        const common = {cx: (a.x ?? 0.5) * w, cy: (a.y ?? 0.5) * h, rx, ry, fill: 'none', strokeDasharray: len, strokeDashoffset: len * (1 - p), strokeLinecap: 'round' as const, transform: `rotate(-90 ${(a.x ?? 0.5) * w} ${(a.y ?? 0.5) * h})`};
        return (
          <g key={i}>
            <ellipse {...common} stroke="rgba(0,0,0,.65)" strokeWidth={18} />
            <ellipse {...common} stroke={color} strokeWidth={10} />
          </g>
        );
      }
      if (a.type === 'box' || a.type === 'underline') {
        const x = (a.x ?? 0.3) * w, y = (a.y ?? 0.3) * h, bw = (a.w ?? 0.4) * w, bh = a.type === 'underline' ? 0 : (a.h ?? 0.2) * h;
        const len = a.type === 'underline' ? bw : 2 * (bw + bh);
        const d = a.type === 'underline' ? `M${x},${y} L${x + bw},${y}` : `M${x},${y} h${bw} v${bh} h${-bw} Z`;
        return (
          <g key={i}>
            <path d={d} fill="none" stroke="rgba(0,0,0,.65)" strokeWidth={18} strokeDasharray={len} strokeDashoffset={len * (1 - p)} strokeLinejoin="round" strokeLinecap="round" />
            <path d={d} fill="none" stroke={color} strokeWidth={10} strokeDasharray={len} strokeDashoffset={len * (1 - p)} strokeLinejoin="round" strokeLinecap="round" />
          </g>
        );
      }
      if (a.type === 'arrow') {
        const [fx, fy] = a.from || [0.2, 0.2];
        const [tx, ty] = a.to || [0.5, 0.5];
        const x1 = fx * w, y1 = fy * h, x2 = tx * w, y2 = ty * h;
        const len = Math.hypot(x2 - x1, y2 - y1);
        const ang = Math.atan2(y2 - y1, x2 - x1);
        const head = 40;
        const hx = x1 + (x2 - x1) * p, hy = y1 + (y2 - y1) * p;
        const left = `${hx - head * Math.cos(ang - 0.5)},${hy - head * Math.sin(ang - 0.5)}`;
        const right = `${hx - head * Math.cos(ang + 0.5)},${hy - head * Math.sin(ang + 0.5)}`;
        return (
          <g key={i}>
            <line x1={x1} y1={y1} x2={hx} y2={hy} stroke="rgba(0,0,0,.65)" strokeWidth={18} strokeLinecap="round" />
            <line x1={x1} y1={y1} x2={hx} y2={hy} stroke={color} strokeWidth={10} strokeLinecap="round" />
            {p > 0.05 && <polygon points={`${hx},${hy} ${left} ${right}`} fill={color} stroke="rgba(0,0,0,.65)" strokeWidth={4} />}
            {len < 1 && null}
          </g>
        );
      }
      // label pill
      const s = progress(t, a.at, 0.18);
      const fontSize = 36;
      const tw = (a.text || '').length * fontSize * 0.68 + 44;
      const lx = Math.min(w - tw - 12, Math.max(12, (a.x ?? 0.5) * w - tw / 2));
      const ly = Math.min(h - 70, Math.max(12, (a.y ?? 0.1) * h - 30));
      return (
        <g key={i} transform={`translate(${lx + tw / 2} ${ly + 30}) scale(${0.6 + 0.4 * s}) translate(${-tw / 2} -30)`} opacity={s}>
          <rect width={tw} height={60} rx={30} fill={color} stroke="rgba(0,0,0,.6)" strokeWidth={4} />
          <text x={tw / 2} y={42} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fontSize} fill="#06121F">
            {(a.text || '').toUpperCase()}
          </text>
        </g>
      );
    })}
  </svg>
);

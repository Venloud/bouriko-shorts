import React from 'react';
import {FONT, Theme, clamp01, easeOut, progress} from './theme';

// Diagrams that BUILD step by step. Each step time (seconds from the beat start) comes from the
// visual plan's word cues, so a part appears when the narrator says it.
export type DiagramProps = {
  name: string;
  t: number; // seconds since beat start
  dur: number;
  steps: number[];
  params?: Record<string, any>;
  theme: Theme;
  w: number;
  h: number;
};

type Ctx = DiagramProps & {p: (i: number, d?: number) => number; on: (i: number) => boolean};

const fit_ = (text: string, width: number, max: number) => Math.min(max, width / (Math.max(1, text.length) * 0.68));
const stroke = (len: number, p: number) => ({strokeDasharray: len, strokeDashoffset: len * (1 - clamp01(p))});

const Txt: React.FC<{x: number; y: number; size?: number; color?: string; children: React.ReactNode; anchor?: 'start' | 'middle' | 'end'; o?: number; weight?: number; spacing?: number}> = ({x, y, size = 40, color = '#fff', children, anchor = 'middle', o = 1, weight = 900, spacing = 0}) => (
  <text x={x} y={y} fontFamily={FONT} fontWeight={weight} fontSize={size} fill={color} textAnchor={anchor} opacity={o} letterSpacing={spacing} style={{paintOrder: 'stroke'}} stroke="rgba(0,0,0,.55)" strokeWidth={size > 50 ? 8 : 5}>
    {children}
  </text>
);

const Pill: React.FC<{x: number; y: number; text: string; color: string; s: number; size?: number}> = ({x, y, text, color, s, size = 34}) => {
  const tw = text.length * size * 0.68 + 40;
  if (s <= 0) return null;
  return (
    <g transform={`translate(${x} ${y}) scale(${0.6 + 0.4 * s})`} opacity={s}>
      <rect x={-tw / 2} y={-30} width={tw} height={60} rx={30} fill={color} stroke="rgba(0,0,0,.55)" strokeWidth={4} />
      <text x={0} y={12} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={size} fill="#06121F">{text.toUpperCase()}</text>
    </g>
  );
};

const Card: React.FC<{x: number; y: number; w: number; h: number; s: number; theme: Theme; border?: string; children?: React.ReactNode}> = ({x, y, w, h, s, theme, border, children}) => {
  if (s <= 0) return null;
  return (
    <g transform={`translate(${x + w / 2} ${y + h / 2}) scale(${0.85 + 0.15 * s}) translate(${-w / 2} ${-h / 2})`} opacity={s}>
      <rect width={w} height={h} rx={28} fill={theme.panel} stroke={border || theme.accent} strokeWidth={5} />
      {children}
    </g>
  );
};

// ---------- tech: traffic light ----------
const TrafficLight: React.FC<{x: number; y: number; s?: number; lit: 'red' | 'yellow' | 'green' | 'none'; theme: Theme; draw?: number}> = ({x, y, s = 1, lit, theme, draw = 1}) => {
  const colors = {red: theme.danger, yellow: theme.warn, green: theme.ok};
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      <rect x={-70} y={-200} width={140} height={400} rx={36} fill="#1B232C" stroke="#E8EEF3" strokeWidth={6} {...stroke(1100, draw)} />
      <rect x={-10} y={200} width={20} height={160} fill="#3A4652" opacity={draw} />
      {(['red', 'yellow', 'green'] as const).map((c, i) => (
        <circle key={c} cx={0} cy={-120 + i * 120} r={46} fill={lit === c ? colors[c] : '#2A333D'} opacity={draw}
          style={lit === c ? {filter: `drop-shadow(0 0 22px ${colors[c]})`} : undefined} />
      ))}
    </g>
  );
};

const CarTop: React.FC<{x: number; y: number; color?: string}> = ({x, y, color = '#E9EEF2'}) => (
  <g transform={`translate(${x} ${y})`}>
    <rect x={-75} y={-130} width={150} height={260} rx={40} fill={color} stroke="#0B0F14" strokeWidth={6} />
    <rect x={-58} y={-80} width={116} height={60} rx={14} fill="#5E7A90" />
    <rect x={-58} y={40} width={116} height={45} rx={12} fill="#5E7A90" />
  </g>
);

const HookQuestion: React.FC<Ctx> = ({w, h, p, theme, t}) => {
  const pulse = 0.5 + 0.5 * Math.sin(t * 6);
  return (
    <g>
      <TrafficLight x={w * 0.34} y={h * 0.42} lit="red" theme={theme} draw={p(0, 0.5)} />
      <g opacity={p(1)} transform={`translate(${(1 - p(1)) * 120} 0)`}>
        <g transform={`translate(${w * 0.66} ${h * 0.7}) rotate(-90)`}><CarTop x={0} y={0} /></g>
      </g>
      <g opacity={p(2, 0.2)} transform={`translate(${w * 0.7} ${h * 0.34}) scale(${0.5 + 0.5 * easeOut(p(2, 0.25)) + pulse * 0.04})`}>
        <circle r={110} fill={theme.accent} />
        <Txt x={0} y={58} size={170} color="#06121F">?</Txt>
      </g>
    </g>
  );
};

const LoopField: React.FC<Ctx> = ({w, h, p, on, theme, t, steps}) => {
  const lx = w * 0.27, ly = h * 0.44, lw = w * 0.46, lh = h * 0.24;
  const per = 2 * (lw + lh);
  const carIn = p(4, 0.9);
  const carY = h * 1.25 - (h * 1.25 - (ly + lh / 2)) * carIn;
  const disturbed = on(4) && carIn > 0.7;
  const ringColor = disturbed ? theme.warn : theme.accent;
  return (
    <g>
      <g opacity={p(0)}>
        <rect x={0} y={0} width={w} height={h} fill="#2B3138" />
        {[0.1, 0.9].map((xx) => <line key={xx} x1={w * xx} y1={0} x2={w * xx} y2={h} stroke="#E9C46A" strokeWidth={8} />)}
      </g>
      <line x1={w * 0.1} y1={h * 0.3} x2={w * 0.9} y2={h * 0.3} stroke="#F4F7FA" strokeWidth={22} {...stroke(w, p(0, 0.5))} />
      {on(0) && <Txt x={w * 0.5} y={h * 0.25} size={30} color="#F4F7FA" o={p(0)}>STOP LINE</Txt>}
      {/* saw-cut loop */}
      <rect x={lx} y={ly} width={lw} height={lh} rx={8} fill="none" stroke="#11161B" strokeWidth={22} {...stroke(per, p(1, 0.6))} />
      <rect x={lx} y={ly} width={lw} height={lh} rx={8} fill="none" stroke={theme.accent} strokeWidth={9} {...stroke(per, p(1, 0.6))} />
      <Pill x={w * 0.5} y={ly - 50} text="wire loop" color={theme.accent} s={p(1, 0.25)} />
      {/* current running around the wire */}
      {on(2) && Array.from({length: 10}).map((_, i) => {
        const d = ((t * 380 + i * per / 10) % per);
        let x = lx, y = ly;
        if (d < lw) { x = lx + d; y = ly; }
        else if (d < lw + lh) { x = lx + lw; y = ly + d - lw; }
        else if (d < 2 * lw + lh) { x = lx + lw - (d - lw - lh); y = ly + lh; }
        else { x = lx; y = ly + lh - (d - 2 * lw - lh); }
        return <circle key={i} cx={x} cy={y} r={9} fill={theme.warn} opacity={p(2)} />;
      })}
      {/* magnetic field */}
      {on(3) && [1, 2, 3].map((k) => {
        const phase = ((t - steps[3]) * 0.9 + k / 3) % 1;
        const grow = 30 + phase * 90;
        const squash = disturbed ? 0.45 : 1;
        return <rect key={k} x={lx - grow} y={ly - grow * squash} width={lw + 2 * grow} height={lh + 2 * grow * squash} rx={30 + grow / 2}
          fill="none" stroke={ringColor} strokeWidth={5} opacity={(1 - phase) * 0.8 * p(3)} />;
      })}
      {on(3) && !disturbed && <Pill x={w * 0.5} y={h * 0.86} text="magnetic field" color={theme.accent} s={p(3, 0.25)} />}
      {on(4) && <g transform={`translate(${w * 0.5} ${carY})`}><CarTop x={0} y={0} /></g>}
      {disturbed && <Pill x={w * 0.5} y={h * 0.86} text="field changes" color={theme.warn} s={clamp01((carIn - 0.7) / 0.3)} />}
    </g>
  );
};

const DetectionFlow: React.FC<Ctx> = ({w, h, p, on, theme, t, params}) => {
  const labels: string[] = params?.labels || ['CAR', 'LOOP', 'CONTROLLER', 'LIGHT'];
  const ys = labels.map((_, i) => h * (0.12 + i * 0.255));
  const final = on(labels.length);
  return (
    <g>
      {labels.map((label, i) => {
        const s = p(i, 0.35);
        const y = ys[i];
        return (
          <g key={label}>
            {i > 0 && (
              <g>
                <line x1={w / 2} y1={ys[i - 1] + 70} x2={w / 2} y2={y - 70} stroke={theme.accent} strokeWidth={10} strokeLinecap="round" {...stroke(h * 0.12, s)} />
                {s > 0.95 && <polygon points={`${w / 2},${y - 62} ${w / 2 - 22},${y - 96} ${w / 2 + 22},${y - 96}`} fill={theme.accent} />}
                {s > 0.2 && s < 1 && null}
                {on(i) && (() => {
                  const k = ((t * 1.4) % 1);
                  return <circle cx={w / 2} cy={ys[i - 1] + 70 + (y - 70 - ys[i - 1] - 70) * k} r={10} fill={theme.warn} opacity={0.9} />;
                })()}
              </g>
            )}
            <Card x={w * 0.17} y={y - 70} w={w * 0.66} h={140} s={s} theme={theme} border={i === labels.length - 1 && final ? theme.ok : theme.accent}>
              <Txt x={w * 0.33} y={88} size={54} color={i === labels.length - 1 && final ? theme.ok : '#fff'}>{label}</Txt>
            </Card>
          </g>
        );
      })}
      {final && <Pill x={w / 2} y={h * 0.97} text={params?.done || 'green light'} color={theme.ok} s={p(labels.length, 0.25)} />}
    </g>
  );
};

const Icon: React.FC<{kind: string; color: string; t: number}> = ({kind, color, t}) => {
  if (kind === 'loop') return <rect x={-70} y={-42} width={140} height={84} rx={8} fill="none" stroke={color} strokeWidth={10} />;
  if (kind === 'camera') return (
    <g><rect x={-70} y={-40} width={110} height={80} rx={14} fill={color} /><polygon points="40,-20 75,-38 75,38 40,20" fill={color} /></g>
  );
  if (kind === 'radar') return (
    <g>{[30, 60, 90].map((r, i) => <path key={r} d={`M${-r * 0.7},${-r * 0.7} A${r},${r} 0 0 1 ${r * 0.7},${-r * 0.7}`} transform="translate(0 40)" fill="none" stroke={color} strokeWidth={9} opacity={0.4 + 0.6 * ((Math.sin(t * 5 - i) + 1) / 2)} />)}<circle cx={0} cy={40} r={12} fill={color} /></g>
  );
  // timer
  return (
    <g><circle r={56} fill="none" stroke={color} strokeWidth={9} /><line x1={0} y1={0} x2={0} y2={-38} stroke={color} strokeWidth={9} strokeLinecap="round" transform={`rotate(${t * 120})`} /><line x1={0} y1={0} x2={26} y2={0} stroke={color} strokeWidth={9} strokeLinecap="round" /></g>
  );
};

const Methods: React.FC<Ctx> = ({w, h, p, theme, t, params}) => {
  const items: {k: string; label: string}[] = params?.items || [
    {k: 'loop', label: 'ROAD LOOP'}, {k: 'camera', label: 'CAMERA'}, {k: 'radar', label: 'RADAR'}, {k: 'timer', label: 'TIMER'},
  ];
  const cw = w * 0.44, ch = h * 0.4;
  return (
    <g>
      {items.map((it, i) => {
        const x = i % 2 === 0 ? w * 0.04 : w * 0.52;
        const y = i < 2 ? h * 0.06 : h * 0.52;
        const hl = params?.highlight?.includes?.(i);
        return (
          <Card key={it.k} x={x} y={y} w={cw} h={ch} s={p(i, 0.3)} theme={theme} border={hl ? theme.warn : theme.accent}>
            <g transform={`translate(${cw / 2} ${ch * 0.42})`}><Icon kind={it.k} color={hl ? theme.warn : theme.accent} t={t} /></g>
            <Txt x={cw / 2} y={ch * 0.85} size={40}>{it.label}</Txt>
          </Card>
        );
      })}
    </g>
  );
};

// ---------- generic ----------
const Keyword: React.FC<Ctx> = ({w, h, p, theme, params}) => {
  const lines: string[] = params?.lines || [params?.text || ''];
  const size = params?.size || 96;
  const gap = size * 1.25;
  const top = h * 0.5 - ((lines.length - 1) * gap) / 2; // vertically centred in the box
  const under = top + (lines.length - 1) * gap + size * 0.55;
  return (
    <g>
      {lines.map((l, i) => (
        <g key={i} opacity={p(i, 0.2)} transform={`translate(0 ${(1 - p(i, 0.25)) * 40})`}>
          <Txt x={w / 2} y={top + i * gap} size={Math.min(size, (w * 0.92) / (Math.max(1, l.length) * 0.68))} color={i === (params?.accentLine ?? -1) ? theme.accent : '#fff'}>{l}</Txt>
        </g>
      ))}
      <line x1={w * 0.18} y1={under} x2={w * 0.82} y2={under} stroke={params?.color || theme.accent} strokeWidth={14} strokeLinecap="round" {...stroke(w * 0.64, p(lines.length, 0.4))} />
      {params?.sub && <Txt x={w / 2} y={under + 90} size={40} color={theme.muted} o={p(lines.length, 0.3)}>{params.sub}</Txt>}
    </g>
  );
};

const Counter: React.FC<Ctx> = ({w, h, p, theme, params, dur, steps}) => {
  const from = params?.from ?? 0, to = params?.to ?? 100;
  // finish counting at least 0.6 s before the beat ends, so the final value is on screen
  const room = Math.max(0.3, dur - (steps[1] ?? 0) - 0.6);
  const k = p(1, Math.min(params?.countDur ?? 1.2, room));
  const v = k > 0.995 ? to : Math.round(from + (to - from) * k);
  return (
    <g opacity={p(0, 0.2)}>
      <Txt x={w / 2} y={h * 0.5} size={260} color="#fff">{`${params?.prefix || ''}${v}`}</Txt>
      <Txt x={w / 2} y={h * 0.62} size={56} color={theme.accent} spacing={6}>{params?.label || ''}</Txt>
      <rect x={w * 0.12} y={h * 0.7} width={w * 0.76} height={22} rx={11} fill="#1C2733" />
      <rect x={w * 0.12} y={h * 0.7} width={w * 0.76 * Math.abs((v - from) / ((to - from) || 1))} height={22} rx={11} fill={params?.color || theme.accent} />
    </g>
  );
};

// ---------- JJK ----------
const lonlat = (lon: number, lat: number, w: number, h: number): [number, number] => {
  const k = Math.min(w / 15.2, h / 15.4);
  return [24 + (lon - 128.6) * k * 0.82, 40 + (45.8 - lat) * k];
};
const ISLANDS: number[][][] = [
  [[130.2,33.6],[131,33.9],[131.9,33.3],[131.7,32.3],[131.3,31.4],[130.7,31],[130.2,31.3],[130.1,32.1],[129.7,32.6],[129.8,33.2]],
  [[132,33.4],[132.8,33.9],[133.6,34.2],[134.6,34.2],[134.7,33.8],[134.2,33.2],[133.3,33.4],[132.9,32.8]],
  [[130.9,34],[131.4,34.4],[132.6,35.5],[133.6,35.6],[134.9,35.7],[135.8,35.6],[136.2,36.2],[136.8,37.2],[137.3,37.5],[137.5,36.9],[138.5,37.4],[139.3,38],[139.8,39],[140,40],[139.9,40.6],[140.4,41.2],[141.2,41.3],[141.5,40.5],[142,39.6],[141.6,38.4],[141,37.9],[141,37],[140.6,36.2],[140.9,35.7],[140.3,35.1],[139.8,35],[139.6,35.3],[139.1,35.1],[138.8,34.6],[138.2,34.6],[137.2,34.6],[136.9,34.3],[136.5,34],[135.8,33.5],[135.2,33.8],[135.1,34.3],[135.4,34.6],[134.7,34.7],[133.9,34.4],[133,34.3],[132.2,33.9],[131.7,34]],
  [[140,41.5],[140.5,41.8],[140.2,42.3],[140.4,43.2],[141.3,43.3],[141.6,44.4],[141.9,45.4],[142.9,44.7],[143.8,44.1],[144.8,43.9],[145.3,43.3],[144.3,42.9],[143.3,42],[142,42.5],[141,42.4],[140.9,41.8]],
];
// Illustrative positions along the line from Sendai to Sakurajima (Hokkaido excluded, as in canon).
const COLONIES: [number, number][] = [[140.9,38.3],[140.2,37.2],[139.75,35.75],[139.45,35.6],[138.3,35.4],[137,35.2],[135.9,35.2],[134.4,34.9],[132.5,34.4],[130.65,31.6]];

const JapanColonies: React.FC<Ctx> = ({w, h, p, on, theme, t, steps}) => {
  const paths = ISLANDS.map((pts) => 'M' + pts.map(([a, b]) => lonlat(a, b, w, h).join(',')).join(' L') + ' Z');
  const popStart = steps[1] ?? 0.6, popEnd = steps[2] ?? popStart + 1.5;
  const shown = on(1) ? Math.min(10, Math.floor(((t - popStart) / Math.max(0.2, popEnd - popStart)) * 10) + 1) : 0;
  const line = COLONIES.map(([a, b]) => lonlat(a, b, w, h));
  return (
    <g>
      {paths.map((d, i) => (
        <path key={i} d={d} fill={theme.panel} fillOpacity={p(0, 0.8)} stroke={theme.accent} strokeWidth={6} strokeLinejoin="round" {...stroke(3000, p(0, 0.8))} style={{filter: `drop-shadow(0 0 10px ${theme.accent})`}} />
      ))}
      {on(3) && <polyline points={line.map((q) => q.join(',')).join(' ')} fill="none" stroke={theme.accent2} strokeWidth={6} strokeDasharray="14 12" opacity={p(3)} />}
      {line.slice(0, shown).map(([x, y], i) => {
        const pulse = 0.5 + 0.5 * Math.sin(t * 5 + i);
        return (
          <g key={i}>
            <circle cx={x} cy={y} r={20 + pulse * 10} fill={theme.accent2} fillOpacity={0.3} stroke={theme.accent2} strokeWidth={4} />
            <circle cx={x} cy={y} r={8} fill="#fff" />
          </g>
        );
      })}
      <Txt x={w * 0.06} y={h * 0.08} size={52} anchor="start">JAPAN</Txt>
      <Txt x={w * 0.06} y={h * 0.14} size={38} anchor="start" color={theme.accent2} o={on(1) ? 1 : 0}>{`${shown}/10 COLONIES`}</Txt>
      {on(3) && <Txt x={w * 0.94} y={h * 0.97} size={24} anchor="end" color={theme.muted}>colony positions illustrative</Txt>}
    </g>
  );
};

const JjkTimer: React.FC<Ctx> = ({w, h, p, on, theme, params, steps, t}) => {
  const from = params?.from ?? 19;
  const k = on(1) ? clamp01((t - steps[1]) / Math.max(0.3, (steps[2] ?? steps[1] + 1.5) - steps[1])) : 0;
  const v = Math.round(from * (1 - k));
  const r = Math.min(w, h) * 0.3;
  const len = 2 * Math.PI * r;
  const red = on(2);
  const col = red ? theme.danger : theme.accent;
  return (
    <g>
      <g transform={`translate(${w / 2} ${h * 0.42})`}>
        <circle r={r} fill="none" stroke="#1C2140" strokeWidth={26} opacity={p(0)} />
        <circle r={r} fill="none" stroke={col} strokeWidth={26} strokeLinecap="round" transform="rotate(-90)"
          strokeDasharray={len} strokeDashoffset={len * (1 - p(0, 0.6) * (1 - k))} style={{filter: `drop-shadow(0 0 16px ${col})`}} />
        <Txt x={0} y={70} size={230} color="#fff" o={p(0)}>{v}</Txt>
      </g>
      <Txt x={w / 2} y={h * 0.84} size={50} color={col} spacing={4} o={p(0)}>{params?.label || 'DAYS LEFT'}</Txt>
      {red && <Pill x={w / 2} y={h * 0.95} text={params?.after || 'technique removed'} color={theme.danger} s={p(2, 0.25)} />}
    </g>
  );
};

const Points: React.FC<Ctx> = ({w, h, p, theme}) => (
  <g>
    <Card x={w * 0.08} y={h * 0.06} w={w * 0.84} h={h * 0.4} s={p(0, 0.3)} theme={theme} border={theme.accent}>
      <Txt x={w * 0.42} y={h * 0.15} size={50} color={theme.accent} spacing={4}>SORCERER</Txt>
      <Txt x={w * 0.42} y={h * 0.33} size={180}>+5</Txt>
    </Card>
    <Card x={w * 0.08} y={h * 0.53} w={w * 0.84} h={h * 0.4} s={p(1, 0.3)} theme={theme} border={theme.accent2}>
      <Txt x={w * 0.42} y={h * 0.15} size={50} color={theme.accent2} spacing={4}>NON-SORCERER</Txt>
      <Txt x={w * 0.42} y={h * 0.33} size={180}>+1</Txt>
    </Card>
  </g>
);

const Rule100: React.FC<Ctx> = ({w, h, p, on, theme, t, steps, params}) => {
  const k = on(0) ? clamp01((t - steps[0]) / 1.0) : 0;
  return (
    <g>
      <Txt x={w / 2} y={h * 0.17} size={150} color="#fff" o={p(0, 0.2)}>{`${Math.round(100 * easeOut(k))}`}</Txt>
      <Txt x={w / 2} y={h * 0.23} size={40} color={theme.accent} spacing={6} o={p(0, 0.2)}>POINTS SPENT</Txt>
      <Card x={w * 0.1} y={h * 0.3} w={w * 0.8} h={h * 0.34} s={p(1, 0.3)} theme={theme}>
        <Txt x={w * 0.4} y={h * 0.09} size={44} color={theme.accent} spacing={4}>NEW RULE</Txt>
        {(params?.rule || ['PLAYERS MAY TRANSFER', 'POINTS TO EACH OTHER']).map((l: string, i: number) => (
          <Txt key={i} x={w * 0.4} y={h * (0.165 + i * 0.05)} size={38} weight={800} o={p(1, 0.3 + i * 0.15)}>{l}</Txt>
        ))}
        {params?.ruleNote && <Txt x={w * 0.4} y={h * 0.275} size={24} color={theme.muted} weight={700} o={p(1, 0.6)}>{params.ruleNote}</Txt>}
      </Card>
      {on(2) && (
        <g transform={`translate(${w / 2} ${h * 0.8}) rotate(-4) scale(${1.4 - 0.4 * p(2, 0.2)})`} opacity={p(2, 0.15)}>
          <rect x={-w * 0.42} y={-70} width={w * 0.84} height={140} rx={16} fill="none" stroke={params?.stamp ? theme.danger : theme.warn} strokeWidth={8} />
          <Txt x={0} y={-12} size={36} color={params?.stamp ? theme.danger : theme.warn}>{(params?.stamp || ['ONLY IF IT HAS NO'])[0]}</Txt>
          <Txt x={0} y={40} size={36} color={params?.stamp ? theme.danger : theme.warn}>{(params?.stamp || ['', 'LONG-LASTING EFFECT'])[1]}</Txt>
        </g>
      )}
    </g>
  );
};

const ScoreFreeze: React.FC<Ctx> = (ctx) => {
  const {w, h, p, on, theme, t, steps} = ctx;
  const k = on(1) ? clamp01((t - steps[1]) / Math.max(0.4, (steps[2] ?? steps[1] + 1.6) - steps[1])) : 0;
  const day = Math.max(1, Math.round(19 * k));
  return (
    <g>
      <Card x={w * 0.1} y={h * 0.08} w={w * 0.8} h={h * 0.3} s={p(0, 0.3)} theme={theme}>
        <Txt x={w * 0.4} y={h * 0.1} size={40} color={theme.muted} spacing={6}>YOUR SCORE</Txt>
        <Txt x={w * 0.4} y={h * 0.24} size={150}>7</Txt>
      </Card>
      <Txt x={w / 2} y={h * 0.55} size={44} color={theme.accent} spacing={6} o={p(1, 0.2)}>DAYS WITHOUT CHANGE</Txt>
      <Txt x={w / 2} y={h * 0.74} size={200} color={on(2) ? theme.danger : '#fff'} o={p(1, 0.2)}>{`${on(1) ? day : 0}/19`}</Txt>
      {on(2) && <Pill x={w / 2} y={h * 0.9} text="technique removed" color={theme.danger} s={p(2, 0.25)} />}
    </g>
  );
};

// Colonies feed cursed energy into the merger. No names written inside circles: labels sit beside.
const EnergyMerge: React.FC<Ctx> = ({w, h, p, on, theme, t}) => {
  const src = Array.from({length: 10}).map((_, i) => [w * 0.14, h * (0.12 + i * 0.075)] as [number, number]);
  const hub: [number, number] = [w * 0.66, h * 0.46];
  return (
    <g>
      <Txt x={w * 0.14} y={h * 0.07} size={30} color={theme.accent2} o={p(0)}>10 COLONIES</Txt>
      {src.map(([x, y], i) => (
        <g key={i} opacity={p(0, 0.3)}>
          <rect x={x - 26} y={y - 18} width={52} height={36} rx={8} fill={theme.panel} stroke={theme.accent2} strokeWidth={4} />
          {on(1) && (() => {
            const k = (t * 0.9 + i / 10) % 1;
            return (
              <g>
                <line x1={x + 26} y1={y} x2={hub[0]} y2={hub[1]} stroke={theme.accent2} strokeOpacity={0.35} strokeWidth={4} />
                <circle cx={x + 26 + (hub[0] - x - 26) * k} cy={y + (hub[1] - y) * k} r={8} fill={theme.warn} />
              </g>
            );
          })()}
        </g>
      ))}
      <g opacity={p(1, 0.3)} transform={`translate(${hub[0]} ${hub[1]}) rotate(${t * 40})`}>
        {[0, 60, 120].map((r) => <rect key={r} x={-80} y={-80} width={160} height={160} rx={18} fill="none" stroke={theme.accent} strokeWidth={6} transform={`rotate(${r})`} style={{filter: `drop-shadow(0 0 12px ${theme.accent})`}} />)}
      </g>
      <Txt x={hub[0]} y={hub[1] + 150} size={36} color={theme.warn} o={p(1, 0.3)}>CURSED ENERGY</Txt>
      {on(2) && <Pill x={hub[0]} y={h * 0.86} text="merge humanity with tengen" color={theme.accent} s={p(2, 0.3)} size={28} />}
    </g>
  );
};

const Loophole: React.FC<Ctx> = ({w, h, p, on, theme, params}) => {
  const rules: string[] = params?.rules || ['1  JOIN WITHIN 19 DAYS', '2  OR LOSE YOUR TECHNIQUE', '3  ENTER A COLONY = PLAYER', '4  SCORE BY KILLING PLAYERS',
    '5  SORCERER 5 · NON-SORCERER 1', '6  100 POINTS = NEW RULE', '7  GM ACCEPTS UNLESS LONG-LASTING', '8  NO CHANGE IN 19 DAYS = REMOVAL'];
  const hl: number = params?.highlight ?? (rules.length - 1);
  return (
    <g>
      <Card x={w * 0.04} y={h * 0.04} w={w * 0.92} h={h * 0.9} s={p(0, 0.3)} theme={theme}>
        <Txt x={w * 0.46} y={h * 0.1} size={fit_(params?.title || 'THE RULES', w * 0.85, 46)} color={theme.accent} spacing={3}>{params?.title || 'THE RULES'}</Txt>
        {rules.map((r, i) => (
          <g key={i} opacity={p(0, 0.25 + i * 0.08)}>
            <Txt x={w * 0.05} y={h * (0.2 + i * 0.088)} size={fit_(r, w * 0.82, 32)} anchor="start" weight={800}>{r}</Txt>
          </g>
        ))}
      </Card>
      {on(1) && (
        <g opacity={p(1, 0.2)}>
          <rect x={w * 0.07} y={h * (0.2 + hl * 0.088) - 46} width={w * 0.86} height={68} rx={14} fill="none" stroke={theme.warn} strokeWidth={7} {...stroke(2000, p(1, 0.5))} />
        </g>
      )}
    </g>
  );
};

const FanProposal: React.FC<Ctx> = ({w, h, p, on, theme, params}) => {
  const tape = params?.tape || 'FAN PROPOSAL · NOT CANON';
  const top: string[] = params?.top || ['DEFEAT A CURSE', "THAT'S A PLAYER"];
  const bottom: string = params?.bottom || 'TAKE ALL ITS POINTS';
  const ask: string = params?.ask || 'WOULD IT PASS?';
  const cardW = w * 0.84;
  return (
    <g>
      <g transform={`translate(${w / 2} ${h * 0.08}) rotate(-2)`} opacity={p(0, 0.15)}>
        <rect x={-w * 0.44} y={-44} width={w * 0.88} height={88} fill={theme.warn} />
        <Txt x={0} y={14} size={fit_(tape, w * 0.8, 40)} color="#111">{tape}</Txt>
      </g>
      <Card x={w * 0.08} y={h * 0.18} w={cardW} h={h * 0.22} s={p(0, 0.3)} theme={theme} border={theme.accent2}>
        {top.map((l, i) => <Txt key={i} x={cardW / 2} y={h * (0.09 + i * 0.07)} size={fit_(l, cardW * 0.88, 46)}>{l}</Txt>)}
      </Card>
      <line x1={w / 2} y1={h * 0.42} x2={w / 2} y2={h * 0.5} stroke={theme.accent} strokeWidth={12} strokeLinecap="round" {...stroke(100, p(1, 0.3))} />
      {p(1, 0.3) > 0.9 && <polygon points={`${w / 2},${h * 0.53} ${w / 2 - 26},${h * 0.49} ${w / 2 + 26},${h * 0.49}`} fill={theme.accent} />}
      <Card x={w * 0.08} y={h * 0.55} w={cardW} h={h * 0.16} s={p(1, 0.3)} theme={theme}>
        <Txt x={cardW / 2} y={h * 0.1} size={fit_(bottom, cardW * 0.88, 48)} color={theme.accent}>{bottom}</Txt>
      </Card>
      {on(2) && <Txt x={w / 2} y={h * 0.86} size={fit_(ask, w * 0.9, 60)} color={theme.warn} o={p(2, 0.2)}>{ask}</Txt>}
    </g>
  );
};

const TitleCard: React.FC<Ctx> = ({w, h, p, theme, params}) => {
  const lines: string[] = params?.lines || ['THE CULLING GAME'];
  return (
    <g>
      {lines.map((l, i) => {
        const s = p(i, 0.18);
        return (
          <g key={i} transform={`translate(${w / 2} ${h * 0.4 + i * 130}) scale(${1.6 - 0.6 * s})`} opacity={s}>
            <Txt x={0} y={0} size={fit_(l, w * 0.9, params?.size || 110)} color={i === (params?.accentLine ?? 0) ? theme.accent2 : '#fff'}>{l}</Txt>
          </g>
        );
      })}
      {params?.sub && <Txt x={w / 2} y={h * 0.4 + lines.length * 130 + 20} size={40} color={theme.accent} spacing={6} o={p(lines.length, 0.3)}>{params.sub}</Txt>}
    </g>
  );
};

const Awakening: React.FC<Ctx> = ({w, h, p, theme, t, params}) => {
  const glow = 0.6 + 0.4 * Math.sin(t * 4);
  return (
    <g>
      <g opacity={p(0, 0.4)} transform={`translate(${w / 2} ${h * 0.48})`}>
        <circle r={150} fill="#141735" stroke={theme.ink} strokeWidth={6} />
        <rect x={-110} y={150} width={220} height={260} rx={90} fill="#141735" stroke={theme.ink} strokeWidth={6} />
        {[0, 1, 2, 3].map((i) => (
          <circle key={i} r={170 + i * 45 + (t * 60) % 45} fill="none" stroke={theme.accent} strokeWidth={6} opacity={(0.6 - i * 0.14) * p(1, 0.4) * glow} />
        ))}
      </g>
      <Pill x={w / 2} y={h * 0.08} text={params?.pill || 'cursed technique: awakened'} color={theme.accent} s={p(1, 0.25)} size={30} />
    </g>
  );
};


// Gears = the ritual machine; battles feed it. Labels outside the gears, never inside.
const Gear: React.FC<{x: number; y: number; r: number; teeth: number; rot: number; color: string; fill: string}> = ({x, y, r, teeth, rot, color, fill}) => {
  const pts: string[] = [];
  for (let i = 0; i < teeth * 2; i++) {
    const a = (Math.PI * i) / teeth;
    const rr = i % 2 === 0 ? r : r * 0.82;
    pts.push(`${Math.cos(a) * rr},${Math.sin(a) * rr}`);
  }
  return (
    <g transform={`translate(${x} ${y}) rotate(${rot})`}>
      <polygon points={pts.join(' ')} fill={fill} stroke={color} strokeWidth={6} strokeLinejoin="round" style={{filter: `drop-shadow(0 0 10px ${color})`}} />
      <circle r={r * 0.28} fill="none" stroke={color} strokeWidth={6} />
    </g>
  );
};

const CogMachine: React.FC<Ctx> = ({w, h, p, on, theme, t, params}) => {
  const spin = t * 50;
  const you = params?.you && on(2);
  return (
    <g opacity={p(0, 0.3)}>
      <Gear x={w * 0.38} y={h * 0.42} r={170} teeth={12} rot={spin} color={theme.accent} fill={theme.panel} />
      <Gear x={w * 0.7} y={h * 0.3} r={110} teeth={9} rot={-spin * 1.5 + 10} color={theme.accent2} fill={theme.panel} />
      <Gear x={w * 0.72} y={h * 0.6} r={90} teeth={8} rot={-spin * 1.9} color={you ? theme.warn : theme.accent} fill={theme.panel} />
      {you && <Pill x={w * 0.72} y={h * 0.74} text="you" color={theme.warn} s={p(2, 0.25)} />}
      {on(1) && Array.from({length: 6}).map((_, i) => {
        const k = (t * 0.8 + i / 6) % 1;
        return <circle key={i} cx={w * 0.05 + k * w * 0.2} cy={h * (0.42 + Math.sin(i) * 0.05)} r={10} fill={theme.danger} opacity={1 - k} />;
      })}
      {on(1) && <Txt x={w * 0.12} y={h * 0.3} size={28} color={theme.danger}>BATTLES</Txt>}
      <Txt x={w / 2} y={h * 0.86} size={fit_(params?.label || 'THE RITUAL', w * 0.9, 50)} color="#fff">{params?.label || 'THE RITUAL'}</Txt>
    </g>
  );
};

// Final question: held on screen so viewers can read and think.
const Question: React.FC<Ctx> = ({w, h, p, theme, params}) => {
  const lines: string[] = params?.lines || ['WHAT WOULD YOU DO?'];
  return (
    <g>
      {params?.chip && <Pill x={w / 2} y={h * 0.16} text={params.chip} color={theme.warn} s={p(0, 0.25)} size={36} />}
      {lines.map((l, i) => (
        <g key={i} opacity={p(i + 1, 0.25)}>
          <Txt x={w / 2} y={h * (0.4 + i * 0.12)} size={fit_(l, w * 0.9, 84)} color={i === lines.length - 1 ? theme.accent : '#fff'}>{l}</Txt>
        </g>
      ))}
    </g>
  );
};

const OrbOnly: React.FC<Ctx> = () => null;

const REGISTRY: Record<string, React.FC<Ctx>> = {
  hook_question: HookQuestion,
  loop_field: LoopField,
  detection_flow: DetectionFlow,
  methods: Methods,
  keyword: Keyword,
  counter: Counter,
  japan_colonies: JapanColonies,
  jjk_timer: JjkTimer,
  points: Points,
  rule_100: Rule100,
  score_freeze: ScoreFreeze,
  energy_merge: EnergyMerge,
  loophole: Loophole,
  fan_proposal: FanProposal,
  title_card: TitleCard,
  awakening: Awakening,
  cog_machine: CogMachine,
  question: Question,
  orb_only: OrbOnly,
};

export const DIAGRAM_NAMES = Object.keys(REGISTRY);

export const Diagram: React.FC<DiagramProps> = (props) => {
  const Comp = REGISTRY[props.name] || Keyword;
  const steps = props.steps && props.steps.length ? props.steps : [0];
  const ctx: Ctx = {
    ...props,
    steps,
    p: (i, d = 0.45) => (i < steps.length ? progress(props.t, steps[i], d) : 0),
    on: (i) => i < steps.length && props.t >= steps[i],
  };
  return (
    <svg width={props.w} height={props.h} viewBox={`0 0 ${props.w} ${props.h}`} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
      <Comp {...ctx} />
    </svg>
  );
};

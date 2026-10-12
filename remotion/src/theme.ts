// Layout + colour tokens shared by every component.
// TikTok safe box: everything that must be readable stays inside x 120-960, y 160-1440.
export const W = 1080;
export const H = 1920;
export const SAFE = {x0: 120, x1: 960, y0: 160, y1: 1440};

// Evidence box (footage / photos / diagrams, y 200-1250) and the caption lane under it.
// Captions never share space with the box, so they can't cover faces or on-screen text.
// Nothing is drawn in the bottom 300 px (TikTok caption/UI area).
export const BOX = {x: 120, y: 200, w: 840, h: 1050};
export const CAPTION_LANE = {top: 1290, bottom: 1440};
export const ORB = {x: 540, y: 1252, r: 34};
export const PURPLE = '#8B5CF6';

export const FONT = '"Montserrat", "DejaVu Sans", "Arial Black", sans-serif';

export type Theme = {
  name: string;
  bg: string;
  bg2: string;
  grid: string;
  panel: string;
  ink: string;
  muted: string;
  accent: string; // #2EA8FF: arrows, circles, labels, active caption word
  accent2: string;
  warn: string;
  danger: string;
  ok: string;
};

export const THEMES: Record<string, Theme> = {
  tech: {
    name: 'tech',
    bg: '#0A0E13',
    bg2: '#101923',
    grid: 'rgba(46,168,255,0.07)',
    panel: '#121C27',
    ink: '#F4F7FA',
    muted: '#8FA3B5',
    accent: '#2EA8FF',
    accent2: '#FFC53D',
    warn: '#FFC53D',
    danger: '#FF4D5E',
    ok: '#2BD47D',
  },
  jjk: {
    name: 'jjk',
    bg: '#070818',
    bg2: '#1A0B33',
    grid: 'rgba(46,168,255,0.08)',
    panel: '#0E1030',
    ink: '#F5F3FF',
    muted: '#A39CC9',
    accent: '#2EA8FF',
    accent2: '#FF3B6B',
    warn: '#FFC53D',
    danger: '#FF3B6B',
    ok: '#2BD47D',
  },
};

export const themeOf = (name?: string): Theme => THEMES[name || 'tech'] || THEMES.tech;

// Small easing helpers used by draw-on animations.
export const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
export const easeOut = (v: number) => 1 - Math.pow(1 - clamp01(v), 3);
export const progress = (t: number, at: number, dur: number) => easeOut((t - at) / Math.max(0.001, dur));

/** Design field: 390×680 portrait */
export const FIELD_W = 390;
export const FIELD_H = 680;

/** Each image slot height (approx) */
export const IMG_H = 280;

export interface DiffRegion {
  id: string;
  /** Normalized center X (0-1) */
  cx: number;
  /** Normalized center Y (0-1) */
  cy: number;
  /** Normalized hit radius */
  r: number;
  label_zh: string;
  label_en: string;
}

export interface LevelDef {
  id: string;
  charId: string;
  charName: string;
  baseImg: string;
  diffImg: string;
  differences: DiffRegion[];
}

export type GamePhase = 'idle' | 'select' | 'playing' | 'complete' | 'allClear';

export interface LevelResult {
  stars: number;
  score: number;
  time: number;
  errors: number;
  hints: number;
}

export interface SaveData {
  /** Unlocked level count (1-based, first level always unlocked) */
  unlocked: number;
  /** Best result per level id */
  results: Record<string, LevelResult>;
}

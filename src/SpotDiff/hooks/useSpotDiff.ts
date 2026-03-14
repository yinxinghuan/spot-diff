import { useState, useRef, useCallback, useEffect } from 'react';
import type { GamePhase, LevelDef, LevelResult, SaveData } from '../types';
import { LEVELS } from '../levels';
import { getLocale } from '../i18n';
import type { BubbleMood } from '../utils/expressions';
import { resumeAudio, playTap, playFound, playWrong, playHint, playComplete, playStart } from '../utils/sounds';

const STORAGE_KEY = 'sd_save';
const POINTS_PER_FIND = 100;
const TIME_BONUS_MAX = 300;
const TIME_PENALTY_RATE = 2;
const ERROR_PENALTY = 15;
const HINT_PENALTY = 30;
const STAR3_THRESHOLD = 0.8;
const STAR2_THRESHOLD = 0.5;
const MAX_HINTS = 3;
const COOLDOWN_MS = 500;

function loadSave(): SaveData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return { unlocked: 1, results: {} };
}

function writeSave(data: SaveData) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function calcScore(found: number, time: number, errors: number, hints: number): number {
  const findScore = found * POINTS_PER_FIND;
  const timeBonus = Math.max(0, TIME_BONUS_MAX - time * TIME_PENALTY_RATE);
  const errorPen = errors * ERROR_PENALTY;
  const hintPen = hints * HINT_PENALTY;
  return Math.max(0, findScore + timeBonus - errorPen - hintPen);
}

function calcStars(score: number, totalDiffs: number): number {
  const maxScore = totalDiffs * POINTS_PER_FIND + TIME_BONUS_MAX;
  const ratio = score / maxScore;
  if (ratio >= STAR3_THRESHOLD) return 3;
  if (ratio >= STAR2_THRESHOLD) return 2;
  return 1;
}

export function useSpotDiff() {
  const [phase, setPhase] = useState<GamePhase>('idle');
  const [save, setSave] = useState<SaveData>(loadSave);
  const [currentLevel, setCurrentLevel] = useState<LevelDef | null>(null);
  const [foundIds, setFoundIds] = useState<Set<string>>(new Set());
  const [time, setTime] = useState(0);
  const [errors, setErrors] = useState(0);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [lastResult, setLastResult] = useState<LevelResult | null>(null);
  const [isNewRecord, setIsNewRecord] = useState(false);
  const [bubbleText, setBubbleText] = useState<string | null>(null);
  const [bubbleMood, setBubbleMood] = useState<BubbleMood>('normal');
  const [bubbleLeaving, setBubbleLeaving] = useState(false);
  const [cooldown, setCooldown] = useState(false);
  const [hintTarget, setHintTarget] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const bubbleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bubbleLeaveRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Timer
  useEffect(() => {
    if (phase === 'playing') {
      timerRef.current = setInterval(() => setTime(t => t + 1), 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [phase]);

  const showBubble = useCallback((text: string, durationMs = 1500, mood: BubbleMood = 'normal') => {
    if (bubbleTimerRef.current) clearTimeout(bubbleTimerRef.current);
    if (bubbleLeaveRef.current) clearTimeout(bubbleLeaveRef.current);
    setBubbleLeaving(false);
    setBubbleMood(mood);
    setBubbleText(text);
    bubbleTimerRef.current = setTimeout(() => {
      setBubbleLeaving(true);
      bubbleLeaveRef.current = setTimeout(() => {
        setBubbleText(null);
        setBubbleLeaving(false);
      }, 300);
    }, durationMs);
  }, []);

  const goToSelect = useCallback(() => {
    setPhase('select');
    setCurrentLevel(null);
    setLastResult(null);
  }, []);

  const goHome = useCallback(() => {
    setPhase('idle');
    setCurrentLevel(null);
    setLastResult(null);
  }, []);

  const startLevel = useCallback((levelId: string) => {
    const level = LEVELS.find(l => l.id === levelId);
    if (!level) return;
    setCurrentLevel(level);
    setFoundIds(new Set());
    setTime(0);
    setErrors(0);
    setHintsUsed(0);
    setLastResult(null);
    setIsNewRecord(false);
    setHintTarget(null);
    setBubbleText(null);
    vagueHintShownRef.current = new Set();
    setPhase('playing');
    resumeAudio();
    playStart();
    // Show character start line after a short delay
    setTimeout(() => {
      showBubble(`bubble.start.${level.charId}`, 2000, 'normal');
    }, 500);
  }, [showBubble]);

  const completeLevel = useCallback((level: LevelDef, finalTime: number, finalErrors: number, finalHints: number) => {
    if (timerRef.current) clearInterval(timerRef.current);

    const score = calcScore(level.differences.length, finalTime, finalErrors, finalHints);
    const stars = calcStars(score, level.differences.length);
    const result: LevelResult = { stars, score, time: finalTime, errors: finalErrors, hints: finalHints };
    setLastResult(result);

    // Update save
    const newSave = { ...save };
    const prev = newSave.results[level.id];
    const isRecord = !prev || score > prev.score;
    if (isRecord) {
      newSave.results[level.id] = result;
    }

    // Unlock next level
    const levelIdx = LEVELS.findIndex(l => l.id === level.id);
    if (levelIdx + 2 > newSave.unlocked) {
      newSave.unlocked = Math.min(levelIdx + 2, LEVELS.length);
    }

    writeSave(newSave);
    setSave(newSave);
    setIsNewRecord(isRecord);
    setPhase('complete');
  }, [save]);

  const handleTap = useCallback((nx: number, ny: number) => {
    if (phase !== 'playing' || !currentLevel || cooldown) return;
    playTap();

    // Check hit
    for (const diff of currentLevel.differences) {
      if (foundIds.has(diff.id)) continue;
      const dx = nx - diff.cx;
      const dy = ny - diff.cy;
      if (Math.sqrt(dx * dx + dy * dy) <= diff.r) {
        // Hit!
        const newFound = new Set(foundIds);
        newFound.add(diff.id);
        setFoundIds(newFound);
        setHintTarget(null);
        playFound();
        showBubble(`bubble.found.${currentLevel.charId}`, 1500, 'happy');

        // Check completion
        if (newFound.size === currentLevel.differences.length) {
          playComplete();
          showBubble(`bubble.clear.${currentLevel.charId}`, 2500, 'happy');
          // Delay to let player see the last marker + celebration message
          setTimeout(() => {
            completeLevel(currentLevel, time, errors, hintsUsed);
          }, 2000);
        }
        return;
      }
    }

    // Miss
    playWrong();
    setErrors(e => e + 1);
    setCooldown(true);
    showBubble(`bubble.wrong.${currentLevel.charId}`, 1500, 'normal');
    setTimeout(() => setCooldown(false), COOLDOWN_MS);
  }, [phase, currentLevel, cooldown, foundIds, time, errors, hintsUsed, completeLevel, showBubble]);

  // Track which diffs have had vague hints shown (next press = specific)
  const vagueHintShownRef = useRef<Set<string>>(new Set());

  const useHint = useCallback(() => {
    if (phase !== 'playing' || !currentLevel || hintsUsed >= MAX_HINTS) return;

    const remaining = currentLevel.differences.filter(d => !foundIds.has(d.id));
    if (remaining.length === 0) return;

    const target = remaining[Math.floor(Math.random() * remaining.length)];
    setHintsUsed(h => h + 1);
    setHintTarget(null);
    playHint();

    const isZh = getLocale() === 'zh';
    const label = isZh ? target.label_zh : target.label_en;

    if (!vagueHintShownRef.current.has(target.id)) {
      // First tier: vague hint — general area description
      vagueHintShownRef.current.add(target.id);
      const area = target.cy < 0.33 ? (isZh ? '上方' : 'upper area')
        : target.cy > 0.66 ? (isZh ? '下方' : 'lower area')
        : (isZh ? '中间' : 'middle area');
      const side = target.cx < 0.33 ? (isZh ? '左侧' : 'left side')
        : target.cx > 0.66 ? (isZh ? '右侧' : 'right side')
        : (isZh ? '中央' : 'center');
      const vagueMsg = isZh ? `试试看${area}${side}…` : `Try the ${area}, ${side}...`;
      showBubble(vagueMsg, 2500);
    } else {
      // Second tier: specific hint — name the object
      const specificMsg = isZh ? `注意看${label}！` : `Look at the ${label}!`;
      showBubble(specificMsg, 2500);
    }
  }, [phase, currentLevel, hintsUsed, foundIds, showBubble]);

  const nextLevel = useCallback(() => {
    if (!currentLevel) return;
    const idx = LEVELS.findIndex(l => l.id === currentLevel.id);
    if (idx < LEVELS.length - 1) {
      startLevel(LEVELS[idx + 1].id);
    } else {
      setPhase('allClear');
    }
  }, [currentLevel, startLevel]);

  const isAllClear = LEVELS.every(l => save.results[l.id]);

  return {
    phase,
    save,
    currentLevel,
    foundIds,
    time,
    errors,
    hintsUsed,
    maxHints: MAX_HINTS,
    lastResult,
    isNewRecord,
    bubbleText,
    bubbleMood,
    bubbleLeaving,
    cooldown,
    hintTarget,
    levels: LEVELS,
    isAllClear,
    goHome,
    goToSelect,
    startLevel,
    handleTap,
    useHint,
    nextLevel,
  };
}

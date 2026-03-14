import React, { useState, useEffect, useRef, useCallback } from 'react';
import { LEVELS } from '../levels';

const ALL_IMAGES: string[] = LEVELS.flatMap(l => [l.baseImg, l.diffImg]);
const MIN_MS = 1800;
const MAX_ASSET_MS = 10000;

interface SplashScreenProps {
  onDone: () => void;
}

const SplashScreen: React.FC<SplashScreenProps> = ({ onDone }) => {
  const [progress, setProgress] = useState(0);
  const [fading, setFading] = useState(false);
  const [minDone, setMinDone] = useState(false);
  const [assetsDone, setAssetsDone] = useState(false);
  const doneCalledRef = useRef(false);

  useEffect(() => {
    const timer = setTimeout(() => setMinDone(true), MIN_MS);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const total = ALL_IMAGES.length;
    if (total === 0) {
      setAssetsDone(true);
      return;
    }
    let loaded = 0;
    const timeout = setTimeout(() => setAssetsDone(true), MAX_ASSET_MS);

    ALL_IMAGES.forEach((src) => {
      const img = new Image();
      img.onload = img.onerror = () => {
        loaded += 1;
        setProgress(loaded / total);
        if (loaded === total) {
          clearTimeout(timeout);
          setAssetsDone(true);
        }
      };
      img.src = src;
    });

    return () => clearTimeout(timeout);
  }, []);

  const triggerFade = useCallback(() => {
    if (doneCalledRef.current) return;
    doneCalledRef.current = true;
    setFading(true);
    setTimeout(onDone, 500);
  }, [onDone]);

  useEffect(() => {
    if (minDone && assetsDone) triggerFade();
  }, [minDone, assetsDone, triggerFade]);

  return (
    <div className={`sd-splash${fading ? ' sd-splash--fading' : ''}`}>
      <div className="sd-splash__content">
        <div className="sd-splash__icon">🔍</div>
        <h1 className="sd-splash__title">SPOT DIFF</h1>
      </div>
      <div className="sd-splash__bar-track">
        <div
          className="sd-splash__bar-fill"
          style={{ width: `${Math.round(progress * 100)}%` }}
        />
      </div>
    </div>
  );
};

export default React.memo(SplashScreen);

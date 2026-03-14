import React, { useState } from 'react';
import { useSpotDiff } from './hooks/useSpotDiff';
import { t } from './i18n';
import SplashScreen from './components/SplashScreen';
import LevelSelect from './components/LevelSelect';
import ImagePair from './components/ImagePair';
import CharBubble from './components/CharBubble';
import HintButton from './components/HintButton';
import aigramLogo from './img/aigram.svg';
import './SpotDiff.less';

const POINTS_PER_FIND = 100;

const SpotDiff: React.FC = () => {
  const [showSplash, setShowSplash] = useState(true);
  const {
    phase,
    save,
    currentLevel,
    foundIds,
    time,
    errors,
    hintsUsed,
    maxHints,
    lastResult,
    isNewRecord,
    bubbleText,
    cooldown,
    hintTarget,
    levels,
    goHome,
    goToSelect,
    startLevel,
    handleTap,
    useHint,
    nextLevel,
  } = useSpotDiff();

  if (showSplash) {
    return <SplashScreen onDone={() => setShowSplash(false)} />;
  }

  return (
    <div className="sd">
      {/* Watermark */}
      <img className="sd__watermark" src={aigramLogo} alt="" draggable={false} />

      {/* === IDLE / Title Screen === */}
      {phase === 'idle' && (
        <div className="sd__overlay">
          <div className="sd__modal">
            <div className="sd__modal-icon">🔍</div>
            <h1 className="sd__modal-title">{t('title')}</h1>
            <p className="sd__modal-sub">{t('subtitle')}</p>
            <div className="sd__modal-actions">
              <button className="sd__btn sd__btn--start" onPointerDown={goToSelect}>
                {t('startBtn')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* === Level Select === */}
      {phase === 'select' && (
        <LevelSelect
          levels={levels}
          save={save}
          onSelect={startLevel}
          onBack={goHome}
        />
      )}

      {/* === Playing === */}
      {phase === 'playing' && currentLevel && (
        <>
          {/* Header */}
          <div className="sd__header">
            <div className="sd__stat">
              <span className="sd__stat-label">{t('found')}</span>
              <span className="sd__stat-value">{foundIds.size}/{currentLevel.differences.length}</span>
            </div>
            <div className="sd__stat">
              <span className="sd__stat-label">{t('time')}</span>
              <span className="sd__stat-value">{time}s</span>
            </div>
            <div className="sd__stat">
              <span className="sd__stat-label">{t('errors')}</span>
              <span className="sd__stat-value">{errors}</span>
            </div>
          </div>

          {/* Image pair */}
          <ImagePair
            level={currentLevel}
            foundIds={foundIds}
            hintTarget={hintTarget}
            cooldown={cooldown}
            onTap={handleTap}
          />

          {/* Bottom bar */}
          <div className="sd__bottom">
            <CharBubble charName={currentLevel.charName} textKey={bubbleText} />
            <div className="sd__bottom-actions">
              <HintButton hintsUsed={hintsUsed} maxHints={maxHints} onHint={useHint} />
              <button className="sd__btn sd__btn--quit" onPointerDown={goToSelect}>
                {t('homeBtn')}
              </button>
            </div>
          </div>
        </>
      )}

      {/* === Level Complete === */}
      {phase === 'complete' && lastResult && currentLevel && (
        <div className="sd__overlay">
          <div className="sd__modal sd__modal--complete">
            <div className="sd__modal-icon">
              {'★'.repeat(lastResult.stars)}{'☆'.repeat(3 - lastResult.stars)}
            </div>
            <h2 className="sd__modal-title sd__modal-title--complete">{t('complete')}</h2>
            {isNewRecord && <div className="sd__new-record">{t('newRecord')}</div>}
            <div className="sd__result">
              <div className="sd__result-row">
                <span>{t('found')}</span>
                <strong>{currentLevel.differences.length} × {POINTS_PER_FIND}</strong>
              </div>
              <div className="sd__result-row">
                <span>{t('timeBonus')}</span>
                <strong>+{Math.max(0, 300 - lastResult.time * 2)}</strong>
              </div>
              <div className="sd__result-row">
                <span>{t('errorPenalty')}</span>
                <strong>-{lastResult.errors * 15}</strong>
              </div>
              <div className="sd__result-row">
                <span>{t('hintPenalty')}</span>
                <strong>-{lastResult.hints * 30}</strong>
              </div>
              <div className="sd__result-row sd__result-row--total">
                <span>{t('totalScore')}</span>
                <strong>{lastResult.score}</strong>
              </div>
            </div>
            <div className="sd__modal-actions">
              <button className="sd__btn sd__btn--start" onPointerDown={nextLevel}>
                {t('nextLevel')}
              </button>
              <button className="sd__btn sd__btn--back" onPointerDown={() => startLevel(currentLevel.id)}>
                {t('replayBtn')}
              </button>
              <button className="sd__btn sd__btn--back" onPointerDown={goToSelect}>
                {t('homeBtn')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* === All Clear === */}
      {phase === 'allClear' && (
        <div className="sd__overlay">
          <div className="sd__modal sd__modal--complete">
            <div className="sd__modal-icon">🏆</div>
            <h2 className="sd__modal-title">{t('allClear')}</h2>
            <p className="sd__modal-sub">{t('allClearSub')}</p>
            <div className="sd__modal-actions">
              <button className="sd__btn sd__btn--start" onPointerDown={goToSelect}>
                {t('selectLevel')}
              </button>
              <button className="sd__btn sd__btn--back" onPointerDown={goHome}>
                {t('homeBtn')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SpotDiff;

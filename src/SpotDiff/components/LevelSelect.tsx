import React from 'react';
import type { LevelDef, SaveData } from '../types';
import { t } from '../i18n';

interface LevelSelectProps {
  levels: LevelDef[];
  save: SaveData;
  onSelect: (levelId: string) => void;
  onBack: () => void;
}

const LevelSelect: React.FC<LevelSelectProps> = ({ levels, save, onSelect, onBack }) => {
  return (
    <div className="sd__select">
      <h2 className="sd__select-title">{t('selectLevel')}</h2>
      <div className="sd__select-grid">
        {levels.map((level, idx) => {
          const unlocked = idx < save.unlocked;
          const result = save.results[level.id];
          return (
            <div
              key={level.id}
              className={`sd__select-card${unlocked ? '' : ' sd__select-card--locked'}`}
              onPointerDown={unlocked ? () => onSelect(level.id) : undefined}
            >
              <div className="sd__select-card-bg">
                <img src={level.cardImg} alt="" draggable={false} />
              </div>
              <div className="sd__select-card-info">
                <div className="sd__select-card-num">{idx + 1}</div>
                <div className="sd__select-card-name">{level.charName}</div>
                {result ? (
                  <div className="sd__select-card-stars">
                    {'★'.repeat(result.stars)}{'☆'.repeat(3 - result.stars)}
                  </div>
                ) : unlocked ? (
                  <div className="sd__select-card-stars sd__select-card-stars--empty">☆☆☆</div>
                ) : (
                  <div className="sd__select-card-lock">🔒</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <button className="sd__btn sd__btn--back" onPointerDown={onBack}>
        {t('homeBtn')}
      </button>
    </div>
  );
};

export default React.memo(LevelSelect);

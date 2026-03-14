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
    <div className="sd__overlay">
      <div className="sd__modal">
        <h2 className="sd__modal-title">{t('selectLevel')}</h2>
        <div className="sd__level-grid">
          {levels.map((level, idx) => {
            const unlocked = idx < save.unlocked;
            const result = save.results[level.id];
            return (
              <div
                key={level.id}
                className={`sd__level-card${unlocked ? '' : ' sd__level-card--locked'}`}
                onPointerDown={unlocked ? () => onSelect(level.id) : undefined}
              >
                <div className="sd__level-num">{idx + 1}</div>
                <div className="sd__level-name">{level.charName}</div>
                {result ? (
                  <div className="sd__level-stars">
                    {'★'.repeat(result.stars)}{'☆'.repeat(3 - result.stars)}
                  </div>
                ) : unlocked ? (
                  <div className="sd__level-stars sd__level-stars--empty">☆☆☆</div>
                ) : (
                  <div className="sd__level-lock">🔒</div>
                )}
              </div>
            );
          })}
        </div>
        <button className="sd__btn sd__btn--back" onPointerDown={onBack}>
          {t('homeBtn')}
        </button>
      </div>
    </div>
  );
};

export default React.memo(LevelSelect);

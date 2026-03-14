import React from 'react';
import { t } from '../i18n';

interface CharBubbleProps {
  charName: string;
  textKey: string | null;
}

const CharBubble: React.FC<CharBubbleProps> = ({ charName, textKey }) => {
  if (!textKey) return null;

  return (
    <div className="sd__bubble">
      <span className="sd__bubble-name">{charName}</span>
      <span className="sd__bubble-text">{t(textKey)}</span>
    </div>
  );
};

export default React.memo(CharBubble);

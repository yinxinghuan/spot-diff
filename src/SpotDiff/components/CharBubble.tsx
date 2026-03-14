import React from 'react';
import { t } from '../i18n';
import { getExpressionUrl, type BubbleMood } from '../utils/expressions';

interface CharBubbleProps {
  charId: string;
  charName: string;
  textKey: string | null;
  mood: BubbleMood;
  leaving?: boolean;
}

const CharBubble: React.FC<CharBubbleProps> = ({ charId, charName, textKey, mood, leaving }) => {
  if (!textKey) return null;

  const isI18nKey = textKey.startsWith('bubble.');
  const text = isI18nKey ? t(textKey) : textKey;
  const avatarUrl = getExpressionUrl(charId, mood);

  return (
    <div className={`sd__vn${leaving ? ' sd__vn--leaving' : ''}`}>
      <div className="sd__vn-portrait">
        <img src={avatarUrl} alt={charName} draggable={false} />
      </div>
      <div className="sd__vn-box">
        <div className="sd__vn-name">{charName}</div>
        <div className="sd__vn-text">{text}</div>
      </div>
    </div>
  );
};

export default React.memo(CharBubble);

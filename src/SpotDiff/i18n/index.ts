type Locale = 'zh' | 'en';

const MESSAGES: Record<string, Record<Locale, string>> = {
  'title': { zh: '找茬大师', en: 'SPOT DIFF' },
  'subtitle': { zh: '找出两张图的不同之处', en: 'Find the differences between two images' },
  'startBtn': { zh: '开始游戏', en: 'START' },
  'selectLevel': { zh: '选择关卡', en: 'SELECT LEVEL' },
  'level': { zh: '第 {n} 关', en: 'LEVEL {n}' },
  'locked': { zh: '未解锁', en: 'LOCKED' },
  'found': { zh: '已找到', en: 'FOUND' },
  'time': { zh: '时间', en: 'TIME' },
  'score': { zh: '得分', en: 'SCORE' },
  'errors': { zh: '错误', en: 'ERRORS' },
  'hints': { zh: '提示', en: 'HINTS' },
  'hintBtn': { zh: '提示 ({n})', en: 'HINT ({n})' },
  'noHints': { zh: '无提示', en: 'NO HINTS' },
  'seconds': { zh: '{n}秒', en: '{n}s' },
  'complete': { zh: '关卡完成！', en: 'LEVEL CLEAR!' },
  'allClear': { zh: '全部通关！', en: 'ALL CLEAR!' },
  'allClearSub': { zh: '你找到了所有不同之处！', en: 'You found every difference!' },
  'stars': { zh: '{n} 星', en: '{n} Stars' },
  'nextLevel': { zh: '下一关', en: 'NEXT' },
  'replayBtn': { zh: '重玩', en: 'REPLAY' },
  'homeBtn': { zh: '返回', en: 'HOME' },
  'best': { zh: '最高分: {n}', en: 'Best: {n}' },
  'newRecord': { zh: '新纪录！', en: 'NEW RECORD!' },
  'timeBonus': { zh: '时间奖励', en: 'Time Bonus' },
  'errorPenalty': { zh: '错误扣分', en: 'Error Penalty' },
  'hintPenalty': { zh: '提示扣分', en: 'Hint Penalty' },
  'totalScore': { zh: '总分', en: 'Total' },
  // Character bubble lines
  'bubble.found': { zh: '找到了！', en: 'Found it!' },
  'bubble.wrong': { zh: '不对哦~', en: 'Nope~' },
  'bubble.hint': { zh: '看这里！', en: 'Look here!' },
  'bubble.clear': { zh: '太厉害了！', en: 'Amazing!' },
  'bubble.start': { zh: '来找找看！', en: "Let's go!" },
  // Character names
  'char.algram': { zh: 'Algram', en: 'Algram' },
  'char.jenny': { zh: 'Jenny', en: 'Jenny' },
  'char.jmf': { zh: 'JM·F', en: 'JM·F' },
  'char.ghostpixel': { zh: 'ghostpixel', en: 'ghostpixel' },
  'char.isaya': { zh: 'Isaya', en: 'Isaya' },
  'char.isabel': { zh: 'Isabel', en: 'Isabel' },
};

function detectLocale(): Locale {
  const override = localStorage.getItem('sd_locale');
  if (override === 'en' || override === 'zh') return override;
  return navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en';
}

let currentLocale: Locale = detectLocale();

export function t(key: string, vars?: { n?: number | string }): string {
  const entry = MESSAGES[key];
  let str = entry?.[currentLocale] ?? entry?.['en'] ?? key;
  if (vars?.n !== undefined) {
    str = str.replace('{n}', String(vars.n));
  }
  return str;
}

export function useLocale() {
  const setLocale = (l: Locale) => {
    currentLocale = l;
    localStorage.setItem('sd_locale', l);
  };
  return { t, locale: currentLocale, setLocale };
}

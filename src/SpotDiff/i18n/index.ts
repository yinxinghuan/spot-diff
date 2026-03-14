type Locale = 'zh' | 'en';

const MESSAGES: Record<string, Record<Locale, string>> = {
  'title': { zh: '找茬侦探', en: 'SPOT DIFF' },
  'subtitle': { zh: '发现隐藏的线索', en: 'Discover the hidden clues' },
  'startBtn': { zh: '开始调查', en: 'INVESTIGATE' },
  'selectLevel': { zh: '选择案件', en: 'SELECT CASE' },
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
  'complete': { zh: '案件解决！', en: 'CASE CLOSED!' },
  'allClear': { zh: '全案告破！', en: 'ALL CASES SOLVED!' },
  'allClearSub': { zh: '你是最出色的侦探！', en: 'You are the greatest detective!' },
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

  // Character-specific found lines
  'bubble.found.algram': { zh: '不错嘛，有点节奏感！', en: 'Nice rhythm!' },
  'bubble.found.jenny': { zh: 'Bug found! 准确率不错~', en: 'Bug found! Nice accuracy~' },
  'bubble.found.jmf': { zh: '……嗯，观察力可以。', en: '...Hm, good eyes.' },
  'bubble.found.ghostpixel': { zh: '嘻嘻，被你发现了~', en: 'Hehe, you found it~' },
  'bubble.found.isaya': { zh: '好眼力！像个艺术家~', en: 'Good eye! Like an artist~' },
  'bubble.found.isabel': { zh: '不错呢，品味很好♪', en: 'Nice taste~♪' },

  // Character-specific wrong lines
  'bubble.wrong.algram': { zh: '跑调了兄弟，再看看', en: 'Off-key, try again' },
  'bubble.wrong.jenny': { zh: '这不是Bug啦…', en: "That's not a bug..." },
  'bubble.wrong.jmf': { zh: '……不是那里。', en: '...Not there.' },
  'bubble.wrong.ghostpixel': { zh: '嘿嘿，想吓我？', en: 'Hehe, nice try~' },
  'bubble.wrong.isaya': { zh: '唔…再仔细看看？', en: 'Hmm, look closer?' },
  'bubble.wrong.isabel': { zh: '这里没什么不同哦', en: 'Nothing different here~' },

  // Character-specific clear lines
  'bubble.clear.algram': { zh: '完美演出！安可！', en: 'Perfect show! Encore!' },
  'bubble.clear.jenny': { zh: '全部修复！可以上线了！', en: 'All fixed! Ready to ship!' },
  'bubble.clear.jmf': { zh: '……不错。', en: '...Impressive.' },
  'bubble.clear.ghostpixel': { zh: '全找到了！你是通灵师吗？', en: 'Found all! Are you psychic?' },
  'bubble.clear.isaya': { zh: '太厉害了！要画下来！', en: 'Amazing! I must paint this!' },
  'bubble.clear.isabel': { zh: '完美！就像最美的花束♪', en: 'Perfect! Like a bouquet~♪' },

  // Character-specific start lines
  'bubble.start.algram': { zh: '来我的录音室找找看！', en: 'Spot the diff in my studio!' },
  'bubble.start.jenny': { zh: '帮我Debug一下这个房间~', en: 'Help me debug this room~' },
  'bubble.start.jmf': { zh: '……有人动过我的东西。', en: '...Someone touched my stuff.' },
  'bubble.start.ghostpixel': { zh: '这屋子有点不对劲…', en: "Something's off here..." },
  'bubble.start.isaya': { zh: '我的画室有些变化呢~', en: 'My studio looks different~' },
  'bubble.start.isabel': { zh: '谁动了我的洗衣房！', en: 'Someone messed with my laundry!' },

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

export function getLocale(): Locale {
  return currentLocale;
}

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

// Character expression images
// Each character has: normal, happy
const expressionModules = import.meta.glob('../img/chars/expressions/*.png', { eager: true, import: 'default' }) as Record<string, string>;

type Expression = 'normal' | 'happy';

const cache: Record<string, Record<Expression, string>> = {};

function getExpressionMap(charId: string): Record<Expression, string> {
  if (cache[charId]) return cache[charId];

  const map: Record<Expression, string> = { normal: '', happy: '' };
  for (const [path, url] of Object.entries(expressionModules)) {
    if (path.includes(`${charId}_normal`)) map.normal = url;
    if (path.includes(`${charId}_happy`)) map.happy = url;
  }

  // Fallback: if no expression found, use normal for both
  if (!map.happy && map.normal) map.happy = map.normal;
  if (!map.normal && map.happy) map.normal = map.happy;

  cache[charId] = map;
  return map;
}

export type BubbleMood = 'normal' | 'happy';

export function getExpressionUrl(charId: string, mood: BubbleMood): string {
  return getExpressionMap(charId)[mood] || '';
}

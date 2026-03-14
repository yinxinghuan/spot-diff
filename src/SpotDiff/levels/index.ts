import type { LevelDef } from '../types';

import algramBase from '../img/levels/algram/base.png';
import jennyBase from '../img/levels/jenny/base.png';
import jmfBase from '../img/levels/jmf/base.png';
import ghostpixelBase from '../img/levels/ghostpixel/base.png';
import isayaBase from '../img/levels/isaya/base.png';
import isabelBase from '../img/levels/isabel/base.png';

import algramDiff from '../img/levels/algram/diff.png';
import jennyDiff from '../img/levels/jenny/diff.png';
import jmfDiff from '../img/levels/jmf/diff.png';
import ghostpixelDiff from '../img/levels/ghostpixel/diff.png';
import isayaDiff from '../img/levels/isaya/diff.png';
import isabelDiff from '../img/levels/isabel/diff.png';

import algramAvatar from '../img/chars/algram.png';
import jennyAvatar from '../img/chars/jenny.png';
import jmfAvatar from '../img/chars/jmf.png';
import ghostpixelAvatar from '../img/chars/ghostpixel.png';
import isayaAvatar from '../img/chars/isaya.png';
import isabelAvatar from '../img/chars/isabel.png';

import algramCard from '../img/cards/algram.png';
import jennyCard from '../img/cards/jenny.png';
import jmfCard from '../img/cards/jmf.png';
import ghostpixelCard from '../img/cards/ghostpixel.png';
import isayaCard from '../img/cards/isaya.png';
import isabelCard from '../img/cards/isabel.png';

export const LEVELS: LevelDef[] = [
  {
    id: 'algram',
    charId: 'algram',
    charName: 'Algram',
    avatar: algramAvatar,
    cardImg: algramCard,
    baseImg: algramBase,
    diffImg: algramDiff,
    differences: [
      { id: 'a1', cx: 0.174, cy: 0.643, r: 0.18, label_zh: '吉他颜色', label_en: 'Guitar color' },
      { id: 'a2', cx: 0.697, cy: 0.369, r: 0.12, label_zh: '黑胶唱片', label_en: 'Vinyl record' },
      { id: 'a3', cx: 0.114, cy: 0.931, r: 0.10, label_zh: '耳机颜色', label_en: 'Headphones' },
    ],
  },
  {
    id: 'jenny',
    charId: 'jenny',
    charName: 'Jenny',
    avatar: jennyAvatar,
    cardImg: jennyCard,
    baseImg: jennyBase,
    diffImg: jennyDiff,
    differences: [
      { id: 'j1', cx: 0.185, cy: 0.554, r: 0.16, label_zh: '台灯颜色', label_en: 'Desk lamp' },
      { id: 'j2', cx: 0.855, cy: 0.644, r: 0.12, label_zh: '猫咪', label_en: 'Cat' },
      { id: 'j3', cx: 0.281, cy: 0.883, r: 0.10, label_zh: '盆栽植物', label_en: 'Plant' },
    ],
  },
  {
    id: 'jmf',
    charId: 'jmf',
    charName: 'JM·F',
    avatar: jmfAvatar,
    cardImg: jmfCard,
    baseImg: jmfBase,
    diffImg: jmfDiff,
    differences: [
      { id: 'm1', cx: 0.525, cy: 0.119, r: 0.14, label_zh: '霓虹灯', label_en: 'Neon sign' },
      { id: 'm2', cx: 0.156, cy: 0.870, r: 0.12, label_zh: '地面物品', label_en: 'Floor items' },
      { id: 'm3', cx: 0.626, cy: 0.774, r: 0.12, label_zh: '地面线缆', label_en: 'Floor cables' },
    ],
  },
  {
    id: 'ghostpixel',
    charId: 'ghostpixel',
    charName: 'ghostpixel',
    avatar: ghostpixelAvatar,
    cardImg: ghostpixelCard,
    baseImg: ghostpixelBase,
    diffImg: ghostpixelDiff,
    differences: [
      { id: 'g1', cx: 0.937, cy: 0.483, r: 0.12, label_zh: '右侧机器', label_en: 'Right machine' },
      { id: 'g2', cx: 0.948, cy: 0.272, r: 0.12, label_zh: '右上区域', label_en: 'Upper right' },
      { id: 'g3', cx: 0.623, cy: 0.707, r: 0.12, label_zh: '地面物品', label_en: 'Floor item' },
    ],
  },
  {
    id: 'isaya',
    charId: 'isaya',
    charName: 'Isaya',
    avatar: isayaAvatar,
    cardImg: isayaCard,
    baseImg: isayaBase,
    diffImg: isayaDiff,
    differences: [
      { id: 'i1', cx: 0.244, cy: 0.479, r: 0.12, label_zh: '桌面区域', label_en: 'Desk area' },
      { id: 'i2', cx: 0.363, cy: 0.713, r: 0.10, label_zh: '地面物品', label_en: 'Floor item' },
      { id: 'i3', cx: 0.542, cy: 0.657, r: 0.10, label_zh: '床边物品', label_en: 'Bed area' },
    ],
  },
  {
    id: 'isabel',
    charId: 'isabel',
    charName: 'Isabel',
    avatar: isabelAvatar,
    cardImg: isabelCard,
    baseImg: isabelBase,
    diffImg: isabelDiff,
    differences: [
      { id: 'b1', cx: 0.681, cy: 0.630, r: 0.10, label_zh: '水槽区域', label_en: 'Sink area' },
      { id: 'b2', cx: 0.403, cy: 0.119, r: 0.10, label_zh: '架子物品', label_en: 'Shelf items' },
      { id: 'b3', cx: 0.498, cy: 0.497, r: 0.10, label_zh: '洗衣机上', label_en: 'Washer top' },
    ],
  },
];

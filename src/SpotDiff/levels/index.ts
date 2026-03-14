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

export const LEVELS: LevelDef[] = [
  {
    id: 'algram',
    charId: 'algram',
    charName: 'Algram',
    baseImg: algramBase,
    diffImg: algramDiff,
    differences: [
      { id: 'a1', cx: 0.08, cy: 0.45, r: 0.055, label_zh: '吉他颜色', label_en: 'Guitar color' },
      { id: 'a2', cx: 0.35, cy: 0.35, r: 0.05, label_zh: '音箱指示灯', label_en: 'Amp indicator' },
      { id: 'a3', cx: 0.72, cy: 0.28, r: 0.055, label_zh: '唱片封面', label_en: 'Vinyl cover' },
      { id: 'a4', cx: 0.4, cy: 0.85, r: 0.05, label_zh: '踏板灯', label_en: 'Pedal light' },
      { id: 'a5', cx: 0.88, cy: 0.35, r: 0.045, label_zh: '谱架标记', label_en: 'Sheet mark' },
    ],
  },
  {
    id: 'jenny',
    charId: 'jenny',
    charName: 'Jenny',
    baseImg: jennyBase,
    diffImg: jennyDiff,
    differences: [
      { id: 'j1', cx: 0.28, cy: 0.35, r: 0.055, label_zh: '屏幕代码', label_en: 'Screen code' },
      { id: 'j2', cx: 0.38, cy: 0.72, r: 0.05, label_zh: '咖啡杯', label_en: 'Coffee mug' },
      { id: 'j3', cx: 0.35, cy: 0.12, r: 0.05, label_zh: '便签颜色', label_en: 'Sticky note' },
      { id: 'j4', cx: 0.5, cy: 0.75, r: 0.05, label_zh: '键盘灯', label_en: 'Keyboard LED' },
      { id: 'j5', cx: 0.78, cy: 0.55, r: 0.05, label_zh: '猫咪颜色', label_en: 'Cat color' },
    ],
  },
  {
    id: 'jmf',
    charId: 'jmf',
    charName: 'JM·F',
    baseImg: jmfBase,
    diffImg: jmfDiff,
    differences: [
      { id: 'm1', cx: 0.2, cy: 0.35, r: 0.055, label_zh: '终端文字', label_en: 'Terminal text' },
      { id: 'm2', cx: 0.82, cy: 0.4, r: 0.05, label_zh: '服务器灯', label_en: 'Server LED' },
      { id: 'm3', cx: 0.5, cy: 0.25, r: 0.05, label_zh: '屏幕图标', label_en: 'Screen icon' },
      { id: 'm4', cx: 0.45, cy: 0.85, r: 0.05, label_zh: '线缆颜色', label_en: 'Cable color' },
      { id: 'm5', cx: 0.7, cy: 0.8, r: 0.05, label_zh: '能量饮料', label_en: 'Energy drink' },
    ],
  },
  {
    id: 'ghostpixel',
    charId: 'ghostpixel',
    charName: 'ghostpixel',
    baseImg: ghostpixelBase,
    diffImg: ghostpixelDiff,
    differences: [
      { id: 'g1', cx: 0.18, cy: 0.25, r: 0.055, label_zh: '浮空书本', label_en: 'Floating book' },
      { id: 'g2', cx: 0.5, cy: 0.45, r: 0.05, label_zh: '传送门光芒', label_en: 'Portal glow' },
      { id: 'g3', cx: 0.65, cy: 0.3, r: 0.05, label_zh: '幽灵颜色', label_en: 'Ghost color' },
      { id: 'g4', cx: 0.12, cy: 0.45, r: 0.055, label_zh: '镜中光点', label_en: 'Mirror light' },
      { id: 'g5', cx: 0.45, cy: 0.9, r: 0.05, label_zh: '地毯花纹', label_en: 'Rug pattern' },
    ],
  },
  {
    id: 'isaya',
    charId: 'isaya',
    charName: 'Isaya',
    baseImg: isayaBase,
    diffImg: isayaDiff,
    differences: [
      { id: 'i1', cx: 0.18, cy: 0.5, r: 0.055, label_zh: '画板颜料', label_en: 'Canvas paint' },
      { id: 'i2', cx: 0.52, cy: 0.3, r: 0.05, label_zh: '黑猫颜色', label_en: 'Cat color' },
      { id: 'i3', cx: 0.58, cy: 0.45, r: 0.05, label_zh: '耳机颜色', label_en: 'Headphone color' },
      { id: 'i4', cx: 0.22, cy: 0.85, r: 0.05, label_zh: '颜料色块', label_en: 'Paint spot' },
      { id: 'i5', cx: 0.82, cy: 0.7, r: 0.045, label_zh: '床上物品', label_en: 'Bed item' },
    ],
  },
  {
    id: 'isabel',
    charId: 'isabel',
    charName: 'Isabel',
    baseImg: isabelBase,
    diffImg: isabelDiff,
    differences: [
      { id: 'b1', cx: 0.2, cy: 0.65, r: 0.055, label_zh: '玫瑰花色', label_en: 'Rose color' },
      { id: 'b2', cx: 0.48, cy: 0.3, r: 0.05, label_zh: '镜中倒影', label_en: 'Mirror reflection' },
      { id: 'b3', cx: 0.75, cy: 0.45, r: 0.05, label_zh: '百合花色', label_en: 'Lily color' },
      { id: 'b4', cx: 0.42, cy: 0.6, r: 0.05, label_zh: '珠宝盒', label_en: 'Jewelry box' },
      { id: 'b5', cx: 0.7, cy: 0.7, r: 0.045, label_zh: '香水瓶', label_en: 'Perfume bottle' },
    ],
  },
];

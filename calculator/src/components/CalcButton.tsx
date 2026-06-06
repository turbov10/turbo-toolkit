import { Button, View, Text } from '@tarojs/components';
import { vibrateShort } from '@tarojs/taro';
import type { Key } from '../lib/useCalculator';
import './CalcButton.scss';

type Props = {
  keyDef: Key;
  label: string;
  variant: 'fn' | 'num' | 'op' | 'eq' | 'ghost';
  onPress: (k: Key) => void;
  flex?: number;
};

export function CalcButton({ keyDef, label, variant, onPress, flex = 1 }: Props) {
  const handleClick = () => {
    try {
      vibrateShort({ type: 'light' });
    } catch {
      // h5/tauri: vibrateShort is a no-op
    }
    onPress(keyDef);
  };

  return (
    <View className="calc-cell" style={{ flex }}>
      <Button
        className={'calc-btn calc-btn--' + variant}
        hoverClass="calc-btn--active"
        onClick={handleClick}
        // @ts-ignore — Taro's plain props
        plain
      >
        <Text className="calc-btn__label">{label}</Text>
      </Button>
    </View>
  );
}

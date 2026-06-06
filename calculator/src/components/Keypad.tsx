import { View } from '@tarojs/components';
import { CalcButton } from './CalcButton';
import type { Key } from '../lib/useCalculator';
import './Keypad.scss';

type Props = {
  onPress: (k: Key) => void;
};

export function Keypad({ onPress }: Props) {
  return (
    <View className="calc-keypad">
      <View className="calc-keypad__row">
        <CalcButton
          keyDef={{ kind: 'ac' }}
          label="AC"
          variant="fn"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'negate' }}
          label="±"
          variant="fn"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'percent' }}
          label="%"
          variant="fn"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'op', value: '÷' }}
          label="÷"
          variant="op"
          onPress={onPress}
        />
      </View>

      <View className="calc-keypad__row">
        <CalcButton
          keyDef={{ kind: 'digit', value: '7' }}
          label="7"
          variant="num"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'digit', value: '8' }}
          label="8"
          variant="num"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'digit', value: '9' }}
          label="9"
          variant="num"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'op', value: '×' }}
          label="×"
          variant="op"
          onPress={onPress}
        />
      </View>

      <View className="calc-keypad__row">
        <CalcButton
          keyDef={{ kind: 'digit', value: '4' }}
          label="4"
          variant="num"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'digit', value: '5' }}
          label="5"
          variant="num"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'digit', value: '6' }}
          label="6"
          variant="num"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'op', value: '−' }}
          label="−"
          variant="op"
          onPress={onPress}
        />
      </View>

      <View className="calc-keypad__row">
        <CalcButton
          keyDef={{ kind: 'digit', value: '1' }}
          label="1"
          variant="num"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'digit', value: '2' }}
          label="2"
          variant="num"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'digit', value: '3' }}
          label="3"
          variant="num"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'op', value: '+' }}
          label="+"
          variant="op"
          onPress={onPress}
        />
      </View>

      <View className="calc-keypad__row">
        <CalcButton
          keyDef={{ kind: 'digit', value: '0' }}
          label="0"
          variant="num"
          onPress={onPress}
          flex={2}
        />
        <CalcButton
          keyDef={{ kind: 'dot' }}
          label="."
          variant="num"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'back' }}
          label="⌫"
          variant="ghost"
          onPress={onPress}
        />
        <CalcButton
          keyDef={{ kind: 'eq' }}
          label="="
          variant="eq"
          onPress={onPress}
        />
      </View>
    </View>
  );
}

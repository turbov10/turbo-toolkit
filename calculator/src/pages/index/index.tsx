import { View } from '@tarojs/components';
import { Display } from '../../components/Display';
import { Keypad } from '../../components/Keypad';
import { useCalculator } from '../../lib/useCalculator';
import './index.scss';

export default function Index() {
  const { state, press } = useCalculator();

  return (
    <View className="page page--calc">
      <Display state={state} />
      <Keypad onPress={press} />
      <View className="calc-footer">
        <View className="calc-footer__hint">长按 AC 重置</View>
      </View>
    </View>
  );
}

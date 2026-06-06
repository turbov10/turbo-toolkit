import { View, Text } from '@tarojs/components';
import type { CalcState } from '../lib/useCalculator';
import './Display.scss';

type Props = {
  state: CalcState;
};

function prettyExpression(expr: string): string {
  return expr.replace(/\*/g, '×').replace(/\//g, '÷');
}

export function Display({ state }: Props) {
  const { expression, result, error, justEvaluated } = state;
  const exprText = prettyExpression(expression);
  const mainText = error ? 'Error' : result;
  const mainIsResult = justEvaluated || error;

  return (
    <View className="calc-display">
      <View className="calc-display__header">
        <Text className="calc-display__title">Calculator</Text>
        <Text className="calc-display__subtitle">标准</Text>
      </View>
      <View className="calc-display__history">
        <Text className="calc-display__history-text" decode={false}>
          {exprText || '\u00A0'}
        </Text>
      </View>
      <View className="calc-display__main">
        <Text
          className={
            'calc-display__main-text ' +
            (mainIsResult ? 'is-result' : 'is-input')
          }
        >
          {mainText}
        </Text>
      </View>
    </View>
  );
}

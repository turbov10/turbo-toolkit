import { useCallback, useMemo, useState } from 'react';
import { evaluate, formatResult } from './calc';

type Op = '+' | '−' | '×' | '÷';

export type Key =
  | { kind: 'digit'; value: string }
  | { kind: 'op'; value: Op }
  | { kind: 'dot' }
  | { kind: 'paren'; value: '(' | ')' }
  | { kind: 'ac' }
  | { kind: 'back' }
  | { kind: 'eq' }
  | { kind: 'percent' }
  | { kind: 'negate' };

export type CalcState = {
  expression: string;
  result: string;
  error: string | null;
  justEvaluated: boolean;
};

const INITIAL: CalcState = {
  expression: '',
  result: '0',
  error: null,
  justEvaluated: false,
};

function appendNumber(state: CalcState, digit: string): CalcState {
  if (state.error) {
    return { expression: digit, result: digit, error: null, justEvaluated: false };
  }
  if (state.justEvaluated) {
    return { expression: digit, result: digit, error: null, justEvaluated: false };
  }
  // prevent multiple dots in a single number segment
  const seg = lastNumberSegment(state.expression);
  if (digit === '0' && seg === '0') return state;
  if (seg === '0' && digit !== '.') {
    return {
      ...state,
      expression: state.expression.slice(0, -1) + digit,
      result: digit,
    };
  }
  if (seg.includes('.')) return state;
  return {
    ...state,
    expression: state.expression + digit,
    result: state.result === '0' ? digit : state.result + digit,
  };
}

function lastNumberSegment(expr: string): string {
  const m = expr.match(/[0-9.]*$/);
  return m ? m[0] : '';
}

function appendDot(state: CalcState): CalcState {
  if (state.error) return { ...INITIAL };
  if (state.justEvaluated) {
    return { expression: '0.', result: '0.', error: null, justEvaluated: false };
  }
  const seg = lastNumberSegment(state.expression);
  if (seg.includes('.')) return state;
  if (seg === '') {
    return {
      ...state,
      expression: state.expression + '0.',
      result: '0.',
    };
  }
  return {
    ...state,
    expression: state.expression + '.',
    result: state.result + '.',
  };
}

function appendOp(state: CalcState, op: Op): CalcState {
  if (state.error) return state;
  if (state.expression === '') {
    if (op === '−') {
      return { ...state, expression: '-', result: '-' };
    }
    return state;
  }
  const last = state.expression.slice(-1);
  if (last === '+' || last === '-' || last === '×' || last === '÷' || last === '.') {
    // replace last operator
    return {
      ...state,
      expression: state.expression.slice(0, -1) + op,
      justEvaluated: false,
    };
  }
  return {
    ...state,
    expression: state.expression + op,
    justEvaluated: false,
  };
}

function appendParen(state: CalcState, paren: '(' | ')'): CalcState {
  if (state.error) return state;
  if (paren === '(') {
    if (state.justEvaluated) {
      return { expression: '(', result: '(', error: null, justEvaluated: false };
    }
    const last = state.expression.slice(-1);
    if (/[0-9)]/.test(last)) {
      // implicit multiplication
      return {
        ...state,
        expression: state.expression + '×(',
        result: '(',
      };
    }
    return {
      ...state,
      expression: state.expression + '(',
      result: '(',
    };
  }
  // close paren: only if there is an unmatched '('
  const opens = (state.expression.match(/\(/g) || []).length;
  const closes = (state.expression.match(/\)/g) || []).length;
  if (opens <= closes) return state;
  const last = state.expression.slice(-1);
  if (last === '.' || /[+\-×÷(]/.test(last)) return state;
  return {
    ...state,
    expression: state.expression + ')',
    result: ')',
  };
}

function backspace(state: CalcState): CalcState {
  if (state.error) return { ...INITIAL };
  if (state.justEvaluated) return { ...INITIAL };
  if (state.expression.length === 0) return state;
  return {
    ...state,
    expression: state.expression.slice(0, -1),
    result: state.expression.length <= 1 ? '0' : state.result.slice(0, -1),
  };
}

function toggleSign(state: CalcState): CalcState {
  if (state.error || !state.expression) return state;
  // find the last number and toggle its sign
  const m = state.expression.match(/(-?\d*\.?\d+)$/);
  if (!m) return state;
  const num = m[0];
  const start = m.index!;
  let replaced: string;
  if (num.startsWith('-')) {
    replaced = num.slice(1);
  } else {
    replaced = '-' + num;
  }
  const newExpr = state.expression.slice(0, start) + replaced;
  try {
    const r = formatResult(evaluate(newExpr));
    return { ...state, expression: newExpr, result: r, error: null };
  } catch {
    return { ...state, expression: newExpr };
  }
}

function percent(state: CalcState): CalcState {
  if (state.error || !state.expression) return state;
  // turn the last number into "num/100"
  const m = state.expression.match(/(\d*\.?\d+)$/);
  if (!m) return state;
  const num = Number(m[0]);
  const newNum = num / 100;
  const newExpr = state.expression.slice(0, m.index) + String(newNum);
  return {
    ...state,
    expression: newExpr,
    result: formatResult(newNum),
  };
}

function equals(state: CalcState): CalcState {
  if (state.error) return state;
  if (!state.expression) return state;
  // auto-close parens
  const opens = (state.expression.match(/\(/g) || []).length;
  const closes = (state.expression.match(/\)/g) || []).length;
  const padded = state.expression + ')'.repeat(Math.max(0, opens - closes));
  try {
    const v = evaluate(padded);
    const formatted = formatResult(v);
    return {
      expression: padded,
      result: formatted,
      error: null,
      justEvaluated: true,
    };
  } catch (e) {
    return {
      ...state,
      error: e instanceof Error ? e.message : 'Error',
      result: 'Error',
    };
  }
}

function allClear(): CalcState {
  return { ...INITIAL };
}

export function useCalculator() {
  const [state, setState] = useState<CalcState>(INITIAL);

  const press = useCallback((key: Key) => {
    setState((s) => {
      switch (key.kind) {
        case 'digit':
          return appendNumber(s, key.value);
        case 'dot':
          return appendDot(s);
        case 'op':
          return appendOp(s, key.value);
        case 'paren':
          return appendParen(s, key.value);
        case 'back':
          return backspace(s);
        case 'ac':
          return allClear();
        case 'eq':
          return equals(s);
        case 'negate':
          return toggleSign(s);
        case 'percent':
          return percent(s);
      }
    });
  }, []);

  const api = useMemo(
    () => ({
      state,
      press,
    }),
    [state, press],
  );

  return api;
}

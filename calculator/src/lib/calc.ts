type Token =
  | { kind: 'num'; value: number }
  | { kind: 'op'; value: '+' | '-' | '*' | '/' }
  | { kind: 'lparen' }
  | { kind: 'rparen' };

type OpChar = '+' | '-' | '*' | '/';
const OP_PRECEDENCE: Record<OpChar, number> = {
  '+': 1,
  '-': 1,
  '*': 2,
  '/': 2,
};

function normalizeOp(ch: string): OpChar | null {
  switch (ch) {
    case '+':
      return '+';
    case '-':
    case '−':
      return '-';
    case '*':
    case '×':
    case '·':
      return '*';
    case '/':
    case '÷':
      return '/';
    default:
      return null;
  }
}

function tokenize(input: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;
  let prev: Token | null = null;

  while (i < input.length) {
    const ch = input[i];

    if (ch === ' ' || ch === '\t') {
      i += 1;
      continue;
    }

    if (ch === '(') {
      tokens.push({ kind: 'lparen' });
      prev = tokens[tokens.length - 1];
      i += 1;
      continue;
    }

    if (ch === ')') {
      tokens.push({ kind: 'rparen' });
      prev = tokens[tokens.length - 1];
      i += 1;
      continue;
    }

    if (ch === '+' || ch === '-' || ch === '*' || ch === '/' || ch === '×' || ch === '÷' || ch === '−' || ch === '·') {
      const opChar = normalizeOp(ch);
      if (!opChar) {
        i += 1;
        continue;
      }
      const isAfterValue = prev !== null && (prev.kind === 'num' || prev.kind === 'rparen');
      const isUnaryMinus =
        opChar === '-' && !isAfterValue;
      const isUnaryPlus =
        opChar === '+' && !isAfterValue;

      if (isUnaryPlus) {
        // skip leading/trailing plus
        i += 1;
        continue;
      }

      if (isUnaryMinus) {
        // emit 0 minus for unary so it parses as 0 - x
        tokens.push({ kind: 'num', value: 0 });
        tokens.push({ kind: 'op', value: '-' });
        prev = tokens[tokens.length - 1];
        i += 1;
        continue;
      }

      tokens.push({ kind: 'op', value: opChar });
      prev = tokens[tokens.length - 1];
      i += 1;
      continue;
    }

    if ((ch >= '0' && ch <= '9') || ch === '.') {
      let j = i;
      let dotSeen = ch === '.';
      while (j < input.length) {
        const c = input[j];
        if (c >= '0' && c <= '9') {
          j += 1;
        } else if (c === '.' && !dotSeen) {
          dotSeen = true;
          j += 1;
        } else {
          break;
        }
      }
      if (j === i || (input[i] === '.' && j === i + 1)) {
        // empty number like "."; ignore
        i += 1;
        continue;
      }
      const numStr = input.slice(i, j);
      const value = Number(numStr);
      if (Number.isNaN(value)) {
        throw new Error(`Invalid number: ${numStr}`);
      }
      tokens.push({ kind: 'num', value });
      prev = tokens[tokens.length - 1];
      i = j;
      continue;
    }

    throw new Error(`Unexpected character: ${ch}`);
  }

  return tokens;
}

function toRPN(tokens: Token[]): Token[] {
  const out: Token[] = [];
  const stack: Token[] = [];
  for (const t of tokens) {
    if (t.kind === 'num') {
      out.push(t);
    } else if (t.kind === 'op') {
      while (stack.length) {
        const top = stack[stack.length - 1];
        if (
          top.kind === 'op' &&
          OP_PRECEDENCE[top.value] >= OP_PRECEDENCE[t.value]
        ) {
          out.push(stack.pop() as Token);
        } else {
          break;
        }
      }
      stack.push(t);
    } else if (t.kind === 'lparen') {
      stack.push(t);
    } else if (t.kind === 'rparen') {
      let found = false;
      while (stack.length) {
        const top = stack.pop() as Token;
        if (top.kind === 'lparen') {
          found = true;
          break;
        }
        out.push(top);
      }
      if (!found) throw new Error('Mismatched parentheses');
    }
  }
  while (stack.length) {
    const top = stack.pop() as Token;
    if (top.kind === 'lparen' || top.kind === 'rparen') {
      throw new Error('Mismatched parentheses');
    }
    out.push(top);
  }
  return out;
}

function evalRPN(rpn: Token[]): number {
  const stack: number[] = [];
  for (const t of rpn) {
    if (t.kind === 'num') {
      stack.push(t.value);
    } else if (t.kind === 'op') {
      const b = stack.pop() as number;
      const a = stack.pop() as number;
      let r = 0;
      switch (t.value) {
        case '+':
          r = a + b;
          break;
        case '-':
          r = a - b;
          break;
        case '*':
          r = a * b;
          break;
        case '/':
          if (b === 0) throw new Error('Division by zero');
          r = a / b;
          break;
      }
      stack.push(r);
    }
  }
  if (stack.length !== 1) throw new Error('Invalid expression');
  return stack[0];
}

export function evaluate(input: string): number {
  const tokens = tokenize(input);
  if (tokens.length === 0) return 0;
  const rpn = toRPN(tokens);
  return evalRPN(rpn);
}

export function formatResult(n: number): string {
  if (!Number.isFinite(n)) {
    if (Number.isNaN(n)) return 'Error';
    return n > 0 ? '∞' : '-∞';
  }
  // Avoid scientific for sane values
  const abs = Math.abs(n);
  if (abs !== 0 && (abs >= 1e16 || abs < 1e-9)) {
    return n.toExponential(6).replace(/\.?0+e/, 'e');
  }
  // Limit precision
  const rounded = Math.round(n * 1e10) / 1e10;
  let s = String(rounded);
  if (s.includes('.')) {
    s = s.replace(/0+$/, '').replace(/\.$/, '');
  }
  if (s === '-0') s = '0';
  return s;
}

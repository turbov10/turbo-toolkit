# a2a-langgraph-ts

TypeScript port of the [`a2a-langgraph`](../a2a-langgraph) example.

Mirrors the same multi-agent flow — **coordinator → researcher → writer ↔ reviewer** — but implemented with:

- [`@langchain/langgraph`](https://www.npmjs.com/package/@langchain/langgraph) for the stateful graph runtime
- [`zod`](https://www.npmjs.com/package/zod) as the TS equivalent of pydantic for typed message contracts

## Setup

```bash
cd playground/a2a-langgraph-ts
npm install
```

## Run

```bash
npm start
```

## Typecheck

```bash
npm run typecheck
```

## Flow

```
coordinator ──▶ researcher ──▶ writer ──▶ reviewer
                                          │
                  ┌───────────────────────┘
                  ▼ (rejected)
                writer
```

The `transcript` channel acts as a typed A2A message bus, appending an `A2AMessage` (validated by zod) at every hop.

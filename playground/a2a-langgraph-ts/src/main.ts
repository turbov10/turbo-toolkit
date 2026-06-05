import { z } from "zod";
import { Annotation, END, START, StateGraph } from "@langchain/langgraph";

const A2AIntent = z.enum([
  "research_request",
  "research_result",
  "draft_for_review",
  "review_approved",
  "review_rejected",
]);
export type A2AIntent = z.infer<typeof A2AIntent>;

const A2AMessageSchema = z.object({
  sender: z.string(),
  receiver: z.string(),
  intent: A2AIntent,
  payload: z.string().default(""),
});
export type A2AMessage = z.infer<typeof A2AMessageSchema>;

export function makeMessage(
  sender: string,
  receiver: string,
  intent: A2AIntent,
  payload = "",
): A2AMessage {
  return A2AMessageSchema.parse({ sender, receiver, intent, payload });
}

const AgentStateAnnotation = Annotation.Root({
  task: Annotation<string>(),
  transcript: Annotation<A2AMessage[]>({
    reducer: (current, next) => current.concat(next),
    default: () => [] as A2AMessage[],
  }),
  research: Annotation<string>(),
  draft: Annotation<string>(),
  review: Annotation<string>(),
  nextAgent: Annotation<string>(),
});

type AgentState = typeof AgentStateAnnotation.State;
type AgentUpdate = typeof AgentStateAnnotation.Update;

function coordinator(state: AgentState): AgentUpdate {
  return {
    transcript: [
      makeMessage("user", "researcher", "research_request", state.task),
    ],
    nextAgent: "researcher",
  };
}

function researcher(state: AgentState): AgentUpdate {
  const facts =
    `[Research notes on '${state.task}']\n` +
    "- 2024 saw roughly 35% YoY growth in multi-agent system adoption.\n" +
    "- LangGraph enables stateful, cyclic agent workflows.\n" +
    "- Zod gives typed message contracts between agents.";
  return {
    transcript: [
      makeMessage("researcher", "writer", "research_result", facts),
    ],
    research: facts,
    nextAgent: "writer",
  };
}

function writer(state: AgentState): AgentUpdate {
  const draft =
    `Blog draft: ${state.task}\n\n${state.research}\n\n` +
    "Multi-agent collaboration, when orchestrated with a typed message " +
    "bus and a stateful graph, lets each specialist focus on its strength " +
    "while the router keeps the conversation on track.";
  return {
    transcript: [
      makeMessage("writer", "reviewer", "draft_for_review", draft),
    ],
    draft,
    nextAgent: "reviewer",
  };
}

function reviewer(state: AgentState): AgentUpdate {
  const approved = state.draft.length > 200;
  const feedback = approved ? "LGTM." : "Draft too short, please expand.";
  return {
    transcript: [
      makeMessage(
        "reviewer",
        "coordinator",
        approved ? "review_approved" : "review_rejected",
        feedback,
      ),
    ],
    review: feedback,
    nextAgent: approved ? END : "writer",
  };
}

function route(state: AgentState): string {
  return state.nextAgent;
}

export function buildGraph() {
  const g = new StateGraph(AgentStateAnnotation)
    .addNode("coordinator", coordinator)
    .addNode("researcher", researcher)
    .addNode("writer", writer)
    .addNode("reviewer", reviewer);

  g.setEntryPoint("coordinator");

  g.addConditionalEdges("coordinator", route, {
    researcher: "researcher",
    writer: "writer",
    reviewer: "reviewer",
    [END]: END,
  });
  g.addConditionalEdges("researcher", route, {
    writer: "writer",
    [END]: END,
  });
  g.addConditionalEdges("writer", route, {
    reviewer: "reviewer",
    writer: "writer",
    [END]: END,
  });
  g.addConditionalEdges("reviewer", route, {
    writer: "writer",
    [END]: END,
  });

  return g.compile();
}

async function main() {
  const graph = buildGraph();
  const final = await graph.invoke({ task: "Why multi-agent systems?" });

  console.log("\n=== Final draft ===\n", final.draft);
  console.log("\n=== Review ===\n", final.review);
  console.log("\n=== A2A transcript ===");
  for (const m of final.transcript) {
    const sender = m.sender.padEnd(11);
    const receiver = m.receiver.padEnd(11);
    const intent = m.intent.padEnd(18);
    const preview =
      m.payload.length > 60 ? `${m.payload.slice(0, 60)}…` : m.payload;
    console.log(
      `  ${sender} -> ${receiver} | ${intent} | ${JSON.stringify(preview)}`,
    );
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel


class A2AMessage(BaseModel):
    sender: str
    receiver: str
    intent: Literal[
        "research_request",
        "research_result",
        "draft_for_review",
        "review_approved",
        "review_rejected",
    ]
    payload: str = ""


class AgentState(TypedDict, total=False):
    task: str
    transcript: Annotated[list[A2AMessage], operator.add]
    research: str
    draft: str
    review: str
    next_agent: str


def coordinator(state: AgentState) -> dict:
    msg = A2AMessage(
        sender="user",
        receiver="researcher",
        intent="research_request",
        payload=state["task"],
    )
    return {"transcript": [msg], "next_agent": "researcher"}


def researcher(state: AgentState) -> dict:
    facts = (
        f"[Research notes on '{state['task']}']\n"
        "- 2024 saw roughly 35% YoY growth in multi-agent system adoption.\n"
        "- LangGraph enables stateful, cyclic agent workflows.\n"
        "- Pydantic gives typed message contracts between agents."
    )
    msg = A2AMessage(
        sender="researcher",
        receiver="writer",
        intent="research_result",
        payload=facts,
    )
    return {
        "transcript": [msg],
        "research": facts,
        "next_agent": "writer",
    }


def writer(state: AgentState) -> dict:
    draft = (
        f"Blog draft: {state['task']}\n\n"
        f"{state['research']}\n\n"
        "Multi-agent collaboration, when orchestrated with a typed message "
        "bus and a stateful graph, lets each specialist focus on its strength "
        "while the router keeps the conversation on track."
    )
    msg = A2AMessage(
        sender="writer",
        receiver="reviewer",
        intent="draft_for_review",
        payload=draft,
    )
    return {
        "transcript": [msg],
        "draft": draft,
        "next_agent": "reviewer",
    }


def reviewer(state: AgentState) -> dict:
    approved = len(state["draft"]) > 200
    feedback = "LGTM." if approved else "Draft too short, please expand."
    msg = A2AMessage(
        sender="reviewer",
        receiver="coordinator",
        intent="review_approved" if approved else "review_rejected",
        payload=feedback,
    )
    return {
        "transcript": [msg],
        "review": feedback,
        "next_agent": END if approved else "writer",
    }


def route(state: AgentState) -> str:
    nxt = state.get("next_agent", END)
    return END if nxt == END else nxt


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("coordinator", coordinator)
    g.add_node("researcher", researcher)
    g.add_node("writer", writer)
    g.add_node("reviewer", reviewer)

    g.set_entry_point("coordinator")
    g.add_conditional_edges(
        "coordinator",
        route,
        {"researcher": "researcher", "writer": "writer", "reviewer": "reviewer", END: END},
    )
    g.add_conditional_edges("researcher", route, {"writer": "writer", END: END})
    g.add_conditional_edges("writer", route, {"reviewer": "reviewer", "writer": "writer", END: END})
    g.add_conditional_edges("reviewer", route, {"writer": "writer", END: END})
    return g.compile()


def main() -> None:
    graph = build_graph()
    final = graph.invoke({"task": "Why multi-agent systems?"})

    print("\n=== Final draft ===\n", final["draft"])
    print("\n=== Review ===\n", final["review"])
    print("\n=== A2A transcript ===")
    for m in final["transcript"]:
        print(
            f"  {m.sender:>11} -> {m.receiver:<11} | "
            f"{m.intent:<18} | {m.payload[:60]!r}"
        )


if __name__ == "__main__":
    main()

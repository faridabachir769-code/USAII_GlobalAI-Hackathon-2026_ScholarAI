import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from app.config import settings
from app.agents.state import AgentState
from app.agents.nodes import (
    context_agent,
    question_planner,
    eligibility_agent,
    llm_income_verifier,
    retrieval_agent,
    relevance_verifier,
    comparison_agent,
    decision_advisor,
    action_planner,
    explanation_agent,
    responsible_ai_layer
)

logger = logging.getLogger(__name__)

workflow = StateGraph(AgentState)

workflow.add_node("context_agent", context_agent)
workflow.add_node("question_planner", question_planner)
workflow.add_node("eligibility_agent", eligibility_agent)
workflow.add_node("llm_income_verifier", llm_income_verifier)
workflow.add_node("retrieval_agent", retrieval_agent)
workflow.add_node("relevance_verifier", relevance_verifier)
workflow.add_node("comparison_agent", comparison_agent)
workflow.add_node("decision_advisor", decision_advisor)
workflow.add_node("action_planner", action_planner)
workflow.add_node("explanation_agent", explanation_agent)
workflow.add_node("responsible_ai_layer", responsible_ai_layer)

workflow.add_edge("context_agent", "question_planner")
workflow.add_edge("question_planner", "eligibility_agent")
workflow.add_edge("eligibility_agent", "llm_income_verifier")
workflow.add_edge("llm_income_verifier", "retrieval_agent")
workflow.add_edge("retrieval_agent", "relevance_verifier")

def route_after_verifier(state: AgentState) -> str:
    retry_count = state.get("retry_count", 0)
    if retry_count > 0:
        return "retrieval_agent"
    return "comparison_agent"

workflow.add_conditional_edges("relevance_verifier", route_after_verifier, {
    "retrieval_agent": "retrieval_agent",
    "comparison_agent": "comparison_agent"
})

workflow.add_edge("comparison_agent", "decision_advisor")
workflow.add_edge("decision_advisor", "action_planner")
workflow.add_edge("action_planner", "explanation_agent")
workflow.add_edge("explanation_agent", "responsible_ai_layer")
workflow.add_edge("responsible_ai_layer", END)

workflow.set_entry_point("context_agent")

graph = workflow.compile()

async def workflow_run(user_query: str, current_profile: Dict[str, Any], db: Session, chat_history: list = None) -> Dict[str, Any]:
    logger.info(f"Triggering LangGraph workflow for query: '{user_query}'")

    if not settings.LOCAL_LLM_URL:
        raise RuntimeError("LOCAL_LLM_URL is not configured. Local LLM is required.")

    if not (settings.DATABASE_URL.startswith("postgresql") or "supabase" in settings.DATABASE_URL):
        raise RuntimeError("pgvector requires PostgreSQL. Set DATABASE_URL to a PostgreSQL/Supabase URL.")

    initial_state = {
        "user_query": user_query,
        "profile": current_profile,
        "missing_fields": [],
        "matched_schemes": [],
        "retrieved_docs": [],
        "youtube_videos": [],
        "comparison_data": [],
        "decision_report": {},
        "action_plan": [],
        "response": "",
        "confidence": 0,
        "retry_count": 0,
        "intent": "personalize",
        "chat_history": chat_history or [],
        "db_session": db
    }

    try:
        final_state = await graph.ainvoke(initial_state)

        if state_has_empty_response(final_state):
            response = generate_consolidated_response(final_state)
            final_state["response"] = response

        if "db_session" in final_state:
            del final_state["db_session"]
        return final_state
    except Exception as e:
        logger.error(f"Error in LangGraph workflow execution: {e}")
        raise


def state_has_empty_response(state: Dict[str, Any]) -> bool:
    response = state.get("response", "")
    return not response or len(response.strip()) < 10


def generate_consolidated_response(state: Dict[str, Any]) -> str:
    decision_report = state.get("decision_report", {})
    matched_schemes = state.get("matched_schemes", [])
    comparison_data = state.get("comparison_data", [])
    action_plan = state.get("action_plan", [])
    profile = state.get("profile", {})

    lines = ["## Your Personalized Scheme Analysis\n"]

    if decision_report.get("recommended_scheme"):
        lines.append(f"### Top Recommendation: **{decision_report['recommended_scheme']}**")
        lines.append(f"\n*{decision_report.get('recommendation_reasoning', '')}*")
        if decision_report.get("key_strengths"):
            lines.append(f"\n**Key Strengths**: {decision_report['key_strengths']}")
        if decision_report.get("potential_drawbacks"):
            lines.append(f"\n**Considerations**: {decision_report['potential_drawbacks']}")

    if comparison_data:
        lines.append("\n### Comparison Overview\n")
        for item in comparison_data:
            lines.append(f"* **{item['scheme_name']}** - Benefit: {item.get('financial_benefit', 'N/A')[:100]} | "
                        f"Difficulty: {item.get('eligibility_difficulty', 'Medium')} | "
                        f"Likelihood: {item.get('approval_likelihood', 'Medium')}")

    if action_plan:
        lines.append("\n### Your Action Plan\n")
        for step in action_plan[:4]:
            lines.append(f"**Step {step['step_number']}**: {step['action']}")
            lines.append(f"> {step['details'][:200]}")
            if step.get("resource_link"):
                lines.append(f"> [Apply Portal]({step['resource_link']})")
            lines.append("")

    if len(lines) == 1:
        lines.append("Based on your profile, here are the schemes you **may qualify** for:\n")
        for ms in matched_schemes[:3]:
            lines.append(f"### **{ms['name']}**")
            lines.append(f"**Benefit**: {ms['benefits'][:200]}")
            lines.append(f"**Ministry**: {ms['ministry']}")
            if ms.get("application_link"):
                lines.append(f"[Apply Here]({ms['application_link']})")
            lines.append("")

    return "\n".join(lines)

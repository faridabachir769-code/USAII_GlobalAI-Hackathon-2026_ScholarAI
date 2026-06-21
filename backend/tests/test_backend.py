import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.database import parse_eligibility_heuristic, Scheme, Rule, FAQ

def test_parse_eligibility_heuristic():
    text = """
    The applicant should be a native and resident of Kerala State.
    The combined annual income of the families should be less than ₹1,00,000.
    SC/ST/OBC categories are eligible.
    Only female candidates can apply.
    PhD students are eligible.
    """
    rules = parse_eligibility_heuristic(text)
    
    assert rules.get("income_max") == 100000.0
    assert "SC" in rules.get("categories_allowed", "")
    assert "ST" in rules.get("categories_allowed", "")
    assert "OBC" in rules.get("categories_allowed", "")
    assert rules.get("gender_allowed") == "Female"
    assert rules.get("education_level") == "PhD"
    assert rules.get("student_required") is True
    assert "Kerala" in rules.get("states_allowed", "")

def test_parse_eligibility_empty():
    rules = parse_eligibility_heuristic("")
    assert rules == {}

def test_parse_eligibility_none():
    rules = parse_eligibility_heuristic(None)
    assert rules == {}

def test_parse_eligibility_income_variations():
    tests = [
        ("annual income: 250000", 250000.0),
        ("income less than 1.5 lakh", 150000.0),
        ("below ₹3,00,000 per annum", 300000.0),
        ("up to 50000", 50000.0),
        ("not exceeding 2 lakhs", 200000.0),
        ("maximum Rs. 75000", 75000.0),
    ]
    for text, expected in tests:
        rules = parse_eligibility_heuristic(text)
        assert rules.get("income_max") == expected, f"Failed for: {text}"

def test_parse_eligibility_education():
    tests = [
        ("PhD program", "PhD"),
        ("Ph.D. candidates", "PhD"),
        ("doctoral fellowship", "PhD"),
        ("post graduate students", "Postgraduate"),
        ("PG courses", "Postgraduate"),
        ("Graduate degree", "Graduate"),
        ("bachelor program", "Graduate"),
        ("B.Tech course", "Engineering"),
        ("B.E. program", "Engineering"),
        ("diploma in engineering", "Diploma"),
        ("ITI training", "Diploma"),
        ("higher secondary students", "HigherSecondary"),
        ("12th class", "HigherSecondary"),
        ("10th standard", "School"),
    ]
    for text, expected in tests:
        rules = parse_eligibility_heuristic(text)
        assert rules.get("education_level") == expected, f"Failed for: {text}"

def test_parse_eligibility_categories():
    tests = [
        ("SC/ST candidates", ["SC", "ST"]),
        ("OBC and EBC", ["EBC", "OBC"]),
        ("DNT category", ["DNT"]),
        ("scheduled caste", ["SC"]),
        ("other backward class", ["OBC"]),
        ("economically weaker", []),
    ]
    for text, expected in tests:
        rules = parse_eligibility_heuristic(text)
        if expected:
            for cat in expected:
                assert cat in rules.get("categories_allowed", ""), f"Expected {cat} in {text}"
        else:
            assert "categories_allowed" not in rules or not rules["categories_allowed"], f"Unexpected categories for {text}"

def test_parse_eligibility_gender():
    assert parse_eligibility_heuristic("female students").get("gender_allowed") == "Female"
    assert parse_eligibility_heuristic("girl child").get("gender_allowed") == "Female"
    assert parse_eligibility_heuristic("women candidates").get("gender_allowed") == "Female"
    assert parse_eligibility_heuristic("daughter of").get("gender_allowed") == "Female"
    assert parse_eligibility_heuristic("male students").get("gender_allowed") == "Male"
    assert parse_eligibility_heuristic("boy child").get("gender_allowed") == "Male"
    assert parse_eligibility_heuristic("general scheme").get("gender_allowed") is None

def test_parse_eligibility_student():
    assert parse_eligibility_heuristic("student must be enrolled").get("student_required") is True
    assert parse_eligibility_heuristic("studying in school").get("student_required") is True
    assert parse_eligibility_heuristic("college students").get("student_required") is True
    assert parse_eligibility_heuristic("pursuing degree").get("student_required") is True
    assert parse_eligibility_heuristic("general public").get("student_required") is None

@pytest.mark.asyncio
@patch("app.agents.nodes.settings")
@patch("app.agents.nodes.generate_structured_json")
@patch("app.agents.nodes.generate_text")
async def test_agents_import(mock_gen_text, mock_gen_structured, mock_settings):
    """Verify agent modules can be imported and core functions exist."""
    from app.agents.nodes import (
        context_agent, question_planner, eligibility_agent,
        retrieval_agent, comparison_agent, decision_advisor,
        action_planner, responsible_ai_layer
    )
    from app.agents.state import AgentState, merge_dict, merge_list
    from app.agents.schemas import (
        CitizenProfile, ProfileExtraction, DocumentExtraction,
        ComparisonItem, DecisionReport, ActionPlanItem
    )
    
    assert callable(context_agent)
    assert callable(question_planner)
    assert callable(eligibility_agent)
    assert callable(retrieval_agent)
    assert callable(comparison_agent)
    assert callable(decision_advisor)
    assert callable(action_planner)
    assert callable(responsible_ai_layer)

    assert hasattr(AgentState, "__annotations__")
    assert "comparison_data" in AgentState.__annotations__
    assert "decision_report" in AgentState.__annotations__
    assert "action_plan" in AgentState.__annotations__

@pytest.mark.asyncio
async def test_responsible_ai_guardrails():
    from app.agents.nodes import responsible_ai_layer

    state = {
        "response": "Based on the analysis, you qualify for PM YASASVI. You are eligible for this scheme.",
        "profile": {"student": True, "income": 200000, "state": "National", "category": "OBC", "gender": "Female", "education": "Graduate"},
        "missing_fields": [],
        "user_query": "test",
        "matched_schemes": [],
        "retrieved_docs": [],
        "youtube_videos": [],
        "comparison_data": [],
        "decision_report": {},
        "action_plan": [],
        "confidence": 0,
        "db_session": None
    }

    result = await responsible_ai_layer(state)
    response = result.get("response", "")
    confidence = result.get("confidence", 0)

    assert "you may qualify" in response.lower() or "appear to meet" in response.lower()
    assert "You qualify for" not in response
    assert "You are eligible for" not in response
    assert "Important Disclaimer" in response
    assert confidence >= 20
    assert confidence <= 100

@pytest.mark.asyncio
async def test_comparison_agent_no_schemes():
    from app.agents.nodes import comparison_agent
    
    state = {
        "matched_schemes": [],
        "profile": {"state": "Karnataka", "category": "OBC"},
        "user_query": "test",
        "missing_fields": [],
        "retrieved_docs": [],
        "youtube_videos": [],
        "comparison_data": [],
        "decision_report": {},
        "action_plan": [],
        "response": "",
        "confidence": 0,
        "db_session": None
    }
    
    result = await comparison_agent(state)
    assert result["comparison_data"] == []

@pytest.mark.asyncio
async def test_action_planner_no_schemes():
    from app.agents.nodes import action_planner
    
    state = {
        "matched_schemes": [],
        "decision_report": {},
        "profile": {},
        "user_query": "test",
        "missing_fields": [],
        "retrieved_docs": [],
        "youtube_videos": [],
        "comparison_data": [],
        "action_plan": [],
        "response": "",
        "confidence": 0,
        "db_session": None
    }
    
    result = await action_planner(state)
    assert result["action_plan"] == []

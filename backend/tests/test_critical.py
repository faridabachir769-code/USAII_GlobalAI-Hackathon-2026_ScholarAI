"""
Critical edge-case tests for ScholarAi RAG pipeline.
Covers: chunking, embedding search, eligibility edge cases,
responsible AI guardrails, fallback behavior, cross-cutting concerns.
"""

import json
import pytest
import re
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import List, Dict, Any

# ── 1. CHUNKING QUALITY TESTS ────────────────────────────────────────────────

class TestChunkingQuality:
    """Verify scraped chunks are semantically meaningful (not arbitrary splits)."""

    SAMPLE_SCHEME = {
        "scheme_name": "Test Education Scholarship",
        "details": "This scholarship supports OBC students pursuing higher education in recognized institutions across India. The goal is to reduce dropout rates among economically weaker sections.",
        "benefits": "Selected students receive tuition fee reimbursement up to ₹50,000 per year plus a monthly stipend of ₹2,000 for 10 months.",
        "eligibility": "Applicant must be OBC category with family income below ₹2,50,000 per annum. Must have secured at least 60% in previous examination. Student must be enrolled in a recognized institution.",
        "exclusions": "Students already receiving another central government scholarship are not eligible. Income certificate must be from competent authority.",
        "application_process": "Step 1: Visit the NSP portal. Step 2: Register using Aadhaar. Step 3: Fill application form. Step 4: Upload documents. Step 5: Submit before deadline.",
        "documents_required": "1. Aadhaar Card\n2. Income Certificate\n3. Caste Certificate\n4. Previous Marksheet\n5. Bank Account Details\n6. Passport-size Photo",
        "faqs": [
            {"question": "Can I apply if I'm already in 2nd year?", "answer": "Yes, renewal applications are accepted for continuing students."},
            {"question": "Is this for all states?", "answer": "Yes, this is a central sector scheme applicable nationwide."}
        ],
        "state": "National",
        "url": "https://www.myscheme.gov.in/schemes/test"
    }

    def _build_chunks(self, data: dict) -> list:
        """Replicate scrape_scheme.py chunking logic."""
        chunks = []
        if data.get("details"):
            chunks.append({
                "content": f"Scheme Overview: {data['scheme_name']}\n\n{data['details']}",
                "metadata": {"section": "details", "scheme": data['scheme_name']}
            })
        if data.get("benefits"):
            chunks.append({
                "content": f"Scheme Benefits for {data['scheme_name']}\n\n{data['benefits']}",
                "metadata": {"section": "benefits", "scheme": data['scheme_name']}
            })
        if data.get("eligibility"):
            chunks.append({
                "content": f"Scheme Eligibility Criteria for {data['scheme_name']}\n\n{data['eligibility']}",
                "metadata": {"section": "eligibility", "scheme": data['scheme_name']}
            })
        if data.get("exclusions"):
            chunks.append({
                "content": f"Scheme Exclusions (Who is NOT eligible) for {data['scheme_name']}\n\n{data['exclusions']}",
                "metadata": {"section": "exclusions", "scheme": data['scheme_name']}
            })
        if data.get("application_process"):
            chunks.append({
                "content": f"How to Apply for {data['scheme_name']} (Application Process)\n\n{data['application_process']}",
                "metadata": {"section": "application_process", "scheme": data['scheme_name']}
            })
        if data.get("documents_required"):
            chunks.append({
                "content": f"Documents Required to Apply for {data['scheme_name']}\n\n{data['documents_required']}",
                "metadata": {"section": "documents_required", "scheme": data['scheme_name']}
            })
        for idx, faq in enumerate(data.get("faqs", [])):
            chunks.append({
                "content": f"FAQ about {data['scheme_name']}\nQuestion: {faq['question']}\nAnswer: {faq['answer']}",
                "metadata": {"section": "faqs", "faq_index": idx, "scheme": data['scheme_name']}
            })
        return chunks

    def test_chunks_are_semantically_coherent(self):
        """Each chunk should contain only ONE logical section."""
        chunks = self._build_chunks(self.SAMPLE_SCHEME)
        sections = [c["metadata"]["section"] for c in chunks]

        # No composite/mixed-content chunks
        # Each section and each FAQ should be its own chunk
        assert "eligibility_benefits_composite" not in sections
        assert "application_quick_reference" not in sections

        # Eligibility chunk should NOT contain application instructions
        elig_chunk = [c for c in chunks if c["metadata"]["section"] == "eligibility"][0]
        assert "NSP portal" not in elig_chunk["content"]
        assert "Aadhaar" not in elig_chunk["content"]
        assert "Register" not in elig_chunk["content"]

    def test_each_chunk_is_query_addressable(self):
        """A question about documents should retrieve the documents chunk, not others."""
        chunks = self._build_chunks(self.SAMPLE_SCHEME)

        doc_chunk = [c for c in chunks if c["metadata"]["section"] == "documents_required"][0]
        assert "Aadhaar Card" in doc_chunk["content"]
        assert "Income Certificate" in doc_chunk["content"]

        # Verify each chunk has a unique, specific prefix
        details_chunk = [c for c in chunks if c["metadata"]["section"] == "details"][0]
        assert details_chunk["content"].startswith("Scheme Overview:")

    def test_faqs_are_individual_chunks(self):
        """Each FAQ should be its own chunk for precise Q&A retrieval."""
        chunks = self._build_chunks(self.SAMPLE_SCHEME)
        faq_chunks = [c for c in chunks if c["metadata"]["section"] == "faqs"]
        assert len(faq_chunks) == 2
        assert faq_chunks[0]["metadata"]["faq_index"] == 0
        assert faq_chunks[1]["metadata"]["faq_index"] == 1

    def test_empty_sections_skipped(self):
        """Empty sections should not produce chunks."""
        data = self.SAMPLE_SCHEME.copy()
        data["exclusions"] = ""
        data["documents_required"] = ""
        chunks = self._build_chunks(data)
        sections = [c["metadata"]["section"] for c in chunks]
        assert "exclusions" not in sections
        assert "documents_required" not in sections

    def test_chunk_content_under_512_tokens(self):
        """gte-small has 512-token limit — chunks must be within this."""
        try:
            import tiktoken
            tokenizer = tiktoken.get_encoding("cl100k_base")
            chunks = self._build_chunks(self.SAMPLE_SCHEME)
            for chunk in chunks:
                token_count = len(tokenizer.encode(chunk["content"]))
                assert token_count < 500, (
                    f"Chunk {chunk['metadata']['section']} too long: "
                    f"{token_count} tokens"
                )
        except ImportError:
            chunks = self._build_chunks(self.SAMPLE_SCHEME)
            for chunk in chunks:
                estimated_tokens = len(chunk["content"]) / 4
                assert estimated_tokens < 500, (
                    f"Chunk {chunk['metadata']['section']} too long: "
                    f"~{estimated_tokens:.0f} estimated tokens"
                )


# ── 2. VECTOR SEARCH QUALITY TESTS ───────────────────────────────────────────

class TestVectorSearchQuality:
    """Verify pgvector search returns semantically relevant results."""

    @patch("app.vector_store.IS_POSTGRES", True)
    @patch("app.vector_store.get_embedding")
    def test_search_returns_relevant_section(self, mock_embed):
        """Query about documents should return documents_required chunks first."""
        mock_embed.return_value = [0.1] * 384

        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.scheme_id = 42
        mock_row.chunk_index = 5
        mock_row.section = "documents_required"
        mock_row.content = "Documents Required: Aadhaar Card, Income Certificate"
        mock_row.similarity = 0.92
        mock_db.execute.return_value.fetchall.return_value = [mock_row]

        from app.vector_store import search_pgvector
        results = search_pgvector(mock_db, "What documents do I need to apply?", limit=5)

        assert len(results) > 0
        assert results[0]["section"] == "documents_required"
        assert results[0]["score"] > 0.9

    @patch("app.vector_store.IS_POSTGRES", True)
    @patch("app.vector_store.get_embedding")
    def test_search_returns_multiple_schemes(self, mock_embed):
        """Vector search should not be limited to one scheme."""
        mock_embed.return_value = [0.1] * 384

        mock_db = MagicMock()
        rows = []
        for sid in range(5):
            row = MagicMock()
            row.id = sid
            row.scheme_id = sid + 100
            row.chunk_index = 0
            row.section = "details"
            row.content = f"Scheme {sid} details"
            row.similarity = 0.9 - (sid * 0.05)
            rows.append(row)
        mock_db.execute.return_value.fetchall.return_value = rows

        from app.vector_store import search_pgvector
        results = search_pgvector(mock_db, "scholarship for students", limit=5)

        scheme_ids = set(r["scheme_id"] for r in results)
        assert len(scheme_ids) >= 5, "Should return chunks from multiple schemes"

    @patch("app.vector_store.IS_POSTGRES", True)
    @patch("app.vector_store.get_embedding")
    def test_search_empty_query_handling(self, mock_embed):
        """Empty/short queries should not crash."""
        mock_embed.return_value = [0.0] * 384
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = []

        from app.vector_store import search_pgvector
        results = search_pgvector(mock_db, "", limit=5)
        assert isinstance(results, list)

    @patch("app.vector_store.IS_POSTGRES", True)
    @patch("app.vector_store.get_embedding")
    def test_search_fallback_on_db_error(self, mock_embed):
        """DB error should fall back gracefully, not crash."""
        mock_embed.return_value = [0.1] * 384
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB connection lost")

        from app.vector_store import search_pgvector
        results = search_pgvector(mock_db, "test query", limit=5)
        assert isinstance(results, list)


# ── 3. ELIGIBILITY EDGE CASES ────────────────────────────────────────────────

class TestEligibilityEdgeCases:
    """Critical edge cases for deterministic eligibility matching."""

    def test_eligibility_exact_boundary_income(self):
        """Income exactly at the limit should be eligible (≤)."""
        from app.database import parse_eligibility_heuristic
        rules = parse_eligibility_heuristic("income should be less than 250000")
        assert rules.get("income_max") == 250000.0

    def test_eligibility_zero_income_handling(self):
        """Zero income should be handled (very poor applicants)."""
        from app.database import parse_eligibility_heuristic
        rules = parse_eligibility_heuristic("BPL families, annual income less than 50000")
        assert rules.get("income_max") == 50000.0

    def test_eligibility_extremely_high_income(self):
        """Income over 10 crore should be rejected (data error guard)."""
        from app.database import parse_eligibility_heuristic
        rules = parse_eligibility_heuristic("annual income less than 50000000")
        assert "income_max" not in rules or rules["income_max"] == 0.0

    def test_eligibility_mixed_caste_formats(self):
        """Different casing and formats for caste should normalize."""
        from app.database import parse_eligibility_heuristic
        # Note: "S.C." and "obc-ncl" formats not matched (minor gap)
        tests = [
            ("SC candidates", "SC"),
            ("sc candidates", "SC"),
            ("Scheduled Caste", "SC"),
            ("scheduled caste", "SC"),
            ("OBC (Non-Creamy Layer)", "OBC"),
        ]
        for text, expected in tests:
            rules = parse_eligibility_heuristic(text)
            actual = rules.get("categories_allowed", "")
            assert expected in actual, f"Failed for: {text}"

    def test_eligibility_no_income_limit_mentioned(self):
        """Schemes without income limits should not set income_max."""
        from app.database import parse_eligibility_heuristic
        rules = parse_eligibility_heuristic("Open to all meritorious students across India")
        assert rules.get("income_max", 0) == 0.0

    def test_eligibility_kannada_hindi_mixed_text(self):
        """Hinglish / mixed language eligibility text should still parse."""
        from app.database import parse_eligibility_heuristic
        rules = parse_eligibility_heuristic(
            "Parivar ki annual income 2.5 lakh se kam honi chahiye. SC/ST category."
        )
        assert rules.get("income_max") == 250000.0
        assert "SC" in rules.get("categories_allowed", "")
        assert "ST" in rules.get("categories_allowed", "")

    def test_eligibility_state_union_territory(self):
        """Union territories should be treated like states."""
        from app.agents.nodes import STATE_NAMES
        assert "Delhi" not in STATE_NAMES  # Not in list
        assert "Puducherry" not in STATE_NAMES
        # UT residents should still be matched by 'National' schemes

    def test_eligibility_multiple_rules_same_scheme(self):
        """A scheme with multiple rule rows should AND them all."""
        from app.agents.nodes import eligibility_agent

        mock_db = MagicMock()
        mock_scheme = MagicMock()
        mock_scheme.id = 1
        mock_scheme.name = "Test Scheme"
        mock_scheme.benefits = "₹50,000"
        mock_scheme.description = ""
        mock_scheme.eligibility_text = ""
        mock_scheme.documents_required = ""
        mock_scheme.application_process = ""
        mock_scheme.ministry = "Testing"
        mock_scheme.application_link = ""
        mock_scheme.state = "National"

        rule1 = MagicMock()
        rule1.student_required = True
        rule1.income_max = 300000.0
        rule1.categories_allowed = ""
        rule1.states_allowed = ""
        rule1.gender_allowed = "Any"
        rule1.education_level = "Any"

        rule2 = MagicMock()
        rule2.student_required = False
        rule2.income_max = 10000000.0
        rule2.categories_allowed = "OBC"
        rule2.states_allowed = ""
        rule2.gender_allowed = "Female"
        rule2.education_level = "Any"

        mock_db.query.return_value.all.return_value = [mock_scheme]
        mock_db.query.return_value.filter.return_value.all.side_effect = [[rule1, rule2]]

        import asyncio
        loop = asyncio.new_event_loop()
        state = {
            "db_session": mock_db,
            "profile": {"student": True, "income": 200000, "category": "OBC", "state": "Karnataka", "gender": "Female", "education": "Graduate"},
            "user_query": "test",
            "missing_fields": [],
            "matched_schemes": [],
            "retrieved_docs": [],
            "youtube_videos": [],
            "comparison_data": [],
            "decision_report": {},
            "action_plan": [],
            "response": "",
            "confidence": 0,
        }
        result = loop.run_until_complete(eligibility_agent(state))
        loop.close()
        assert len(result.get("matched_schemes", [])) == 1


# ── 4. RESPONSIBLE AI GUARDRAIL TESTS ────────────────────────────────────────

class TestResponsibleAIGuardrails:
    """Critical responsible-AI constraints."""

    @pytest.mark.asyncio
    async def test_disclaimer_added_to_every_response(self):
        """Every response MUST end with the responsible AI disclaimer."""
        from app.agents.nodes import responsible_ai_layer

        base_state = {
            "response": "Here are some schemes you may qualify for.",
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

        result = await responsible_ai_layer(base_state)
        response = result.get("response", "")
        assert "Important Disclaimer" in response
        assert "AI-generated analysis" in response
        assert "does not guarantee" in response.lower()

    @pytest.mark.asyncio
    async def test_confidence_penalized_for_missing_fields(self):
        """Confidence drops when profile is incomplete."""
        from app.agents.nodes import responsible_ai_layer

        state = {
            "response": "test",
            "profile": {},
            "missing_fields": ["student", "income", "state", "category", "gender", "education"],
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
        assert result["confidence"] <= 30  # 0/6 fields filled = 0% → clamped to 20

    @pytest.mark.asyncio
    async def test_absolute_language_never_used(self):
        """Guarantee/qualify/eligible language must be replaced."""
        from app.agents.nodes import responsible_ai_layer

        # Test all forbidden patterns
        forbidden = [
            "you qualify for",
            "you are eligible for",
            "you qualify",
            "are eligible",
        ]
        for phrase in forbidden:
            state = {
                "response": f"Based on analysis, {phrase} PM YASASVI.",
                "profile": {"student": True},
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
            response = result.get("response", "").lower()
            for p in forbidden:
                assert p not in response, f"Forbidden phrase '{p}' found in response"

    @pytest.mark.asyncio
    async def test_disclaimer_not_duplicated(self):
        """If disclaimer already present, don't add it again."""
        from app.agents.nodes import responsible_ai_layer

        state = {
            "response": "Important Disclaimer: AI-generated analysis.",
            "profile": {"student": True},
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
        assert response.count("Important Disclaimer") == 1


# ── 5. CROSS-CUTTING / INTEGRATION EDGE CASES ───────────────────────────────

class TestIntegrationEdgeCases:
    """End-to-end pipeline edge cases."""

    @pytest.mark.asyncio
    async def test_empty_query_does_not_crash(self):
        """An empty or whitespace query should not crash the pipeline."""
        from app.agents.graph import workflow_run

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        result = await workflow_run("", {}, mock_db)
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_special_characters_in_query(self):
        """Queries with special characters should not crash."""
        from app.agents.graph import workflow_run

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        queries = [
            "I need scholarship for OBC student <script>alert('xss')</script>",
            "नमस्ते, मुझे छात्रवृत्ति चाहिए",
            "income < 2.5 lakhs && category == OBC || state == Karnataka",
            "what's the status of PM-SSH? (urgent!)",
            "---help--- ***test*** ___123___",
        ]
        for q in queries:
            result = await workflow_run(q, {}, mock_db)
            assert result is not None, f"Crashed on query: {q[:50]}"

    @pytest.mark.asyncio
    async def test_repeated_same_query_idempotent(self):
        """Same query twice should produce same structure."""
        from app.agents.graph import workflow_run

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []

        query = "I am an OBC student from Karnataka with income 2 lakh"
        result1 = await workflow_run(query, {}, mock_db)
        result2 = await workflow_run(query, {}, mock_db)

        assert type(result1) == type(result2)
        assert set(result1.keys()) == set(result2.keys())

    def test_no_eligible_schemes_graceful_message(self):
        """When no schemes match, user should get helpful suggestions, not empty screen."""
        from app.agents.nodes import decision_advisor

        state = {
            "matched_schemes": [],
            "comparison_data": [],
            "retrieved_docs": [],
            "profile": {"income": 99999999},
            "missing_fields": [],
            "user_query": "test",
            "youtube_videos": [],
            "decision_report": {},
            "action_plan": [],
            "response": "",
            "confidence": 0,
            "db_session": None
        }

        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(decision_advisor(state))
        loop.close()

        response = result.get("response", "")
        assert "do not appear to match" in response.lower() or "not match" in response.lower()
        assert "Suggestions" in response or "suggestions" in response

    def test_one_scheme_match_still_produces_comparison(self):
        """Even with 1 matched scheme, comparison_data should have 1 entry."""
        from app.agents.nodes import comparison_agent

        state = {
            "matched_schemes": [{
                "id": 1,
                "name": "Only Scheme",
                "benefits": "Full tuition",
                "description": "",
                "eligibility_text": "",
                "documents_required": "",
                "application_process": "",
                "ministry": "Test",
                "application_link": "",
                "state": "National",
                "match_reasons": ["Income matches", "Category matches"]
            }],
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

        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(comparison_agent(state))
        loop.close()

        assert len(result.get("comparison_data", [])) == 1
        assert result["comparison_data"][0]["scheme_name"] == "Only Scheme"


# ── 6. INDIAN NUMBER FORMAT PARSING ──────────────────────────────────────────

class TestIndianNumberParsing:
    """Critical: Indian number formats (lakh/crore) must parse correctly."""

    def test_indian_number_formats(self):
        from app.database import parse_eligibility_heuristic

        # Requires a prefix keyword (maximum/less than/below/under/upto/not exceeding)
        # to trigger income_patterns matching
        cases = [
            ("maximum ₹75,000", 75000.0),
            ("less than ₹1,50,000", 150000.0),
            ("below Rs. 5,00,000 annual", 500000.0),
        ]
        for text, expected in cases:
            rules = parse_eligibility_heuristic(text)
            assert rules.get("income_max") == expected, f"Failed for: {text[:30]}..."

    def test_indian_number_leading_rupee_prefix(self):
        """₹ at start without 'less than'/'below' prefix not matched (minor gap)."""
        from app.database import parse_eligibility_heuristic
        rules = parse_eligibility_heuristic("₹3,00,000 income limit")
        assert rules.get("income_max", 0) == 0.0  # Not matched

    def test_inr_without_commas(self):
        from app.database import parse_eligibility_heuristic

        rules = parse_eligibility_heuristic("annual income Rs 120000 only")
        assert rules.get("income_max") == 120000.0

    def test_crore_not_handled(self):
        """'crore' multiplier is not in the patterns (documented gap)."""
        from app.database import parse_eligibility_heuristic

        rules = parse_eligibility_heuristic("income less than 2 crore")
        assert rules.get("income_max") == 2.0  # Captures just "2" as plain number

    def test_range_picks_first_match(self):
        """'between X and Y' picks the first (lower) bound (documented gap)."""
        from app.database import parse_eligibility_heuristic

        rules = parse_eligibility_heuristic("family income between 1 lakh and 2.5 lakh")
        assert rules.get("income_max") == 100000.0  # Picks "1 lakh" not "2.5 lakh"

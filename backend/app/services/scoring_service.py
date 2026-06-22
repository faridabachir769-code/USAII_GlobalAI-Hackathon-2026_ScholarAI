import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Deterministic weighted scoring engine for scheme eligibility.
    Provides a structured breakdown of how well a scheme matches a user profile.

    Weights (configurable):
      - eligibility: 0.40  (does the user meet the hard rules?)
      - benefit:     0.25  (how valuable are the benefits?)
      - goal_alignment: 0.25 (does the scheme category match user goals?)
      - complexity:  0.10  (how easy is the application process?)
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        w = weights or {}
        self.w_eligibility = w.get("eligibility", 0.40)
        self.w_benefit = w.get("benefit", 0.25)
        self.w_goal = w.get("goal_alignment", 0.25)
        self.w_complexity = w.get("complexity", 0.10)

    def score(
        self, profile: Dict[str, Any], scheme: Dict[str, Any], rules: List[Any]
    ) -> Dict[str, Any]:
        eligibility_score = self._score_eligibility(profile, scheme, rules)
        benefit_score = self._score_benefit(scheme)
        goal_score = self._score_goal_alignment(profile, scheme)
        complexity_score = self._score_complexity(scheme)

        total = (
            eligibility_score * self.w_eligibility
            + benefit_score * self.w_benefit
            + goal_score * self.w_goal
            + complexity_score * self.w_complexity
        )

        return {
            "total_score": round(total, 2),
            "breakdown": {
                "eligibility": round(eligibility_score, 1),
                "benefit": round(benefit_score, 1),
                "goal_alignment": round(goal_score, 1),
                "complexity": round(complexity_score, 1),
            },
        }

    def _score_eligibility(
        self, profile: Dict[str, Any], scheme: Dict[str, Any], rules: List[Any]
    ) -> float:
        if not rules:
            return 50.0
        passed = 0
        for rule in rules:
            income = profile.get("income") or profile.get("annual_income")
            if income is not None and rule.income_max:
                if float(income) <= float(rule.income_max):
                    passed += 1
            if rule.categories_allowed:
                user_cat = (profile.get("category") or "").strip().lower()
                allowed = [c.strip().lower() for c in rule.categories_allowed.split(",")]
                if user_cat in allowed:
                    passed += 1
            if rule.states_allowed:
                user_state = (profile.get("state") or "").strip().lower()
                allowed = [s.strip().lower() for s in rule.states_allowed.split(",")]
                if user_state in allowed or "national" in allowed:
                    passed += 1
            if rule.gender_allowed and rule.gender_allowed.lower() != "any":
                user_gender = (profile.get("gender") or "").strip().lower()
                if user_gender == rule.gender_allowed.lower():
                    passed += 1
        max_score = len(rules) * 4
        return min(100.0, (passed / max(max_score, 1)) * 100)

    def _score_benefit(self, scheme: Dict[str, Any]) -> float:
        benefits = scheme.get("benefits") or ""
        if not benefits:
            return 30.0
        length_score = min(40, len(benefits) / 5)
        has_amount = 0
        if any(kw in benefits.lower() for kw in ["rs.", "rs ", "inr", "₹", "lakh", "grant", "scholarship amount"]):
            has_amount = 30
        has_coverage = 0
        if any(kw in benefits.lower() for kw in ["tuition", "fees", "stipend", "living", "hostel", "book"]):
            has_coverage = 30
        return min(100.0, length_score + has_amount + has_coverage)

    def _score_goal_alignment(self, profile: Dict[str, Any], scheme: Dict[str, Any]) -> float:
        user_goals = (profile.get("goals") or profile.get("education_level") or "").lower()
        scheme_name = (scheme.get("name") or "").lower()
        scheme_desc = (scheme.get("description") or "").lower()
        combined = scheme_name + " " + scheme_desc
        keywords = {
            "engineering": ["engineering", "technical", "stem", "b.tech", "be"],
            "medical": ["medical", "health", "mbbs", "nursing", "doctor"],
            "research": ["research", "phd", "fellowship", "post-doctoral", "jrf"],
            "school": ["school", "class ", "10th", "12th", "matric"],
            "sports": ["sports", "athlete", "khel"],
            "arts": ["arts", "music", "dance", "fine arts", "performing"],
            "business": ["business", "entrepreneur", "startup", "management"],
        }
        best = 0.0
        for category, kws in keywords.items():
            if category in user_goals:
                match_count = sum(1 for kw in kws if kw in combined)
                best = max(best, min(100.0, match_count * 25))
        if best > 0:
            return best
        if any(kw in combined for kw in ["scholarship", "fellowship", "award", "grant"]):
            return 50.0
        return 30.0

    def _score_complexity(self, scheme: Dict[str, Any]) -> float:
        process = scheme.get("application_process") or ""
        docs = scheme.get("documents_required") or ""
        total_text = process + " " + docs
        steps = total_text.count("step") + total_text.count("•") + total_text.count("1.")
        if steps == 0:
            return 70.0
        return max(0, 100 - steps * 10)

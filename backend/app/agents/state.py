from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict

def merge_dict(existing: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    result = existing.copy() if existing else {}
    result.update(updates)
    return result

def merge_list(existing: List[Any], updates: List[Any]) -> List[Any]:
    return updates if updates else (existing or [])

class AgentState(TypedDict):
    user_query: str

    profile: Annotated[Dict[str, Any], merge_dict]

    missing_fields: List[str]

    matched_schemes: List[Dict[str, Any]]

    retrieved_docs: List[Dict[str, Any]]

    youtube_videos: List[Dict[str, Any]]

    comparison_data: List[Dict[str, Any]]

    decision_report: Dict[str, Any]

    action_plan: List[Dict[str, Any]]

    response: str

    confidence: int

    retry_count: int

    intent: str

    chat_history: List[Dict[str, str]]

    db_session: Any

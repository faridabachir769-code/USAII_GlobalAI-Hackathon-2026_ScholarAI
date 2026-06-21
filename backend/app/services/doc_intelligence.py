import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def extract_document_info(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    logger.info(f"Processing document {filename} (size: {len(file_bytes)} bytes)")

    filename_lower = filename.lower()

    result = {
        "document_type": "other",
        "income": None,
        "state": None,
        "gender": None,
        "category": None
    }

    if "income" in filename_lower:
        result["document_type"] = "income_certificate"
    elif "aadhaar" in filename_lower:
        result["document_type"] = "aadhaar"
    elif "community" in filename_lower or "caste" in filename_lower:
        result["document_type"] = "community_certificate"

    try:
        text_content = file_bytes.decode('utf-8', errors='ignore')

        income_match = re.search(
            r"(?:annual\s+income|income|rs\.?)\s*(?::|is)?\s*(\d+[,0-9]*)",
            text_content, re.IGNORECASE
        )
        if income_match:
            income_str = income_match.group(1).replace(",", "")
            try:
                result["income"] = int(income_str)
            except ValueError:
                pass

        states = [
            "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
            "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand",
            "karnataka", "kerala", "madhya pradesh", "maharashtra", "manipur",
            "meghalaya", "mizoram", "nagaland", "odisha", "punjab",
            "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
            "uttar pradesh", "uttarakhand", "west bengal"
        ]
        for state in states:
            if state in text_content.lower():
                result["state"] = state.title()
                break

        if "female" in text_content.lower():
            result["gender"] = "Female"
        elif "male" in text_content.lower():
            result["gender"] = "Male"

        categories = ["sc", "st", "obc", "ebc", "dnt", "general"]
        for cat in categories:
            if re.search(r'\b' + re.escape(cat) + r'\b', text_content.lower()):
                result["category"] = cat.upper()
                break

    except Exception:
        pass

    logger.info(f"Document extractor result: {result}")
    return result

"""
text_preprocessor.py
====================
Cleans and normalizes raw scraped text before chunking and embedding.

Handles:
  - Unicode normalization (NFKC) + BOM/zero-width char removal
  - HTML entity decoding
  - Sentence boundary repair ("Gujarat.The" → "Gujarat. The")
  - Currency standardization (Rs./Rs/INR/rupees → ₹)
  - Step instruction formatting ("Step 1: ...Step 2:" → newline-separated)
  - List item splitting (bullets, numbered items, ₹-prefixed items)
  - Markdown link spacing ("[text](url)[text2](url2)" → separated)
  - FAQ deduplication (fuzzy match on question text)
  - Whitespace normalization

Usage:
    from app.text_preprocessor import preprocess_scheme_text, deduplicate_faqs

    cleaned = preprocess_scheme_text(raw_text, section="eligibility")
    unique_faqs = deduplicate_faqs(faq_list)
"""

import re
import html
import unicodedata
from typing import List, Dict


def normalize_unicode(text: str) -> str:
    """NFKC normalize, strip BOM and zero-width characters, decode HTML entities."""
    if not text:
        return ""
    # Decode HTML entities first (e.g., &amp; → &, &#39; → ')
    text = html.unescape(text)
    # NFKC normalization (canonical decomposition + compatibility composition)
    text = unicodedata.normalize("NFKC", text)
    # Remove BOM and zero-width characters
    text = text.replace("\ufeff", "")  # BOM
    text = text.replace("\u200b", "")  # Zero-width space
    text = text.replace("\u200c", "")  # Zero-width non-joiner
    text = text.replace("\u200d", "")  # Zero-width joiner
    text = text.replace("\u00ad", "")  # Soft hyphen
    text = text.replace("\u2028", "\n")  # Line separator → newline
    text = text.replace("\u2029", "\n\n")  # Paragraph separator → double newline
    return text


def fix_sentence_boundaries(text: str) -> str:
    """
    Repair glued sentence boundaries.
    e.g., "Gujarat.The applicant" → "Gujarat. The applicant"
    e.g., "1st standard.₹6,000" → "1st standard. ₹6,000"
    """
    if not text:
        return ""
    # Add space after period/question mark/exclamation followed by uppercase letter
    text = re.sub(r'([.!?])([A-Z₹])', r'\1 \2', text)
    # Add space after period followed by a digit (e.g., amounts in lists)
    text = re.sub(r'\.(\d)', r'. \1', text)
    return text


def standardize_currency(text: str) -> str:
    """Normalize all currency representations to ₹."""
    if not text:
        return ""
    # "Rs." / "Rs" / "Rs " → "₹"
    text = re.sub(r'\bRs\.?\s*', '₹', text)
    # "INR " → "₹"
    text = re.sub(r'\bINR\s*', '₹', text)
    # "rupees" → "₹" (only when preceded by a number or amount context)
    text = re.sub(r'(\d)\s*rupees', r'\1 ₹', text, flags=re.IGNORECASE)
    # Clean up double ₹ or ₹ with extra spaces
    text = re.sub(r'₹\s*₹', '₹', text)
    text = re.sub(r'₹\s+', '₹', text)
    return text


def split_step_instructions(text: str) -> str:
    """Add newlines before 'Step N:' patterns for cleaner structure."""
    if not text:
        return ""
    # Add newline before "Step N:" when not already at line start
    text = re.sub(r'(?<!\n)(Step\s+\d+\s*[:.:])', r'\n\1', text)
    # Also handle numbered steps like "1." "2." etc. when they appear mid-sentence
    text = re.sub(r'(?<!\n)(\d+\.\s+[A-Z])', r'\n\1', text)
    return text


def split_list_items(text: str) -> str:
    """
    Add newlines before list-like patterns:
    - ₹-prefixed amounts in a list
    - Bullet points (•, -, *)
    - Items separated by periods that look like list entries
    """
    if not text:
        return ""
    # Split on ₹ when it appears to be a list item (preceded by period/space)
    text = re.sub(r'([.;])\s*(₹\d)', r'\1\n\2', text)
    # Split on bullet characters
    text = re.sub(r'(?<!\n)([•●■□])', r'\n\1', text)
    return text


def clean_markdown_links(text: str) -> str:
    """Add spacing between consecutive markdown links."""
    if not text:
        return ""
    # Add newline between ](url)[next link]
    text = re.sub(r'\)\s*\[', ')\n[', text)
    return text


def normalize_whitespace(text: str) -> str:
    """Clean up excessive whitespace while preserving intentional newlines."""
    if not text:
        return ""
    # Replace tabs with spaces
    text = text.replace("\t", " ")
    # Collapse multiple spaces (but not newlines) into single space
    text = re.sub(r'[^\S\n]+', ' ', text)
    # Collapse 3+ consecutive newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove trailing/leading whitespace per line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    return text.strip()


def normalize_dashes(text: str) -> str:
    """Standardize various dash characters."""
    if not text:
        return ""
    # Em dash → regular dash
    text = text.replace("—", " - ")
    # En dash → regular dash
    text = text.replace("–", "-")
    # Remove trailing "/- " from amounts (₹4,000/- → ₹4,000)
    text = re.sub(r'(\d)/-', r'\1', text)
    return text


def preprocess_scheme_text(text: str, section: str = "") -> str:
    """
    Full preprocessing pipeline for a scheme text section.

    Args:
        text: Raw scraped text content
        section: Section name (details, benefits, eligibility, etc.)
               Used to apply section-specific rules.

    Returns:
        Cleaned, normalized text ready for chunking and embedding.
    """
    if not text or not text.strip():
        return ""

    # 1. Unicode normalization + entity decoding
    text = normalize_unicode(text)

    # 2. Sentence boundary repair
    text = fix_sentence_boundaries(text)

    # 3. Currency standardization
    text = standardize_currency(text)

    # 4. Dash normalization
    text = normalize_dashes(text)

    # 5. Section-specific formatting
    if section in ("application_process",):
        text = split_step_instructions(text)

    if section in ("benefits", "documents_required", "eligibility"):
        text = split_list_items(text)

    if section in ("sources_and_references",):
        text = clean_markdown_links(text)

    # 6. Whitespace normalization (always last)
    text = normalize_whitespace(text)

    return text


def deduplicate_faqs(faqs: List[Dict[str, str]], threshold: float = 0.85) -> List[Dict[str, str]]:
    """
    Remove duplicate FAQ entries based on question similarity.

    Uses a simple normalized text comparison with Jaccard similarity
    on word sets. Threshold of 0.85 catches near-duplicates like:
      "Are families with higher income eligible?" (FAQ #3)
      "Are families with higher income eligible?" (FAQ #9)

    Args:
        faqs: List of {"question": str, "answer": str} dicts
        threshold: Similarity threshold above which FAQs are considered duplicates

    Returns:
        Deduplicated list of FAQs (keeps the longer answer version)
    """
    if not faqs:
        return []

    def _normalize_question(q: str) -> str:
        """Lowercase, remove punctuation, collapse whitespace."""
        q = q.lower().strip()
        q = re.sub(r'[^\w\s]', '', q)
        q = re.sub(r'\s+', ' ', q)
        return q

    def _jaccard_similarity(s1: str, s2: str) -> float:
        """Word-level Jaccard similarity."""
        words1 = set(s1.split())
        words2 = set(s2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    unique_faqs = []
    seen_normalized = []

    for faq in faqs:
        q = faq.get("question", "").strip()
        a = faq.get("answer", "").strip()
        if not q or not a:
            continue

        norm_q = _normalize_question(q)
        is_duplicate = False

        for idx, seen_q in enumerate(seen_normalized):
            sim = _jaccard_similarity(norm_q, seen_q)
            if sim >= threshold:
                is_duplicate = True
                # Keep the version with the longer answer
                existing_answer = unique_faqs[idx].get("answer", "")
                if len(a) > len(existing_answer):
                    unique_faqs[idx] = {"question": q, "answer": a}
                break

        if not is_duplicate:
            unique_faqs.append({"question": q, "answer": a})
            seen_normalized.append(norm_q)

    return unique_faqs


def preprocess_all_sections(raw_data: Dict) -> Dict:
    """
    Apply preprocessing to all sections of a scheme's raw_data dict.
    Returns a new dict with cleaned text (does not modify original).
    """
    cleaned = {}
    text_sections = [
        "details", "benefits", "eligibility", "exclusions",
        "application_process", "documents_required", "sources_and_references"
    ]
    for key in text_sections:
        raw_text = raw_data.get(key, "")
        cleaned[key] = preprocess_scheme_text(raw_text, section=key)

    # Copy non-text fields as-is
    for key in raw_data:
        if key not in text_sections and key != "faqs":
            cleaned[key] = raw_data[key]

    # Deduplicate and preprocess FAQ answers
    raw_faqs = raw_data.get("faqs", [])
    deduped = deduplicate_faqs(raw_faqs)
    cleaned_faqs = []
    for faq in deduped:
        cleaned_faqs.append({
            "question": preprocess_scheme_text(faq["question"]),
            "answer": preprocess_scheme_text(faq["answer"])
        })
    cleaned["faqs"] = cleaned_faqs

    return cleaned

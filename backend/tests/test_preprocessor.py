import pytest
from app.text_preprocessor import (
    normalize_unicode,
    fix_sentence_boundaries,
    standardize_currency,
    split_step_instructions,
    split_list_items,
    clean_markdown_links,
    deduplicate_faqs,
    preprocess_scheme_text,
    preprocess_all_sections
)

def test_normalize_unicode():
    assert normalize_unicode("Hello\ufeff World") == "Hello World"
    assert normalize_unicode("Hello\u200bWorld") == "HelloWorld"
    assert normalize_unicode("A &amp; B") == "A & B"
    assert normalize_unicode("It&#39;s fine") == "It's fine"

def test_fix_sentence_boundaries():
    assert fix_sentence_boundaries("Gujarat.The applicant") == "Gujarat. The applicant"
    assert fix_sentence_boundaries("1st standard.₹6,000") == "1st standard. ₹6,000"
    assert fix_sentence_boundaries("No change here. Already spaced.") == "No change here. Already spaced."

def test_standardize_currency():
    assert standardize_currency("Rs. 4000") == "₹4000"
    assert standardize_currency("Rs 4000") == "₹4000"
    assert standardize_currency("4000 rupees") == "4000 ₹"
    assert standardize_currency("INR 4000") == "₹4000"
    assert standardize_currency("₹ ₹ 4000") == "₹4000"

def test_split_step_instructions():
    # step mid sentence
    assert "Step 1" in split_step_instructions("Do something Step 1: click here")
    assert split_step_instructions("Do something Step 1: click here") == "Do something \nStep 1: click here"

def test_split_list_items():
    assert split_list_items("item 1; ₹5,000") == "item 1;\n₹5,000"
    assert split_list_items("Bullet points:•first item•second item") == "Bullet points:\n•first item\n•second item"

def test_clean_markdown_links():
    assert clean_markdown_links("[Link 1](url1)[Link 2](url2)") == "[Link 1](url1)\n[Link 2](url2)"

def test_deduplicate_faqs():
    faqs = [
        {"question": "Are families with higher income eligible?", "answer": "No, they are not."},
        {"question": "Are families with higher income eligible?", "answer": "No, families with higher income are not eligible to apply."},
        {"question": "What is the age limit?", "answer": "18 to 35 years."}
    ]
    deduped = deduplicate_faqs(faqs)
    assert len(deduped) == 2
    # Should keep the version with the longer answer
    income_faq = [f for f in deduped if "income" in f["question"]][0]
    assert "longer" in income_faq["answer"] or "families with higher income" in income_faq["answer"]

def test_preprocess_scheme_text():
    raw_text = "Hello\ufeff World.The details are: Rs. 5,000/- only."
    cleaned = preprocess_scheme_text(raw_text)
    assert cleaned == "Hello World. The details are: ₹5,000 only."

def test_preprocess_all_sections():
    raw_data = {
        "details": "Details here.Glued sentences.",
        "benefits": "Rs. 1000 stipend.",
        "eligibility": "Income below Rs. 1 lakh.",
        "faqs": [
            {"question": "Is it Rs 100?", "answer": "Yes, it is Rs 100."}
        ],
        "state": "Gujarat"
    }
    cleaned = preprocess_all_sections(raw_data)
    assert cleaned["details"] == "Details here. Glued sentences."
    assert cleaned["benefits"] == "₹1000 stipend."
    assert cleaned["eligibility"] == "Income below ₹1 lakh."
    assert cleaned["faqs"][0]["question"] == "Is it ₹100?"
    assert cleaned["faqs"][0]["answer"] == "Yes, it is ₹100."
    assert cleaned["state"] == "Gujarat"

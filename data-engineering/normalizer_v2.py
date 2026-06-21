import json
import os
import re

def split_documents(doc_string):
    if not doc_string:
        return []
    spaced = re.sub(r'(?<=[a-z])(?=[A-Z])', '|', doc_string)
    parts = [p.strip() for p in spaced.split('|') if p.strip()]
    return parts if parts else [doc_string]


def split_steps(process_string):
    if not process_string:
        return []
    steps = re.findall(r'Step \d+:.*?(?=Step \d+:|$)', process_string, re.DOTALL)
    cleaned = [s.strip().replace('\n', ' ') for s in steps]
    return cleaned if cleaned else [process_string.strip()]


def normalize_scheme(raw_json):
    meta = raw_json.get('metadata', {})
    data = raw_json.get('raw_data', {})

    return {
        'scheme_name': meta.get('scheme_name', '').strip(),
        'category': '',
        'state': meta.get('state', '').strip(),
        'description': data.get('details', '').strip(),
        'benefits': data.get('benefits', '').strip(),
        'eligibility': data.get('eligibility', '').strip(),
        'documents': split_documents(data.get('documents_required', '')),
        'application_steps': split_steps(data.get('application_process', '')),
        'apply_url': meta.get('url', '').strip(),
        'faqs': data.get('faqs', [])
    }


# ─── Test on ONE file first ───
if __name__ == '__main__':
    folder = 'scraped_schemes'
    files = os.listdir(folder)
    first_file = files[0]
    print(f"Testing on: {first_file}\n")

    with open(os.path.join(folder, first_file), 'r', encoding='utf-8') as f:
        raw = json.load(f)

    normalized = normalize_scheme(raw)
    print(json.dumps(normalized, indent=2, ensure_ascii=False))
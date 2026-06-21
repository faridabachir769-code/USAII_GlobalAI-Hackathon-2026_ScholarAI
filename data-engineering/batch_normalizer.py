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


# ─── Process ALL files in the folder ───
folder = 'scraped_schemes'
files = [f for f in os.listdir(folder) if f.endswith('.json')]
print(f"Found {len(files)} JSON files")

normalized_all = []
errors = []

for i, filename in enumerate(files, 1):
    filepath = os.path.join(folder, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        normalized = normalize_scheme(raw)

        # Skip entries with no scheme name (likely broken/empty file)
        if not normalized['scheme_name']:
            errors.append((filename, 'empty scheme_name'))
            continue

        normalized_all.append(normalized)
    except Exception as e:
        errors.append((filename, str(e)))

    if i % 100 == 0:
        print(f"  Processed {i}/{len(files)}...")

# ─── Save combined output ───
output_path = 'normalized_schemes.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(normalized_all, f, indent=2, ensure_ascii=False)

print(f"\nDone!")
print(f"  Successfully normalized: {len(normalized_all)}")
print(f"  Errors/skipped: {len(errors)}")
print(f"  Saved to: {output_path}")

if errors:
    print(f"\nFirst 5 errors:")
    for fname, err in errors[:5]:
        print(f"  - {fname}: {err}")

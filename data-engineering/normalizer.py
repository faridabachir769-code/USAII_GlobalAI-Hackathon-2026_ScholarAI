import json
import re

def normalize_scheme(entry):
    """
    Takes a raw scraped scheme dict and maps it to the schemes table schema.
    Adjust the .get() keys once we see Krish's actual JSON field names.
    """
    return {
        'scheme_name': entry.get('name', entry.get('scheme_name', '')).strip(),
        'category': entry.get('category', '').strip(),
        'state': entry.get('state', 'Central').strip(),
        'description': entry.get('description', '').strip(),
        'benefits': entry.get('benefits', '').strip(),
        'eligibility': entry.get('eligibility', '').strip(),
        'documents': entry.get('documents', []),          # should already be a list
        'application_steps': entry.get('application_steps', []),  # should already be a list
        'apply_url': entry.get('url', entry.get('apply_url', '')).strip(),
    }

# ── Test with dummy data ──
dummy_raw = [
    {
        'name': 'National Education Assistance Scheme',
        'category': 'Education',
        'state': 'Karnataka',
        'description': 'Provides financial assistance for higher education to economically weaker students.',
        'benefits': 'Up to ₹50,000 per year tuition support',
        'eligibility': 'Annual family income below ₹250,000; Karnataka residency required',
        'documents': ['Aadhaar Card', 'Income Certificate', 'Caste Certificate'],
        'application_steps': ['Register on portal', 'Upload documents', 'Submit application'],
        'url': 'https://www.myscheme.gov.in/schemes/neas'
    }
]

normalized = [normalize_scheme(e) for e in dummy_raw]
print(json.dumps(normalized, indent=2))
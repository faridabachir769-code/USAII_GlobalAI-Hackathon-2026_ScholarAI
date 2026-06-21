from supabase import create_client
from dotenv import load_dotenv
load_dotenv()
import os
SUPABASE_URL = os.environ.get("SUPABASE_URL", "http://127.0.0.1:54321")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Same dummy normalized data from before
dummy_normalized = [
    {
        'scheme_name': 'National Education Assistance Scheme',
        'category': 'Education',
        'state': 'Karnataka',
        'description': 'Provides financial assistance for higher education to economically weaker students.',
        'benefits': 'Up to ₹50,000 per year tuition support',
        'eligibility': 'Annual family income below ₹250,000; Karnataka residency required',
        'documents': ['Aadhaar Card', 'Income Certificate', 'Caste Certificate'],
        'application_steps': ['Register on portal', 'Upload documents', 'Submit application'],
        'apply_url': 'https://www.myscheme.gov.in/schemes/neas'
    }
]

response = supabase.table('schemes').insert(dummy_normalized).execute()
print(response)
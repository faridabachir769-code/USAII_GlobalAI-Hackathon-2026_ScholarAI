import json
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()
import os
SUPABASE_URL = os.environ.get("SUPABASE_URL", "http://127.0.0.1:54321")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Loading schemes with embeddings...")
with open('schemes_with_embeddings.json', 'r', encoding='utf-8') as f:
    schemes = json.load(f)

print(f"Inserting {len(schemes)} schemes into Supabase...")

# Insert in batches of 50 (safer than one giant request)
batch_size = 50
inserted = 0
failed = []

for i in range(0, len(schemes), batch_size):
    batch = schemes[i:i + batch_size]
    try:
        response = supabase.table('schemes').insert(batch).execute()
        inserted += len(batch)
        print(f"  Inserted {inserted}/{len(schemes)}...")
    except Exception as e:
        print(f"  Batch {i}-{i+batch_size} FAILED: {e}")
        failed.append((i, str(e)))

print(f"\nDone! Inserted: {inserted} | Failed batches: {len(failed)}")

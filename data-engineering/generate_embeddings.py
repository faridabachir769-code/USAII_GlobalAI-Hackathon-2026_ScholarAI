import json
from sentence_transformers import SentenceTransformer

print("Loading gte-small model...")
model = SentenceTransformer('thenlper/gte-small')  # 384-dim, matches our Supabase column

print("Loading normalized schemes...")
with open('normalized_schemes.json', 'r', encoding='utf-8') as f:
    schemes = json.load(f)

print(f"Found {len(schemes)} schemes. Generating embeddings...")

def build_embedding_text(scheme):
    """Combine the most searchable fields into one text block to embed."""
    parts = [
        scheme.get('scheme_name', ''),
        scheme.get('description', ''),
        scheme.get('benefits', ''),
        scheme.get('eligibility', '')
    ]
    return ' '.join(p for p in parts if p)

# Batch embed for speed (much faster than one-by-one)
texts = [build_embedding_text(s) for s in schemes]
embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

for scheme, embedding in zip(schemes, embeddings):
    scheme['embedding'] = embedding.tolist()  # convert numpy array to plain list for JSON/Supabase

output_path = 'schemes_with_embeddings.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(schemes, f, ensure_ascii=False)

print(f"\nDone! Saved {len(schemes)} schemes with embeddings to {output_path}")
print(f"Embedding dimension: {len(embeddings[0])}")

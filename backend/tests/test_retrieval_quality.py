import pytest
from app.database import SessionLocal, Scheme
from app.vector_store import search_similar_documents

def test_retrieval_basic():
    db = SessionLocal()
    try:
        schemes = db.query(Scheme).all()
        if not schemes:
            pytest.skip("No schemes found in the database. Run ingest_scraped_data.py first.")

        # Search using name of first scheme
        target_scheme = schemes[0]
        results = search_similar_documents(target_scheme.name, db=db, limit=5, threshold=0.35)
        
        assert len(results) > 0, f"No results found for query: '{target_scheme.name}'"
        
        # Verify the structure of the retrieved documents
        for r in results:
            assert "text" in r
            assert "score" in r
            assert "payload" in r
            assert "scheme_id" in r["payload"]
            
        # Verify that pre-filtering works by querying with matching scheme_id
        filtered_results = search_similar_documents(
            target_scheme.name,
            db=db,
            limit=5,
            threshold=0.35,
            scheme_ids=[target_scheme.id]
        )
        
        assert len(filtered_results) > 0
        for r in filtered_results:
            assert r["payload"]["scheme_id"] == target_scheme.id

    finally:
        db.close()

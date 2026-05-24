"""
ChromaDB Vector Store for Cold-Start Recommendations
Builds and searches semantic index of business descriptions
"""

import chromadb
from chromadb.config import Settings
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import EMBEDDINGS, FAISS_INDEX_PATH as CHROMA_PATH
    from database.db import get_all_businesses
except ModuleNotFoundError:
    from backend.config import EMBEDDINGS, FAISS_INDEX_PATH as CHROMA_PATH
    from backend.database.db import get_all_businesses

# Initialize ChromaDB client
def get_chroma_client():
    """Get or create ChromaDB client"""
    os.makedirs(CHROMA_PATH, exist_ok=True)

    client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    return client

def build_index():
    """
    Build ChromaDB collection from businesses list.
    Run once at setup to create the vector index.
    """
    print("🔨 Building ChromaDB collection from business data...")

    # Fetch businesses from database
    businesses = get_all_businesses(limit=20000)  # All businesses we loaded
    print(f"   Loaded {len(businesses)} businesses from database")

    # Initialize ChromaDB
    client = get_chroma_client()

    # Delete existing collection if it exists
    try:
        client.delete_collection(name="businesses")
    except:
        pass

    # Create new collection with custom embedding function
    collection = client.create_collection(
        name="businesses",
        metadata={"description": "Nigerian restaurant businesses for RecoNaija"}
    )

    print("   Generating embeddings and adding to ChromaDB...")

    # Prepare data for ChromaDB
    documents = []
    metadatas = []
    ids = []

    print("   Preparing business descriptions...")
    for i, b in enumerate(businesses):
        # Create rich, sentence-based description for better semantic search
        categories = b['categories'].replace(',', ' and').strip() if b['categories'] else 'restaurant'
        city = b['city'] if b['city'] else 'unknown location'
        state = b['state'] if b['state'] else ''
        stars = b['stars'] if b['stars'] else 0

        # Build natural language description
        text = f"{b['name']} is a {categories} located in {city}, {state}. "
        text += f"It has a rating of {stars} stars. "

        # Add location context
        if city and state:
            text += f"You can find this place in {city}, {state}. "

        # Add category context for better matching
        if 'restaurant' in categories.lower() or 'food' in categories.lower():
            text += "This is a food and dining establishment. "
        if 'bar' in categories.lower() or 'nightlife' in categories.lower():
            text += "This is a good spot for nightlife and drinks. "
        if 'fast food' in categories.lower():
            text += "This is a quick service restaurant. "

        documents.append(text.strip())

        # Store metadata
        metadatas.append({
            "business_id": b['business_id'],
            "name": b['name'],
            "categories": b['categories'],
            "city": b['city'],
            "state": b['state'],
            "stars": float(b['stars'])
        })

        ids.append(f"business_{i}")
        
        # Show progress every 1000 businesses
        if (i + 1) % 1000 == 0:
            print(f"   Prepared {i + 1}/{len(businesses)} descriptions...")

    print(f"   ✅ All {len(documents)} descriptions ready")
    print(f"   📦 Adding documents to ChromaDB in batches of 200...")

    # Generate embeddings and add to ChromaDB in batches
    batch_size = 200
    total_batches = (len(documents) + batch_size - 1) // batch_size
    
    import time
    start_time = time.time()
    
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        batch_num = i // batch_size + 1
        
        batch_texts = documents[i:end_idx]
        batch_metas = metadatas[i:end_idx]
        batch_ids = ids[i:end_idx]
        
        retries = 0
        while retries < 3:
            try:
                print(f"   Generating embeddings for batch {batch_num}/{total_batches}...", end='', flush=True)
                
                # Generate embeddings using PublicAI model
                batch_embeddings = EMBEDDINGS.embed_documents(batch_texts)
                
                # Add to ChromaDB with pre-generated embeddings
                collection.add(
                    documents=batch_texts,
                    embeddings=batch_embeddings,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                
                elapsed = time.time() - start_time
                rate = end_idx / elapsed if elapsed > 0 else 0
                print(f" ✅ ({end_idx}/{len(documents)} | {rate:.0f} docs/sec)")
                break
                
            except Exception as e:
                retries += 1
                wait = 5 * (2 ** (retries - 1))
                print(f"\n   ❌ Batch {batch_num} failed ({retries}/3): {e}")
                if retries < 3:
                    print(f"   Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"   Skipping batch {batch_num}")

    print(f"✅ ChromaDB collection built with {len(businesses)} businesses")
    print(f"   Saved to: {CHROMA_PATH}")

def search_similar_businesses(query: str, top_k: int = 10) -> list[dict]:
    """
    Search ChromaDB collection for businesses matching the query.
    Used ONLY for cold-start users (free-text persona, no user_id).

    Args:
        query: Natural language description (e.g., "affordable Nigerian restaurants")
        top_k: Number of results to return

    Returns:
        List of matching businesses with similarity scores
    """
    import time

    # Initialize ChromaDB client
    client = get_chroma_client()

    # Check if collection exists
    try:
        collection = client.get_collection(name="businesses")
        count = collection.count()
        print(f"[ChromaDB] Collection found with {count} businesses")
        
        if count == 0:
            print(f"[ChromaDB] Collection is empty - embeddings not built yet")
            print(f"[ChromaDB] Using MySQL fallback")
            from database.db import get_all_businesses
            businesses = get_all_businesses(limit=top_k)
            return [{
                "business_id": b['business_id'],
                "name": b['name'],
                "categories": b['categories'],
                "city": b['city'],
                "state": b['state'],
                "stars": b['stars'],
                "similarity": 0.5
            } for b in businesses]
            
    except Exception as e:
        print(f"[ChromaDB] Collection not found: {e}")
        print(f"[ChromaDB] Using MySQL fallback")
        from database.db import get_all_businesses
        businesses = get_all_businesses(limit=top_k)
        return [{
            "business_id": b['business_id'],
            "name": b['name'],
            "categories": b['categories'],
            "city": b['city'],
            "state": b['state'],
            "stars": b['stars'],
            "similarity": 0.5
        } for b in businesses]

    # Generate query embedding with retry logic for 502 errors
    max_retries = 3
    retry_delay = 2
    query_embedding = None

    for attempt in range(max_retries):
        try:
            query_embedding = EMBEDDINGS.embed_query(query)
            break
        except Exception as e:
            if "502" in str(e) or "Bad Gateway" in str(e) or "InternalServerError" in str(e):
                if attempt < max_retries - 1:
                    print(f"[ChromaDB] Embedding API failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"[ChromaDB] Embedding API failed after {max_retries} attempts")
                    print(f"[ChromaDB] Falling back to keyword-based search from MySQL")
                    # Fallback: return top-rated businesses from MySQL
                    from database.db import get_all_businesses
                    businesses = get_all_businesses(limit=top_k)
                    return [{
                        "business_id": b['business_id'],
                        "name": b['name'],
                        "categories": b['categories'],
                        "city": b['city'],
                        "state": b['state'],
                        "stars": b['stars'],
                        "similarity": 0.5  # Default similarity for fallback
                    } for b in businesses]
            else:
                raise

    if query_embedding is None:
        print(f"[ChromaDB] No embedding generated, using MySQL fallback")
        from database.db import get_all_businesses
        businesses = get_all_businesses(limit=top_k)
        return [{
            "business_id": b['business_id'],
            "name": b['name'],
            "categories": b['categories'],
            "city": b['city'],
            "state": b['state'],
            "stars": b['stars'],
            "similarity": 0.5
        } for b in businesses]

    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["metadatas", "distances", "documents"]
    )

    # Format results
    formatted_results = []

    if results['metadatas'] and len(results['metadatas']) > 0:
        metadatas = results['metadatas'][0]
        distances = results['distances'][0] if results['distances'] else [0] * len(metadatas)

        for metadata, distance in zip(metadatas, distances):
            biz = {
                "business_id": metadata.get('business_id', ''),
                "name": metadata.get('name', ''),
                "categories": metadata.get('categories', ''),
                "city": metadata.get('city', ''),
                "state": metadata.get('state', ''),
                "stars": metadata.get('stars', 0),
                # Convert distance to similarity score (0-1 range)
                "similarity": float(1 / (1 + distance))
            }
            formatted_results.append(biz)

    return formatted_results

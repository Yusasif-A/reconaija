"""
Build ChromaDB Vector Store for Cold-Start Recommendations
Uses nomic-embedding model via PublicAI
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.embeddings.vector_store import build_index

if __name__ == "__main__":
    print("🚀 Building ChromaDB Vector Store for RecoNaija...")
    print("="*60)
    build_index()
    print("="*60)
    print("✅ ChromaDB collection ready for cold-start recommendations!")

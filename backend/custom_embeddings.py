"""
Custom Embedding Wrapper for nomic-embed server
"""

import os
import requests
import time
from typing import List
from langchain.embeddings.base import Embeddings

class CustomNomicEmbeddings(Embeddings):
    """
    Custom embeddings using the deployed nomic-embed server with GPU acceleration
    """
    
    def __init__(self, api_url: str, model: str = "nomic-embed", timeout: int = 120):
        self.api_url = api_url.rstrip('/')
        self.model = model
        self.embed_endpoint = f"{self.api_url}/embed"
        self.timeout = timeout
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents with retry logic"""
        embeddings = []
        
        for i, text in enumerate(texts):
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        self.embed_endpoint,
                        json={"input": text},
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    embedding = response.json()
                    embeddings.append(embedding)
                    break  # Success, exit retry loop
                    
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        print(f"[CustomEmbeddings] Timeout on doc {i+1}/{len(texts)}, retry {attempt+1}/{max_retries}...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        print(f"[CustomEmbeddings] Failed after {max_retries} attempts, using zero vector")
                        embeddings.append([0.0] * 768)
                        
                except Exception as e:
                    print(f"[CustomEmbeddings] Error embedding document {i+1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        embeddings.append([0.0] * 768)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"[CustomEmbeddings] Processed {i+1}/{len(texts)} documents")
        
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.embed_endpoint,
                    json={"input": text},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"[CustomEmbeddings] Query timeout, retry {attempt+1}/{max_retries}...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"[CustomEmbeddings] Query failed after {max_retries} attempts")
                    return [0.0] * 768
                    
            except Exception as e:
                print(f"[CustomEmbeddings] Error embedding query: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return [0.0] * 768


import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from typing import List, Optional, Dict, Any

import os

DATA_DIR = os.environ.get("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)


chroma_client = chromadb.PersistentClient(path=os.path.join(DATA_DIR, "chroma"))
embedding_fn = SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
kb_collection = chroma_client.get_or_create_collection("knowledge_base", embedding_function=embedding_fn)

def add_documents_chroma(docs: List[Dict[str, Any]]):
    kb_collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=docs,
    )

def search_chroma(query: str, top_k: int = 6):
    results = kb_collection.query(query_texts=[query], n_results=top_k)
    hits = []
    for doc, meta, score, doc_id in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0], results["ids"][0]
    ):
        meta["text"] = doc
        meta["score"] = float(score)
        meta["id"] = doc_id
        hits.append(meta)
    return hits

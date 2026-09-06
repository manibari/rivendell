---
name: vector-search-setup
loop: dev
pdca: do
description: >
  Set up a vector search knowledge base in a FastAPI project from scratch.
  Covers embedding package selection, data modelling, semantic search API,
  and index management.
  TRIGGER when: user asks about knowledge base packages, wants semantic search,
  wants agent long-term memory, or needs RAG architecture.
  DO NOT TRIGGER when: keyword search (BM25/SQL LIKE) is sufficient, or user
  explicitly wants a graph-based memory system (use knowledge-graph instead).
when_to_use: when setting up semantic search, RAG, or vector-based knowledge base in FastAPI
version: 1.0.0
tags: [backend, ai, vector-search]
languages: [python]
source: harvest-auto
---

# Vector Search Setup

## Overview

Building semantic search / RAG from scratch requires: choosing an embedding
provider, designing the vector storage schema, implementing chunking strategy,
and exposing search via API.

## Package Selection

| Option | When to use |
|--------|-------------|
| `sentence-transformers` | Local embeddings, no API cost, good for dev/privacy |
| `openai` embeddings (`text-embedding-3-small`) | Best quality, needs API key |
| `fastembed` | Lightweight local, fast, good default |
| `chromadb` | Full vector DB with persistence (SQLite-backed) |
| `pgvector` + PostgreSQL | If already on Postgres, simplest path |
| `sqlite-vec` | SQLite extension for vector search, zero-infra |

**Recommended default** (FastAPI + SQLite): `fastembed` for embeddings + `sqlite-vec` or `chromadb` for storage.

## Implementation Steps

### Step 1: Install dependencies

```bash
pip install fastembed chromadb   # or: pip install openai pgvector
```

### Step 2: Embedding service (`services/embedding.py`)

```python
from fastembed import TextEmbedding
from typing import List
import numpy as np

_model = None

def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding("BAAI/bge-small-en-v1.5")  # 384-dim, fast
    return _model

def embed(texts: List[str]) -> List[List[float]]:
    model = get_model()
    return [v.tolist() for v in model.embed(texts)]

def embed_one(text: str) -> List[float]:
    return embed([text])[0]
```

### Step 3: Vector storage schema

**With ChromaDB:**
```python
import chromadb

client = chromadb.PersistentClient(path="./data/chroma")
collection = client.get_or_create_collection(
    name="knowledge",
    metadata={"hnsw:space": "cosine"}
)

def add_document(doc_id: str, text: str, metadata: dict):
    vector = embed_one(text)
    collection.add(
        ids=[doc_id],
        embeddings=[vector],
        documents=[text],
        metadatas=[metadata]
    )

def search(query: str, n_results: int = 5) -> list:
    vector = embed_one(query)
    results = collection.query(
        query_embeddings=[vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    return results
```

**With pgvector (PostgreSQL):**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(384),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

### Step 4: Chunking strategy

```python
def chunk_text(text: str, max_tokens: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + max_tokens
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += max_tokens - overlap
    return chunks
```

Rules:
- Chunk size: 300–500 tokens (not chars)
- Overlap: 10–15% of chunk size
- Preserve sentence boundaries where possible

### Step 5: FastAPI search endpoint

```python
from fastapi import APIRouter

router = APIRouter(prefix="/search", tags=["search"])

@router.get("")
async def semantic_search(q: str, limit: int = 5):
    results = search(q, n_results=limit)
    return {
        "query": q,
        "results": [
            {
                "content": doc,
                "score": 1 - dist,   # cosine distance → similarity
                "metadata": meta,
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]
    }
```

### Step 6: Index management

```python
# Rebuild index from source documents
def rebuild_index(documents: list[dict]):
    collection.delete(where={"source": {"$ne": ""}})   # clear all
    for doc in documents:
        chunks = chunk_text(doc["content"])
        for i, chunk in enumerate(chunks):
            add_document(
                doc_id=f"{doc['id']}_chunk_{i}",
                text=chunk,
                metadata={"source": doc["id"], "title": doc.get("title", "")}
            )
```

## Common Issues

- **Slow first load**: embedding models download on first use (~100MB). Pre-download in startup event.
- **Dimension mismatch**: changing embedding models requires rebuilding the full index.
- **Poor results**: try increasing chunk overlap or using a larger embedding model.
- **Cosine vs dot product**: for normalized embeddings (most models), cosine = dot product. Use cosine.

## Integration

| Skill | When |
|-------|------|
| **firebase-backend** | If using Firestore instead of SQL for metadata |
| **db-migration** | If migrating from keyword search to vector search |
| **knowledge-graph** | For structured entity memory (different use case) |

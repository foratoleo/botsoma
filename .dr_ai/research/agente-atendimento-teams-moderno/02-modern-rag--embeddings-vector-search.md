# Modern RAG - Embeddings e Vector Search

**Data de criacao:** 2026-04-08
**Ultima atualizacao:** 2026-04-08

---

## Estado Atual vs Estado Desejado

### Atual (knowledge_base.py)
- Busca por keywords com regex `_tokenize()`
- Sem embeddings, sem similaridade semantica
- Documentos .md fatiados por headings `##`
- Singleton em memoria

### Desejado
- Busca semantica com embeddings densos
- Hybrid search (BM25 + dense) com Reciprocal Rank Fusion
- Re-ranking com cross-encoder para qualidade

---

## Embeddings para Portugues

### Modelo Recomendado: sentence-transformers

```python
from sentence_transformers import SentenceTransformer

# Modelo multilingual leve (80MB, bom para producao)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Alternativa melhor para PT-BR (maior, mais precisa)
# model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

texts = [
    "Como faco para acessar a plataforma?",
    "Nao consigo fazer login no sistema",
    "Preciso resetar minha senha"
]

embeddings = model.encode(texts)  # shape: (3, 384)
```

| Modelo | Dimensoes | Tamanho | Velocidade | Qualidade PT-BR |
|--------|-----------|---------|------------|----------------|
| all-MiniLM-L6-v2 | 384 | 80MB | Rapida | Boa |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | 470MB | Media | Muito Boa |
| all-mpnet-base-v2 | 768 | 420MB | Lenta | Excelente |

**Recomendacao**: Comecar com `all-MiniLM-L6-v2` pela leveza, migrar para `paraphrase-multilingual` se qualidade semantica em PT-BR for insuficiente.

## Vector Stores

### FAISS (Recomendado para inicio)

```python
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorKnowledgeBase:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents: list[dict] = []

    def build_index(self, documents: list[dict]):
        """documents: [{text, source, heading}]"""
        self.documents = documents
        texts = [d["text"] for d in documents]
        embeddings = self.model.encode(texts, normalize_embeddings=True)

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # Inner Product (cosine com vetores normalizados)
        self.index.add(embeddings.astype(np.float32))

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(query_embedding.astype(np.float32), top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and score > 0.3:  # threshold minimo
                doc = self.documents[idx].copy()
                doc["score"] = float(score)
                results.append(doc)
        return results
```

### ChromaDB (Alternativa com persistencia built-in)

```python
import chromadb
from chromadb.config import Settings

class ChromaKnowledgeBase:
    def __init__(self, persist_dir: str = "./data/chroma"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def add_documents(self, documents: list[dict]):
        ids = [f"doc_{i}" for i in range(len(documents))]
        texts = [d["text"] for d in documents]
        embeddings = self.model.encode(texts).tolist()
        metadatas = [{"source": d["source"], "heading": d.get("heading", "")} for d in documents]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )

        return [
            {
                "text": doc,
                "source": meta["source"],
                "heading": meta["heading"],
                "score": 1 - distance  # cosine distance → similarity
            }
            for doc, meta, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ]
```

### Comparacao: FAISS vs ChromaDB

| Aspecto | FAISS | ChromaDB |
|---------|-------|----------|
| **Instalacao** | `pip install faiss-cpu` | `pip install chromadb` |
| **Persistencia** | Manual (save/load) | Automatica (PersistentClient) |
| **Metadata filtering** | Nao nativo | Sim, nativo |
| **Escalabilidade** | Milhoes de vetores | Centenas de milhares |
| **Simplicidade** | Baixo nivel, mais controle | Alto nivel, mais facil |
| **Dependencies** | Leve | Mais pesada (inclui SQLite, etc) |
| **Recomendacao** | Producao com alto volume | Prototipagem e medio volume |

**Para o Botsoma**: FAISS e mais adequado pelo tamanho leve da base de conhecimento e pela natureza stateless do deploy (Docker). A persistencia pode ser feita via `faiss.write_index()` no startup.

## Pipeline de Indexacao

### Chunking Strategy

```python
import re
from pathlib import Path

def chunk_markdown_file(file_path: Path, max_chunk_size: int = 500) -> list[dict]:
    """Divide documento markdown em chunks semanticos."""
    content = file_path.read_text(encoding="utf-8")
    source = file_path.name

    # Dividir por headings
    sections = re.split(r"(?=^#{1,3}\s)", content, flags=re.MULTILINE)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extrair heading
        heading_match = re.match(r"^#{1,3}\s+(.+)", section)
        heading = heading_match.group(1) if heading_match else ""

        # Se a secao e muito grande, dividir por paragrafos
        if len(section) > max_chunk_size:
            paragraphs = section.split("\n\n")
            for para in paragraphs:
                if len(para.strip()) > 50:  # Ignorar paragrafos muito curtos
                    chunks.append({
                        "text": para.strip(),
                        "source": source,
                        "heading": heading
                    })
        else:
            chunks.append({
                "text": section,
                "source": source,
                "heading": heading
            })

    return chunks
```

### Indexacao no Startup

```python
# Em knowledge_base.py - substituir a implementacao atual

from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class EmbeddingKnowledgeBase:
    def __init__(self, docs_dir: str, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks: list[dict] = []
        self._build(docs_dir)

    def _build(self, docs_dir: str):
        all_chunks = []
        for md_file in Path(docs_dir).glob("**/*.md"):
            chunks = chunk_markdown_file(md_file)
            all_chunks.extend(chunks)

        if not all_chunks:
            return

        self.chunks = all_chunks
        texts = [c["text"] for c in all_chunks]
        embeddings = self.model.encode(texts, normalize_embeddings=True)

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings.astype(np.float32))

    def search(self, query: str, top_k: int = 5, threshold: float = 0.3) -> list[dict]:
        if self.index is None:
            return []

        query_emb = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(query_emb.astype(np.float32), top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and score >= threshold:
                chunk = self.chunks[idx].copy()
                chunk["score"] = float(score)
                results.append(chunk)
        return results

    def format_context(self, query: str, max_results: int = 5) -> str:
        results = self.search(query, top_k=max_results)
        if not results:
            return ""
        return "\n\n---\n\n".join(
            f"[Fonte: {r['source']} - {r['heading']}]\n{r['text']}"
            for r in results
        )
```

## Requisitos Adicionais

```
# requirements.txt - adicionar:
sentence-transformers==3.3.1
faiss-cpu==1.9.0.post1
```

**Nota**: `sentence-transformers` depende de `torch`. Para Docker, usar imagem base `python:3.12-slim` e instalar torch CPU-only:

```
torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
sentence-transformers==3.3.1
faiss-cpu==1.9.0.post1
```

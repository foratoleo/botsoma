# Modern RAG - Retrieval Quality e Reranking

**Data de criacao:** 2026-04-08
**Ultima atualizacao:** 2026-04-08

---

## Pipeline de Retrieval Moderno

### Arquitetura Recomendada: Hybrid Search + Reranking

```
Query do Usuario
       |
       v
  +----------+
  | BM25     |---- sparse scores
  | (keyword)|
  +----------+
       |
       v                    +--------+
  +----------+              | RRF    |---- merged ranking
  | Dense    |---- dense    | (Merge)|
  | (FAISS)  |    scores    +--------+
  +----------+                  |
                                v
                          +------------+
                          | Cross-Enc  |---- final ranking
                          | Reranker   |
                          +------------+
                                |
                                v
                          Top-K chunks → LLM
```

### Por que Hybrid Search?

- **BM25** e excelente para matches exatos de termos tecnicos (nomes de funcionalidades, codigos de erro)
- **Dense retrieval** captura sinonimos e significado semantico
- **RRF** combina ambos sem necessidade de calibrar pesos

## Implementacao do Hybrid Search

### BM25 (Sparse Retrieval)

```python
import math
from collections import Counter

class BM25Retriever:
    def __init__(self, documents: list[dict], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)
        self.avg_dl = sum(len(d["text"].split()) for d in documents) / max(self.doc_count, 1)

        # Pre-compute IDF e TF
        self.doc_freqs = Counter()
        self.doc_tfs = []
        for doc in documents:
            tokens = doc["text"].lower().split()
            tf = Counter(tokens)
            self.doc_tfs.append(tf)
            for term in set(tokens):
                self.doc_freqs[term] += 1

    def _idf(self, term: str) -> float:
        df = self.doc_freqs.get(term, 0)
        return math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        query_tokens = query.lower().split()
        scores = []

        for i, doc in enumerate(self.documents):
            score = 0.0
            doc_len = len(doc["text"].split())
            tf = self.doc_tfs[i]

            for token in query_tokens:
                if token not in tf:
                    continue
                idf = self._idf(token)
                numerator = tf[token] * (self.k1 + 1)
                denominator = tf[token] + self.k1 * (1 - self.b + self.b * doc_len / self.avg_dl)
                score += idf * numerator / denominator

            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [
            {**self.documents[idx], "bm25_score": s}
            for idx, s in scores[:top_k] if s > 0
        ]
```

### Reciprocal Rank Fusion (RRF)

```python
def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    key: str = "text",
    k: int = 60
) -> list[dict]:
    """Combina multiplas listas ranqueadas usando RRF."""
    rrf_scores: dict[str, float] = {}
    doc_map: dict[str, dict] = {}

    for ranked in ranked_lists:
        for position, doc in enumerate(ranked):
            doc_key = doc.get(key, "")
            if not doc_key:
                continue
            if doc_key not in rrf_scores:
                rrf_scores[doc_key] = 0.0
                doc_map[doc_key] = doc
            rrf_scores[doc_key] += 1.0 / (k + position + 1)

    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [
        {**doc_map[k], "rrf_score": v}
        for k, v in sorted_docs
    ]
```

### Hybrid Retriever Completo

```python
class HybridRetriever:
    def __init__(self, dense_kb: EmbeddingKnowledgeBase, documents: list[dict]):
        self.dense_kb = dense_kb
        self.bm25 = BM25Retriever(documents)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        # Dense retrieval (busca mais para dar overlap com BM25)
        dense_results = self.dense_kb.search(query, top_k=top_k * 3)
        # Sparse retrieval
        sparse_results = self.bm25.search(query, top_k=top_k * 3)

        # RRF merge
        merged = reciprocal_rank_fusion(
            [dense_results, sparse_results],
            key="text"
        )

        return merged[:top_k]
```

## Cross-Encoder Reranking

O cross-encoder re-avalia os pares query-documento com um modelo mais preciso (mas mais lento). E usado **depois** do hybrid search para refinar o ranking final.

```python
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        if not documents:
            return []

        pairs = [(query, doc["text"]) for doc in documents]
        scores = self.model.predict(pairs)

        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [
            {**doc, "rerank_score": float(score)}
            for doc, score in scored_docs[:top_k]
        ]
```

### Pipeline Completo

```python
class ProductionRetriever:
    def __init__(self, docs_dir: str):
        self.chunks = self._load_chunks(docs_dir)
        self.dense_kb = EmbeddingKnowledgeBase(docs_dir)
        self.hybrid = HybridRetriever(self.dense_kb, self.chunks)
        self.reranker = Reranker()

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        # Etapa 1: Hybrid retrieval (rapido, ~50ms)
        candidates = self.hybrid.search(query, top_k=top_k * 3)

        # Etapa 2: Cross-encoder reranking (~100ms para 15 docs)
        ranked = self.reranker.rerank(query, candidates, top_k=top_k)

        return ranked
```

## Metricas de Qualidade RAG

### RAGAS (Retrieval Augmented Generation Assessment)

```python
# Instalar: pip install ragas

# Metricas principais:
# - faithfulness: a resposta esta fiel ao contexto recuperado? (0-1)
# - context_precision: os chunks retornados sao relevantes? (0-1)
# - context_recall: todos os chunks necessarios foram encontrados? (0-1)
# - answer_relevancy: a resposta responde a pergunta? (0-1)
```

### Avaliacao com Conjunto de Teste

```python
# Estrutura do dataset de teste:
test_cases = [
    {
        "question": "Como faco para acessar a plataforma?",
        "expected_answer_contains": ["login", "senha", "acesso"],
        "expected_decision": "explain",
        "expected_sources": ["docs/login.md"]
    },
    {
        "question": "Sistema esta fora do ar",
        "expected_answer_contains": ["suporte"],
        "expected_decision": "escalate",
        "expected_sources": []
    },
    # ... mais casos
]
```

### Funcao de Avaliacao Simples

```python
def evaluate_rag_quality(
    retriever: ProductionRetriever,
    test_cases: list[dict]
) -> dict:
    results = {"total": len(test_cases), "passed": 0, "failures": []}

    for case in test_cases:
        retrieved = retriever.search(case["question"], top_k=5)

        # Verificar se os chunks relevantes foram encontrados
        sources_found = [r["source"] for r in retrieved]
        expected = case.get("expected_sources", [])

        if expected:
            overlap = set(sources_found) & set(expected)
            if not overlap:
                results["failures"].append({
                    "question": case["question"],
                    "reason": f"Expected sources {expected}, got {sources_found}",
                    "scores": [r.get("rerank_score", r.get("rrf_score", 0)) for r in retrieved[:3]]
                })
                continue

        results["passed"] += 1

    results["pass_rate"] = results["passed"] / results["total"]
    return results
```

## Thresholds Recomendados

| Metrica | Threshold | Acao se Abaixo |
|---------|-----------|----------------|
| Dense cosine similarity | 0.30 | Descartar chunk |
| RRF score | 0.01 | Descartar chunk |
| Cross-encoder score | -2.0 | Descartar chunk |
| Rerank score (top-1) | < 0.0 | Considerar sem contexto relevante |
| Faithfulness | < 0.7 | Ajustar prompt do LLM |

## Dependencias Adicionais

```
# requirements.txt - adicionar para retrieval quality:
sentence-transformers==3.3.1
faiss-cpu==1.9.0.post1
torch==2.5.1
```

## Estrategia de Implementacao Incremental

1. **Fase 1**: Substituir keyword search por FAISS + embeddings (maior ganho imediato)
2. **Fase 2**: Adicionar BM25 + RRF para hybrid search
3. **Fase 3**: Adicionar cross-encoder reranking para refino final
4. **Fase 4**: Criar dataset de teste e avaliar com metricas RAGAS

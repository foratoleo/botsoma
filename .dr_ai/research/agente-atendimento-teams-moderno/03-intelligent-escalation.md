# Escalacao Inteligente

**Data de criacao:** 2026-04-08
**Ultima atualizacao:** 2026-04-08

---

## Estado Atual vs Estado Desejado

### Atual (triage_flow.py)
- Decisao binaria: explain ou escalate
- Sem score de confianca
- Sem analise de sentimento
- Escalacao sem contexto rico para o atendente
- Sem modo co-piloto

### Desejado
- Score de confianca para decisao
- Deteccao de sentimento para trigger de escalacao
- Warm handoff com contexto transfer completo
- Modo co-piloto para atendentes humanos

---

## Scoring de Confianca

### Calculo do Confidence Score

```python
@dataclass
class ConfidenceMetrics:
    """Metricas que alimentam o score de confianca."""
    retrieval_score: float       # Score do top-1 chunk retornado (0-1)
    retrieval_coverage: float    # Quantos chunks relevantes (0-1)
    llm_decision_entropy: float  # Incerteza da decisao do LLM (0-1)
    kb_relevance: float          # Relevancia do KB para o topico (0-1)

    @property
    def overall_confidence(self) -> float:
        """Media ponderada das metricas."""
        weights = {
            "retrieval_score": 0.35,
            "retrieval_coverage": 0.20,
            "llm_decision_entropy": 0.25,
            "kb_relevance": 0.20,
        }
        scores = {
            "retrieval_score": self.retrieval_score,
            "retrieval_coverage": self.retrieval_coverage,
            "llm_decision_entropy": 1.0 - self.llm_decision_entropy,  # Inverter: menos entropia = mais confianca
            "kb_relevance": self.kb_relevance,
        }
        total_weight = sum(weights.values())
        return sum(weights[k] * scores[k] for k in weights) / total_weight
```

### Thresholds de Confianca

| Score | Acao | Descricao |
|-------|------|-----------|
| **>= 0.80** | Auto-explain | Alta confianca na resposta do RAG |
| **0.60 - 0.79** | Clarify | Pedir mais uma pergunta para desambiguar |
| **0.40 - 0.59** | Low-confidence explain | Explicar com caveat + oferecer escalacao |
| **< 0.40** | Auto-escalate | KB nao cobre o topico adequadamente |

### Integracao com Triage Flow

```python
def _compute_confidence(session: Session, search_results: list[dict], parsed: dict) -> ConfidenceMetrics:
    retrieval_score = max((r.get("rerank_score", r.get("score", 0)) for r in search_results), default=0)
    # Normalizar para 0-1 range
    retrieval_score = max(0, min(1, (retrieval_score + 3) / 6))  # cross-encoder range ~[-3, 3]

    retrieval_coverage = min(1.0, len([r for r in search_results if r.get("score", 0) > 0.3]) / 3)

    # Heuristica para entropia da decisao: se reason menciona "ambiguo" ou "incerto"
    reason = parsed.get("reason", "").lower()
    entropy_keywords = ["ambiguo", "incerto", "nao tenho certeza", "ambiguo", "not sure"]
    llm_entropy = 0.6 if any(kw in reason for kw in entropy_keywords) else 0.2

    # KB relevance: se algum resultado tem score alto
    kb_relevance = 0.8 if retrieval_score > 0.6 else (0.5 if retrieval_score > 0.3 else 0.2)

    return ConfidenceMetrics(
        retrieval_score=retrieval_score,
        retrieval_coverage=retrieval_coverage,
        llm_decision_entropy=llm_entropy,
        kb_relevance=kb_relevance,
    )
```

## Deteccao de Sentimento

### Abordagem Simples (sem modelo extra)

```python
FRUSTRATION_PATTERNS = {
    "ja tentei de tudo": 0.7,
    "nao funciona de jeito nenhum": 0.8,
    "pessimo": 0.8,
    "horrivel": 0.8,
    "terrible": 0.8,
    "absurdo": 0.7,
    "ridiculo": 0.7,
    "vou desistir": 0.9,
    "quero falar com alguem": 0.9,
    "quero cancelar": 0.8,
    "pela terceira vez": 0.7,
    "ja liguei antes": 0.6,
    "ninguem resolve": 0.8,
    "urgente": 0.5,
    "emergencia": 0.7,
}

def detect_frustration(text: str) -> float:
    """Retorna score de frustracao (0-1)."""
    normalized = text.lower().strip()
    max_score = 0.0

    for pattern, score in FRUSTRATION_PATTERNS.items():
        if pattern in normalized:
            max_score = max(max_score, score)

    # Multiplos indicadores = frustracao cumulativa
    match_count = sum(1 for p in FRUSTRATION_PATTERNS if p in normalized)
    if match_count >= 3:
        max_score = min(1.0, max_score + 0.2)

    return max_score
```

### Abordagem com Modelo (producao)

```python
# pip install transformers
from transformers import pipeline

class SentimentAnalyzer:
    def __init__(self):
        # Modelo multilingual leve para analise de sentimento
        self.classifier = pipeline(
            "text-classification",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            top_k=None
        )

    def analyze(self, text: str) -> dict:
        result = self.classifier(text)[0]

        # Mapear stars para sentimento
        scores = {r["label"]: r["score"] for r in result}
        negative_score = scores.get("1 star", 0) + scores.get("2 stars", 0)
        positive_score = scores.get("4 stars", 0) + scores.get("5 stars", 0)

        return {
            "sentiment": "negative" if negative_score > positive_score else "positive",
            "frustration_score": negative_score,
            "confidence": max(negative_score, positive_score),
        }
```

### Triggers de Escalacao por Sentimento

| Cenario | Trigger | Acao |
|---------|---------|------|
| Frustracao > 0.7 na 1a msg | Frustracao imediata | Oferecer card: "Quer falar com atendente?" |
| Frustracao > 0.5 + 2+ perguntas | Frustracao crescente | Escalar com tag "frustrado" |
| Palavras "falar com alguem" | Request explicito | Escalar imediatamente |
| Sentimento piorando ao longo da conversa | Tendencia negativa | Escalar preventivamente |

## Warm Handoff

Transferencia de contexto completa para o atendente humano:

```python
@dataclass
class EscalationContext:
    """Contexto completo transferido ao atendente."""
    session_id: str
    user_name: str
    user_id: str
    conversation_summary: str       # Resumo gerado por LLM
    full_history: str               # Historico completo
    triage_decision: str            # "explain" ou "escalate"
    triage_reason: str              # Razao da decisao
    confidence_score: float         # Score de confianca
    frustration_score: float        # Score de frustracao
    topics_discussed: list[str]     # Topicos abordados
    documents_tried: list[str]      # Documentos tentados
    suggested_solutions: list[str]  # Solucoes sugeridas pelo bot
    urgency: str                    # "urgente", "normal", "baixa"
    language: str                   # "pt" ou "en"
    timestamp: str                  # ISO format

def build_escalation_context(session: Session, step: TriageStep, confidence: ConfidenceMetrics) -> EscalationContext:
    return EscalationContext(
        session_id=session.id,
        user_name="",  # preenchido pelo bot com dados do Teams
        user_id="",
        conversation_summary=_generate_summary(session),
        full_history=session.history_as_text(),
        triage_decision=step.decision,
        triage_reason=step.reason,
        confidence_score=confidence.overall_confidence,
        frustration_score=detect_frustration(session.user_text_joined()),
        topics_discussed=_extract_topics(session),
        documents_tried=step.sources,
        suggested_solutions=[t["content"] for t in session.turns if t["role"] == "assistant"],
        urgency=step.urgency or "normal",
        language="pt",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
```

### Mensagem de Escalacao Enriquecida

```python
def format_escalation_card(context: EscalationContext) -> dict:
    """Gera Adaptive Card com contexto da escalacao."""
    urgency_emoji = {"urgente": "🔴", "normal": "🟡", "baixa": "🟢"}
    emoji = urgency_emoji.get(context.urgency, "⚪")

    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": f"{emoji} Escalacao - {context.urgency.upper()}",
                "weight": "Bolder",
                "size": "Large"
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Usuario:", "value": context.user_name},
                    {"title": "Confianca:", "value": f"{context.confidence_score:.0%}"},
                    {"title": "Frustracao:", "value": f"{context.frustration_score:.0%}"},
                    {"title": "Razao:", "value": context.triage_reason},
                    {"title": "Idioma:", "value": context.language}
                ]
            },
            {
                "type": "TextBlock",
                "text": "Resumo:",
                "weight": "Bolder",
                "size": "Medium"
            },
            {
                "type": "TextBlock",
                "text": context.conversation_summary,
                "wrap": true
            },
            {
                "type": "TextBlock",
                "text": "Solucoes tentadas:",
                "weight": "Bolder",
                "size": "Medium"
            },
            {
                "type": "TextBlock",
                "text": ", ".join(context.documents_tried) or "Nenhuma",
                "wrap": true,
                "isSubtle": True
            }
        ]
    }
```

## Modo Co-Piloto

O atendente humano recebe sugestoes do bot durante o atendimento:

```python
class CopilotService:
    """Sugere respostas ao atendente humano baseado no contexto."""

    async def suggest_response(self, context: EscalationContext, latest_message: str) -> str:
        """Retorna sugestao de resposta para o atendente."""
        kb = get_knowledge_base()
        kb_context = kb.format_context(latest_message, max_results=3)

        prompt = f"""
        Contexto da conversa (escalada do bot):
        Resumo: {context.conversation_summary}
        Frustracao: {context.frustration_score:.0%}
        Confianca do bot: {context.confidence_score:.0%}

        Ultima mensagem do usuario: {latest_message}

        Documentacao relevante:
        {kb_context}

        Sugira uma resposta curta e empatica para o atendente enviar.
        """
        return await _call_llm(prompt, "Responda em portugues.", max_tokens=300)
```

## Resumo Automatico da Conversa

```python
async def _generate_summary(session: Session) -> str:
    """Gera resumo da conversa usando LLM."""
    history = session.history_as_text()

    if len(history) < 100:
        return history[:200]

    prompt = f"""
    Resuma esta conversa de suporte em 2-3 frases, incluindo:
    - O problema do usuario
    - O que foi tentado
    - Status atual

    Conversa:
    {history[:2000]}
    """
    return await _call_llm(prompt, "Responda em portugues.", max_tokens=200)
```

## Fluxo de Escalacao Completo

```
Usuario com problema
       |
       v
Triage Flow (max 3 perguntas)
       |
       v
Confidence Score + Sentiment Analysis
       |
       +-- conf >= 0.8 → EXPLAIN (resposta com RAG)
       |
       +-- conf 0.6-0.79 → CLARIFY (+1 pergunta)
       |
       +-- conf < 0.6 OU frustracao > 0.7 → ESCALATE
       |
       v
EscalationContext completo
       |
       v
Proactive message para canal de suporte
com Adaptive Card enriquecido
       |
       v
Atendente aceita → Modo co-piloto ativado
```

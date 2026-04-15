import json
import time
from dataclasses import dataclass

import httpx
import structlog

from bot.config import ZAI_API_KEY, ZAI_MODEL, ZAI_BASE_URL, ZAI_TIMEOUT_MS

logger = structlog.get_logger(__name__)

CLASSIFY_SYSTEM_PROMPT = """Voce e um classificador de mensagens de suporte. Sua UNICA tarefa e classificar se a mensagem do usuario descreve um ERRO/PROBLEMA tecnico ou uma PERGUNTA/INFORMACAO.

Responda APENAS com um JSON valido, sem texto adicional:
{"is_error": true, "confidence": 0.9, "reason": "motivo curto"}

Criteria para is_error=true:
- O usuario relata que algo NAO esta funcionando
- O usuario menciona erro, falha, bug, quebra, problema
- O usuario descreve comportamento inesperado que impede trabalho
- O usuario pede ajuda porque algo esta quebrado

Criteria para is_error=false:
- O usuario pergunta como fazer algo
- O usuario pergunta sobre funcionalidades
- O usuario pede informacoes, documentacao, ou explicacao
- O usuario faz sugestoes ou pedidos de melhoria

Seja rigoroso: so classifique como erro quando houver clareza de que algo esta quebrado."""

EXPLAIN_SYSTEM_PROMPT_TEMPLATE = """Voce e um assistente de suporte tecnico acessado via Microsoft Teams. Sua funcao e explicar topicos baseados na documentacao disponivel.

## REGRAS
- Seja curto. Max 3-4 frases.
- Responda em portugues do Brasil.
- Use a documentacao abaixo como base para sua resposta.
- Se a documentacao nao contem a resposta, diga claramente que nao tem essa informacao e sugira que o usuario entre em contato com o suporte humano.
- NAO invente informacoes que nao estejam na documentacao.
- Prefira listas e formatos estruturados.

## DOCUMENTACAO DISPONIVEL
{context}

## MENSAGEM DO USUARIO
{user_message}"""

MAX_TOKENS_CLASSIFY = 256
MAX_TOKENS_EXPLAIN = 1024


@dataclass
class ClassificationResult:
    is_error: bool
    confidence: float
    reason: str


@dataclass
class ExplanationResult:
    explanation: str
    sources_used: list[str]


async def _call_llm(
    system_prompt: str, user_message: str, max_tokens: int = MAX_TOKENS_EXPLAIN
) -> str:
    payload = {
        "model": ZAI_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.1,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }

    t0 = time.monotonic()
    async with httpx.AsyncClient(timeout=ZAI_TIMEOUT_MS / 1000) as client:
        response = await client.post(
            ZAI_BASE_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ZAI_API_KEY,
                "anthropic-version": "2023-06-01",
            },
        )
    latency_ms = round((time.monotonic() - t0) * 1000, 1)

    if not response.is_success:
        logger.error(
            "llm_call_failed",
            status_code=response.status_code,
            latency_ms=latency_ms,
            model=ZAI_MODEL,
        )
        raise Exception(f"LLM error {response.status_code}: {response.text[:200]}")

    data = response.json()
    text = data.get("content", [{}])[0].get("text", "")

    logger.info(
        "llm_call_completed",
        model=ZAI_MODEL,
        max_tokens=max_tokens,
        latency_ms=latency_ms,
        response_length=len(text),
    )

    return text


async def classify_message(user_text: str) -> ClassificationResult:
    try:
        raw = await _call_llm(CLASSIFY_SYSTEM_PROMPT, user_text, MAX_TOKENS_CLASSIFY)

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        parsed = json.loads(cleaned)

        return ClassificationResult(
            is_error=bool(parsed.get("is_error", False)),
            confidence=float(parsed.get("confidence", 0.5)),
            reason=str(parsed.get("reason", "")),
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.warning(
            "classification_parse_failed",
            error=str(exc),
            text_preview=user_text[:80],
            fallback="keyword_match",
        )

        error_keywords = [
            "erro",
            "error",
            "falha",
            "falhou",
            "bug",
            "quebrou",
            "nao funciona",
            "problema",
            "não funciona",
        ]
        lower = user_text.lower()
        is_error = any(kw in lower for kw in error_keywords)

        return ClassificationResult(
            is_error=is_error,
            confidence=0.5 if is_error else 0.3,
            reason="fallback keyword match" if is_error else "no error keywords found",
        )


async def explain_from_docs(
    user_text: str, doc_context: str, sources: list[str]
) -> ExplanationResult:
    if not doc_context:
        return ExplanationResult(
            explanation="Nao encontrei informacoes sobre esse tema na documentacao disponivel. "
            "Posso escalar sua pergunta para um membro da equipe de suporte. Deseja?",
            sources_used=[],
        )

    system_prompt = EXPLAIN_SYSTEM_PROMPT_TEMPLATE.format(
        context=doc_context,
        user_message=user_text,
    )

    explanation = await _call_llm(system_prompt, user_text, MAX_TOKENS_EXPLAIN)

    return ExplanationResult(
        explanation=explanation,
        sources_used=sources,
    )

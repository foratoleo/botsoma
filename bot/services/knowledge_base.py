"""
Knowledge Base service.

Loads all .md and .txt files from the configured knowledge directory,
splits them into sections by headings, and provides keyword-based
retrieval for the LLM context.
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional

from bot.config import KNOWLEDGE_BASE_DIR

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """In-memory knowledge base loaded from markdown/text files."""

    EXCLUDED_DOCS = {"09-arquitetura-tecnica.md", "exemplo-documentacao.md"}

    def __init__(self, base_dir: Path = KNOWLEDGE_BASE_DIR):
        self.base_dir = Path(base_dir)
        self._sections: list[dict] = []
        self._loaded = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> int:
        """Load (or reload) all documents from disk. Returns section count."""
        self._sections.clear()
        if not self.base_dir.is_dir():
            logger.warning("Knowledge base directory not found: %s", self.base_dir)
            return 0

        count = 0
        for filepath in sorted(self.base_dir.rglob("*")):
            if filepath.suffix.lower() in (".md", ".txt", ".markdown"):
                if filepath.name in self.EXCLUDED_DOCS:
                    logger.debug("Skipping excluded doc: %s", filepath.name)
                    continue
                count += self._load_file(filepath)

        self._loaded = True
        logger.info(
            "Knowledge base loaded: %d sections from %d files",
            len(self._sections),
            count,
        )
        return len(self._sections)

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Return top sections matching *query* by keyword overlap.

        Each result is a dict with keys:
          - source: relative file path
          - heading: section heading (or first line)
          - content: section text
          - score: keyword overlap count
        """
        if not self._loaded:
            self.load()

        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            return []

        scored = []
        for section in self._sections:
            section_tokens = set(section["tokens"])
            overlap = len(query_tokens & section_tokens)
            if overlap > 0:
                scored.append({**section, "score": overlap})

        scored.sort(key=lambda s: s["score"], reverse=True)
        return scored[:max_results]

    def format_context(self, query: str, max_results: int = 5) -> str:
        """Return a formatted string of relevant sections for LLM context."""
        results = self.search(query, max_results)
        if not results:
            return ""

        parts = []
        for r in results:
            parts.append(f"### Fonte: {r['source']}")
            if r["heading"]:
                parts.append(f"## {r['heading']}")
            parts.append(r["content"])
            parts.append("")

        return "\n".join(parts)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def section_count(self) -> int:
        return len(self._sections)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Lowercase, strip punctuation, split on whitespace."""
        return re.findall(r"[a-záàâãéèêíïóôõöúçñ]{2,}", text.lower())

    def _load_file(self, filepath: Path) -> int:
        """Parse a single file into heading-based sections."""
        try:
            text = filepath.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error("Failed to read %s: %s", filepath, exc)
            return 0

        relative = filepath.relative_to(self.base_dir)
        sections = self._split_by_headings(text)

        for heading, content in sections:
            full_text = f"{heading}\n{content}" if heading else content
            self._sections.append(
                {
                    "source": str(relative),
                    "heading": heading,
                    "content": content.strip(),
                    "tokens": self._tokenize(full_text),
                }
            )

        logger.debug("Loaded %d sections from %s", len(sections), relative)
        return len(sections)

    @staticmethod
    def _split_by_headings(text: str) -> list[tuple[str, str]]:
        """Split markdown into sections by ## headings.

        Returns list of (heading, body) tuples.
        """
        # Match ## or ### headings (but not single # which is the title)
        pattern = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
        splits = list(pattern.finditer(text))

        if not splits:
            # No headings — treat entire file as one section
            return [("", text)]

        sections = []
        for i, match in enumerate(splits):
            heading = match.group(2).strip()
            start = match.end()
            end = splits[i + 1].start() if i + 1 < len(splits) else len(text)
            body = text[start:end].strip()
            sections.append((heading, body))

        # Include content before the first heading
        if splits[0].start() > 0:
            preamble = text[: splits[0].start()].strip()
            if preamble:
                sections.insert(0, ("", preamble))

        return sections


# Module-level singleton
_kb: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    """Return the singleton KnowledgeBase, loading on first access."""
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
        _kb.load()
    return _kb

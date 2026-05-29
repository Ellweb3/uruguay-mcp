"""Lightweight relevance ranking over the tool registry.

A dependency-free BM25-lite scorer: it rewards tools whose name/summary/keywords
share rare query terms. Good enough to route a natural-language need ("precio
del dólar", "buscar datasets de salud") to the right handler without pulling in
a search engine.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from ..shared.registry import ToolSpec, registry

_WORD = re.compile(r"[\wáéíóúñü]+", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def search(
    query: str, *, limit: int = 8, module: str | None = None
) -> list[tuple[ToolSpec, float]]:
    specs = [s for s in registry.all() if module is None or s.module == module]
    if not specs:
        return []

    docs = {s.name: _tokens(s.search_text()) for s in specs}
    n = len(specs)
    df: Counter[str] = Counter()
    for toks in docs.values():
        for term in set(toks):
            df[term] += 1

    q_terms = _tokens(query)
    scored: list[tuple[ToolSpec, float]] = []
    for spec in specs:
        toks = docs[spec.name]
        tf = Counter(toks)
        score = 0.0
        for term in q_terms:
            if term not in tf:
                continue
            idf = math.log(1 + n / (1 + df[term]))
            score += idf * (1 + math.log(tf[term]))
        if score > 0:
            scored.append((spec, round(score, 4)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]

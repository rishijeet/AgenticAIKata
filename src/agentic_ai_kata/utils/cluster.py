from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple


def _norm(s: str) -> str:
    return " ".join(s.lower().strip().split())


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def cluster_news(items: List[Dict[str, Any]], title_key: str = "title", threshold: float = 0.82) -> List[Dict[str, Any]]:
    """
    Very lightweight clustering/deduplication: groups items whose titles are highly similar.
    Returns a list of cluster dicts with 'title', 'items' members. Title is the first item's title.
    """
    clusters: List[Tuple[str, List[Dict[str, Any]]]] = []  # (rep_title, items)

    for it in items:
        t = (it.get(title_key) or "").strip()
        if not t:
            # Put empty-title items into their own cluster
            clusters.append((t, [it]))
            continue
        placed = False
        for idx, (rep, members) in enumerate(clusters):
            if rep and similarity(t, rep) >= threshold:
                members.append(it)
                placed = True
                break
        if not placed:
            clusters.append((t, [it]))

    # Build output with representative title and aggregated fields
    out: List[Dict[str, Any]] = []
    for rep, members in clusters:
        # Prefer the longest title as representative
        if members:
            rep_title = max((m.get(title_key) or "" for m in members), key=len, default=rep)
        else:
            rep_title = rep
        out.append({
            "title": rep_title or rep,
            "items": members,
        })
    return out

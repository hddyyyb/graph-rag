import re
from typing import List

STOPWORDS = {
    "the", "a", "an", "is", "are", "of", "to", "and", "or", "in", "on", "for",
    "with", "by", "as", "at", "from", "that", "this"
}

def extract_terms(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    results = []
    seen = set()

    for token in tokens:
        if len(token) < 2:
            continue
        if token in STOPWORDS:
            continue
        if token in seen:
            continue
        seen.add(token)
        results.append(token)

    return results
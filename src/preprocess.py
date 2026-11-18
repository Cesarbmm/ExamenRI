"""Normalización coherente para indexación y consultas de SciFact."""

import re
import unicodedata

from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# La negación es importante en afirmaciones científicas ("not", "no").
STOPWORDS = frozenset(ENGLISH_STOP_WORDS - {"no", "not", "nor", "without"})
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def preprocess(text: str) -> list[str]:
    """Unicode NFKC, minúsculas, tokens alfanuméricos, stopwords, Porter."""
    normalized = unicodedata.normalize("NFKC", text or "").casefold()
    stemmer = PorterStemmer()
    return [
        stemmer.stem(token)
        for token in TOKEN_PATTERN.findall(normalized)
        if token not in STOPWORDS
    ]

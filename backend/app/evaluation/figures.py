"""Numeric figures in prose, for checking that a statement's numbers appear in its evidence."""

import re

DATE_LIKE = re.compile(
    r"\b\d{4}-\d{2}(?:-\d{2})?\b|\b\d{4}-Q\d\b|\b[1-4]Q\d{2}\b|\b\d[HQ]\d{2}\b|\bQ[1-4]\b"
    r"|\b(?:19|20)\d{2}\b"
)
FIGURE = re.compile(
    r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+(?=\s*%)|\d+(?=\s*(?:million|billion|thousand)\b)"
)
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def figures_in(text: str) -> list[str]:
    """Figures in reading order; dates, periods and bare years are not figures."""
    return FIGURE.findall(DATE_LIKE.sub(" ", text))


def unsupported(text: str, support_texts: list[str]) -> list[str]:
    """Figures in `text` that appear in none of the support texts, each reported once."""
    available = {
        token.replace(",", "").rstrip(".")
        for support in support_texts
        for token in NUMBER.findall(support)
    }
    missing: list[str] = []
    for figure in figures_in(text):
        if figure.replace(",", "") not in available and figure not in missing:
            missing.append(figure)
    return missing

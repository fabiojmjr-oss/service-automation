"""The executive brief, against the READMEs that are already under test.

`docs/FINDINGS.md` restates the findings for a reader who decides rather than verifies, so it quotes
figures without deriving them. A second copy of a number is a second place for it to go stale, and the
claim tests cannot see this file. So the coupling is asserted instead: every figure the brief quotes has
to appear in the root README of the same language, which the claim tests re-derive from the generator.
The brief cannot drift without the build failing, and it cannot introduce a figure nothing checks.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUMBER = re.compile(r"\d[\d.,]*\d|\d")
SEPARATORS = {"en": (",", "."), "pt": (".", ",")}


def canonical(token: str, language: str) -> str:
    """One spelling for a figure, so the two language editions can be compared to each other."""
    thousands, decimal = SEPARATORS[language]
    return token.replace(thousands, "").replace(decimal, ".")


def figures(text: str, language: str) -> set[str]:
    """The quantities in a document: decimals, percentages and counts of a hundred or more.

    A bare small integer is prose - four policies, eight agents, wave 3 - and matching those would make
    the test loud without making it strict.
    """
    found = set()
    for match in NUMBER.finditer(text):
        value = canonical(match.group(), language)
        percentage = text[match.end() : match.end() + 1] == "%"
        if "." in value or percentage or int(value) >= 100:
            found.add(value)
    return found


def brief(language: str) -> Path:
    return ROOT / "docs" / ("FINDINGS.md" if language == "en" else "FINDINGS.pt-BR.md")


def readme(language: str) -> Path:
    return ROOT / ("README.md" if language == "en" else "README.pt-BR.md")


def test_every_figure_in_the_brief_is_a_figure_the_readme_already_publishes() -> None:
    """The brief derives nothing, so a figure only it carries is a figure no test re-derives."""
    for language in SEPARATORS:
        quoted = figures(brief(language).read_text(encoding="utf-8"), language)
        assert quoted, (
            f"{brief(language).name} quotes no figures, so this test is asserting nothing"
        )
        published = figures(readme(language).read_text(encoding="utf-8"), language)
        unbacked = sorted(quoted - published, key=float)
        assert not unbacked, (
            f"{brief(language).name} quotes figures the README does not: {unbacked}"
        )


def test_the_two_editions_of_the_brief_quote_the_same_figures() -> None:
    """A figure corrected in one language and not the other is the defect this repository keeps making."""
    english = figures(brief("en").read_text(encoding="utf-8"), "en")
    portuguese = figures(brief("pt").read_text(encoding="utf-8"), "pt")
    assert english == portuguese, (
        f"only in English: {sorted(english - portuguese, key=float)}; "
        f"only in Portuguese: {sorted(portuguese - english, key=float)}"
    )


def test_the_brief_covers_every_example_in_both_languages() -> None:
    """One finding per example, in both editions, or the brief has quietly stopped being complete."""
    scripts = sorted(path.name for path in (ROOT / "examples").glob("*.py"))
    assert scripts, "no examples found, which means this test is not testing anything"
    for language in SEPARATORS:
        text = brief(language).read_text(encoding="utf-8")
        for script in scripts:
            assert script in text, f"{brief(language).name} does not link examples/{script}"
        headings = re.findall(r"^## \d+\. ", text, re.M)
        assert len(headings) == len(scripts), (
            f"{brief(language).name} has {len(headings)} numbered findings "
            f"for {len(scripts)} examples"
        )


def test_the_brief_is_bilingual_and_reachable() -> None:
    """A document nothing links is a document nobody reads, and the README table is the only route."""
    assert "*[Português](FINDINGS.pt-BR.md)*" in brief("en").read_text(encoding="utf-8")
    assert "*[English](FINDINGS.md)*" in brief("pt").read_text(encoding="utf-8")
    for language in SEPARATORS:
        text = readme(language).read_text(encoding="utf-8")
        assert "docs/FINDINGS.md" in text or "docs/FINDINGS.pt-BR.md" in text, readme(language).name


def test_the_brief_declares_what_it_is_not() -> None:
    """It reads as a set of conclusions, so it has to carry the limitation on its face."""
    english = brief("en").read_text(encoding="utf-8")
    assert "not market statistics" in english
    assert "benchmark" in english
    assert "DISCLAIMER.md" in english
    portuguese = brief("pt").read_text(encoding="utf-8")
    assert "estatísticas de mercado" in portuguese
    assert "benchmark" in portuguese
    assert "DISCLAIMER.md" in portuguese

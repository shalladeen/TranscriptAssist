from typing import Iterable
import re
import pandas as pd

# Lazy spaCy load to improve startup time
_nlp = None
def _nlp_en():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp

from .constants import ACTION_PATTERNS, ACTION_VERBS


def _is_action_item_spacy(line: str) -> bool:
    """Rule-lite NLP check for action-y sentences."""
    doc = _nlp_en()(line)
    for token in doc:
        # Root verb matches our action verbs OR a modal/root that lemmatizes to one
        if token.dep_ == "ROOT" and token.lemma_.lower() in ACTION_VERBS:
            return True
        if token.tag_ in ("MD", "VBP", "VB") and token.dep_ == "ROOT" and token.lemma_.lower() in ACTION_VERBS:
            return True
    return False


def find_action_items_with_speakers(speaker_blocks: Iterable, keywords: Iterable[str]) -> pd.DataFrame:
    """
    Scan speaker-attributed lines and return a DataFrame with probable action items.
    Expected input: iterable of (speaker, line) tuples.
    """
    rows = []

    # Normalize keywords, strip empties
    kw = [k.strip().lower() for k in keywords if k and k.strip()]

    for speaker, line in speaker_blocks:
        line_clean = (line or "").strip()
        if not line_clean:
            continue

        keyword_match = any(k in line_clean.lower() for k in kw)
        regex_match = any(re.search(p, line_clean, re.IGNORECASE) for p in ACTION_PATTERNS)
        spacy_match = _is_action_item_spacy(line_clean)

        if keyword_match or regex_match or spacy_match:
            item_type = "Confirmed"
        else:
            # Fallback heuristic: has a verb or soft cue
            doc = _nlp_en()(line_clean)
            has_verb = any(tok.pos_ == "VERB" for tok in doc)
            has_soft_cue = re.search(r"\b(I|We|Let\'s|Can|Should|Maybe|Please|Need)\b", line_clean, re.IGNORECASE)
            if has_verb or has_soft_cue:
                item_type = "Possible"
            else:
                continue

        rows.append({
            "Action Item": line_clean,
            "Type": item_type,
            # Uncomment if speaker is needed:
            # "Speaker": speaker,
        })

    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Action Item", "Type"])

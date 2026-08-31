import os
import re

def normalize_phoneme(phoneme: str) -> str:
    """
    Remove lexical stress digits from the end of vowel phonemes.
    E.g., 'AO0' -> 'AO', 'K' -> 'K'
    """
    return re.sub(r'\d+$', '', phoneme)

def ensure_dir(path: str):
    """Ensure that the given directory path exists."""
    os.makedirs(path, exist_ok=True)

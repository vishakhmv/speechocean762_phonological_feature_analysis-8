import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "results")
SCORES_PATH = os.path.join(BASE_DIR, "scores.json")
FEATURES_PATH = os.path.join(BASE_DIR, "features.json")

PLOT_DPI = 300
PLOT_COLOR = '#4C72B0'

VALID_SCORES = {round(x * 0.1, 1) for x in range(21)}

PLACES = [
    "BILABIAL", "LABIODENTAL", "DENTAL", "ALVEOLAR",
    "POSTALVEOLAR", "PALATAL", "VELAR", "GLOTTAL"
]

MANNERS = [
    "STOP", "FRICATIVE", "AFFRICATE", "NASAL", "LIQUID", "GLIDE"
]

VOICING = ["VOICED", "UNVOICED"]

CONSONANT_FEATURES = VOICING + MANNERS + PLACES


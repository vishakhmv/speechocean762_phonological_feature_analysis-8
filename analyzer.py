import json
import logging
import os
from collections import defaultdict
from typing import Dict, Tuple, Any

from config import (
    SCORES_PATH, FEATURES_PATH, OUTPUT_DIR, 
    VALID_SCORES, CONSONANT_FEATURES, PLACES, MANNERS
)
from utils import normalize_phoneme, ensure_dir
from plotter import export_histogram

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_data() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Safely load the features mapping and the scores dataset."""
    try:
        with open(FEATURES_PATH, 'r', encoding='utf-8') as f:
            features = json.load(f)
        with open(SCORES_PATH, 'r', encoding='utf-8') as f:
            scores = json.load(f)
        return features, scores
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading datasets: {e}")
        raise

def run_analysis() -> None:
    """Main analysis logic to process data and generate results."""
    logging.info("Loading data...")
    features_map, scores_data = load_data()
    
    import shutil
    out_dir = os.path.join(OUTPUT_DIR, "mispronunciations")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir, ignore_errors=True)
        
    consonant_mispro_hists: Dict[str, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
    
    stats = {
        "utterances": 0,
        "words": 0,
        "mispronunciations_processed": 0,
        "missing_can_phones": 0,
        "missing_pron_phones": 0,
        "skipped_invalid_score": 0,
        "skipped_invalid_index": 0
    }
    
    def process_word(word_data: Dict[str, Any]) -> None:
        stats["words"] += 1
        if "phones-accuracy" not in word_data:
            return
            
        accuracies = word_data["phones-accuracy"]
                        
        if "mispronunciations" in word_data:
            for mispro in word_data["mispronunciations"]:
                stats["mispronunciations_processed"] += 1
                can_p_raw = mispro.get("canonical-phone")
                pron_p_raw = mispro.get("pronounced-phone")
                idx = mispro.get("index")
                
                if can_p_raw is None or pron_p_raw is None or idx is None:
                    continue
                    
                if idx < 0 or idx >= len(accuracies):
                    stats["skipped_invalid_index"] += 1
                    continue
                    
                score = accuracies[idx]
                if score not in VALID_SCORES:
                    stats["skipped_invalid_score"] += 1
                    continue
                    
                can_p = normalize_phoneme(can_p_raw)
                pron_p = normalize_phoneme(pron_p_raw)
                
                can_missing = can_p not in features_map
                pron_missing = pron_p not in features_map
                
                if can_missing:
                    stats["missing_can_phones"] += 1
                if pron_missing:
                    stats["missing_pron_phones"] += 1
                    
                if can_missing or pron_missing:
                    continue
                    
                can_f = features_map[can_p]
                pron_f = features_map[pron_p]
                
                can_type = can_f.get("TYPE")
                if can_type == "C":
                    # Voicing comparison: attribute error based on canonical consonant voicing
                    if can_f.get("VOICE") != pron_f.get("VOICE"):
                        if can_f.get("VOICE") == 1.0:
                            consonant_mispro_hists["VOICED"][score] += 1
                        else:
                            consonant_mispro_hists["UNVOICED"][score] += 1
                        
                    # Place of articulation: attribute error to target place
                    can_place = next((p for p in PLACES if can_f.get(p) == 1.0), None)
                    pron_place = next((p for p in PLACES if pron_f.get(p) == 1.0), None)
                    if can_place and pron_place and can_place != pron_place:
                        consonant_mispro_hists[can_place][score] += 1
                        
                    # Manner of articulation: attribute error to target manner
                    can_manner = next((m for m in MANNERS if can_f.get(m) == 1.0), None)
                    pron_manner = next((m for m in MANNERS if pron_f.get(m) == 1.0), None)
                    if can_manner and pron_manner and can_manner != pron_manner:
                        consonant_mispro_hists[can_manner][score] += 1

    logging.info("Processing phonemes and aggregating scores...")
    for utterance_id, utterance_data in scores_data.items():
        stats["utterances"] += 1
        if stats["utterances"] % 1000 == 0:
            logging.info(f"Processed {stats['utterances']} utterances...")
            
        if "words" in utterance_data:
            for word in utterance_data["words"]:
                process_word(word)
                
    logging.info("Exporting results and generating validation summary...")
    export_results(consonant_mispro_hists, stats)
    logging.info(f"Analysis complete. Results saved to {OUTPUT_DIR}")

def export_results(
    consonant_mispro_hists: Dict[str, Dict[float, int]],
    stats: Dict[str, int]
) -> None:
    """Generate the output directory structure, write validations and export artifacts."""
    
    summary_lines = [
        "==================================================",
        "DATASET SUMMARY",
        "==================================================",
        f"Utterances processed: {stats['utterances']}",
        f"Words processed:      {stats['words']}",
        f"Mispronunciations:    {stats['mispronunciations_processed']}",
        f"Missing can. phones:  {stats['missing_can_phones']}",
        f"Missing pron. phones: {stats['missing_pron_phones']}",
        f"Skipped (inv score):  {stats['skipped_invalid_score']}",
        f"Skipped (inv index):  {stats['skipped_invalid_index']}",
        "",
        "==================================================",
        "HISTOGRAM EXPORT",
        "==================================================",
        ""
    ]
    
    csv_count = 0
    png_count = 0

    for f_name in CONSONANT_FEATURES:
        hist = consonant_mispro_hists[f_name]
        dir_path = os.path.join(OUTPUT_DIR, "mispronunciations", "consonants", f_name)
        ensure_dir(dir_path)
        base_name = f_name.lower()
        csv_path = os.path.join(dir_path, f"{base_name}.csv")
        png_path = os.path.join(dir_path, f"{base_name}.png")
        
        export_histogram(hist, csv_path, png_path, f"Consonant Mispronunciation: {f_name}")
        csv_count += 1
        png_count += 1
        
    summary_lines.insert(11, f"CSV files generated:  {csv_count}")
    summary_lines.insert(12, f"PNG files generated:  {png_count}")

    summary_path = os.path.join(OUTPUT_DIR, "validation_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))


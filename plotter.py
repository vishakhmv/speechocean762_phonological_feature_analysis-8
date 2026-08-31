import pandas as pd
import matplotlib.pyplot as plt
import os
import math
import logging
from typing import Dict

from config import VALID_SCORES, PLOT_DPI, PLOT_COLOR

def export_histogram(counts: Dict[float, int], csv_path: str, png_path: str, title: str) -> None:
    """
    Given a dictionary of {score: count}, generates a CSV and a PNG bar chart.
    Ensures all expected score bins are present and sorted ascending.
    """
    complete_counts = {score: counts.get(score, 0) for score in VALID_SCORES}
    
    df = pd.DataFrame(list(complete_counts.items()), columns=["Score", "Count"])
    
    df = df.sort_values(by="Score", ascending=True)
    
    total_count = df["Count"].sum()
    if total_count > 0:
        df["Percentage"] = (df["Count"] / total_count) * 100
        pct_sum = df["Percentage"].sum()
        if not math.isclose(pct_sum, 100.0, rel_tol=1e-5):
            logging.warning(f"Validation Error: Percentages in {csv_path} sum to {pct_sum}, not 100%.")
    else:
        df["Percentage"] = 0.0
        
    df.to_csv(csv_path, index=False)
    
    plt.figure(figsize=(10, 6), dpi=PLOT_DPI)
    
    plt.bar(df["Score"].astype(str), df["Count"], color=PLOT_COLOR, edgecolor='black', alpha=0.7, label='Count')
    
    plt.plot(df["Score"].astype(str), df["Count"], color='red', marker='o', linewidth=2, label='Trend')
    
    plt.title(title)
    plt.xlabel("Pronunciation Score")
    plt.ylabel("Count")
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(png_path)
    plt.close()

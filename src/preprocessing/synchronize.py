"""
synchronize.py (updated)
----------------
Merges all cleaned data sources onto one shared timeline:
  - electron flux (5-min cadence)   <- master timeline
  - proton flux   (5-min cadence)
  - xray flux     (1-min cadence)
  - OMNI data     (hourly cadence)

Strategy: electron flux has the timeline we care about (it's our main
target variable), so we keep its timestamps as the master, and merge in
the most recent reading from each other source at or before that time
(merge_asof, direction="backward").

Input : datasets/processed/electron_flux_clean.csv
        datasets/processed/proton_flux_clean.csv
        datasets/processed/xray_flux_clean.csv
        datasets/processed/omni_clean.csv
Output: datasets/processed/merged_dataset.csv
"""

import pandas as pd
import os

PROCESSED_DIR = os.path.join("datasets", "processed")

PATHS = {
    "electron": os.path.join(PROCESSED_DIR, "electron_flux_clean.csv"),
    "proton": os.path.join(PROCESSED_DIR, "proton_flux_clean.csv"),
    "xray": os.path.join(PROCESSED_DIR, "xray_flux_clean.csv"),
    "omni": os.path.join(PROCESSED_DIR, "omni_clean.csv"),
}
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "merged_dataset.csv")


def load_and_prepare(path, name):
    """Load a cleaned CSV and ensure time_tag is timezone-aware UTC."""
    df = pd.read_csv(path, parse_dates=["time_tag"])
    if df["time_tag"].dt.tz is None:
        df["time_tag"] = df["time_tag"].dt.tz_localize("UTC")
    df = df.sort_values("time_tag").reset_index(drop=True)
    print(f"{name}: {df.shape[0]} rows, range {df['time_tag'].min()} to {df['time_tag'].max()}")
    return df


def merge_all(electron_df, proton_df, xray_df, omni_df):
    """Use electron flux timestamps as the master timeline, and merge in the
    most recent reading from each other source at or before that timestamp."""

    merged = electron_df.copy()

    for name, df in [("proton", proton_df), ("xray", xray_df), ("omni", omni_df)]:
        merged = pd.merge_asof(
            merged.sort_values("time_tag"),
            df.sort_values("time_tag"),
            on="time_tag",
            direction="backward"
        )
        print(f"After merging {name}: {merged.shape}")

    return merged


if __name__ == "__main__":
    electron_df = load_and_prepare(PATHS["electron"], "Electron flux")
    proton_df = load_and_prepare(PATHS["proton"], "Proton flux")
    xray_df = load_and_prepare(PATHS["xray"], "X-ray flux")
    omni_df = load_and_prepare(PATHS["omni"], "OMNI data")

    for name, df in [("proton", proton_df), ("xray", xray_df), ("omni", omni_df)]:
        overlap_start = max(electron_df["time_tag"].min(), df["time_tag"].min())
        overlap_end = min(electron_df["time_tag"].max(), df["time_tag"].max())
        if overlap_start > overlap_end:
            print(f"WARNING: No overlap between electron flux and {name} data!")
        else:
            print(f"Overlap with {name}: {overlap_start} to {overlap_end}")

    merged_df = merge_all(electron_df, proton_df, xray_df, omni_df)

    merged_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved merged dataset to: {OUTPUT_PATH}")
    print(f"Final shape: {merged_df.shape}")
    print("\nMissing values per column:")
    print(merged_df.isna().sum())
    print("\nSample rows:")
    print(merged_df.head())
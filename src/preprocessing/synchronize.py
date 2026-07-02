"""
synchronize.py
----------------
Merges the cleaned electron flux data (5-min cadence) with the cleaned OMNI
data (hourly cadence) onto one shared timeline.

Strategy: electron flux has the finer resolution, so we keep its timestamps
as the master timeline, and forward-fill the hourly OMNI values onto it
(since OMNI values are constant within each hour anyway).

Input : datasets/processed/electron_flux_clean.csv
        datasets/processed/omni_clean.csv
Output: datasets/processed/merged_dataset.csv
"""

import pandas as pd
import os

PROCESSED_DIR = os.path.join("datasets", "processed")

FLUX_PATH = os.path.join(PROCESSED_DIR, "electron_flux_clean.csv")
OMNI_PATH = os.path.join(PROCESSED_DIR, "omni_clean.csv")
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "merged_dataset.csv")


def load_data():
    flux_df = pd.read_csv(FLUX_PATH, parse_dates=["time_tag"])
    omni_df = pd.read_csv(OMNI_PATH, parse_dates=["time_tag"])

    if flux_df["time_tag"].dt.tz is None:
        flux_df["time_tag"] = flux_df["time_tag"].dt.tz_localize("UTC")
    if omni_df["time_tag"].dt.tz is None:
        omni_df["time_tag"] = omni_df["time_tag"].dt.tz_localize("UTC")

    print(f"Electron flux: {flux_df.shape[0]} rows, range {flux_df['time_tag'].min()} to {flux_df['time_tag'].max()}")
    print(f"OMNI data:     {omni_df.shape[0]} rows, range {omni_df['time_tag'].min()} to {omni_df['time_tag'].max()}")

    return flux_df, omni_df


def merge_on_timeline(flux_df, omni_df):
    """Use electron flux timestamps as the master timeline, and merge in the
    most recent OMNI reading at or before each flux timestamp."""

    flux_df = flux_df.sort_values("time_tag")
    omni_df = omni_df.sort_values("time_tag")

    merged = pd.merge_asof(
        flux_df,
        omni_df,
        on="time_tag",
        direction="backward"
    )

    return merged


if __name__ == "__main__":
    flux_df, omni_df = load_data()

    overlap_start = max(flux_df["time_tag"].min(), omni_df["time_tag"].min())
    overlap_end = min(flux_df["time_tag"].max(), omni_df["time_tag"].max())

    if overlap_start > overlap_end:
        print("\nWARNING: No overlapping time range between electron flux and OMNI data!")
        print("The merge will produce empty/NaN OMNI columns for all rows.")
    else:
        print(f"\nOverlap window: {overlap_start} to {overlap_end}")

    merged_df = merge_on_timeline(flux_df, omni_df)

    merged_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved merged dataset to: {OUTPUT_PATH}")
    print(f"Final shape: {merged_df.shape}")
    print("\nMissing values per column:")
    print(merged_df.isna().sum())
    print("\nSample rows:")
    print(merged_df.head())
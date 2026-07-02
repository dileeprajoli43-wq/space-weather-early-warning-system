"""
feature_engineering.py
----------------
Builds engineered features from the merged electron flux + OMNI dataset,
ready for model training.

Input : datasets/processed/merged_dataset.csv
Output: datasets/processed/feature_matrix.csv
"""

import pandas as pd
import os

PROCESSED_DIR = os.path.join("datasets", "processed")
INPUT_PATH = os.path.join(PROCESSED_DIR, "merged_dataset.csv")
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "feature_matrix.csv")

# Columns we'll build rolling/lag features for.
# Pick the flux channels with the fewest missing values, plus key OMNI storm indicators.
TARGET_COLS = ["flux_134keV", "flux_79keV", "flux_865keV"]
STORM_COLS = ["Kp_index", "Dst_index_nT", "AE_index_nT", "BZ_nT"]

FEATURE_COLS = TARGET_COLS + STORM_COLS

# Rolling windows expressed in number of rows.
# Data is at 5-minute cadence, so:
#   3 rows  = 15 minutes
#   12 rows = 1 hour
#   36 rows = 3 hours
ROLLING_WINDOWS = {
    "15min": 3,
    "1hr": 12,
    "3hr": 36,
}

LAG_STEPS = [1, 2, 3, 6, 12]  # 5min, 10min, 15min, 30min, 1hr behind


def load_merged():
    df = pd.read_csv(INPUT_PATH, parse_dates=["time_tag"])
    df = df.sort_values("time_tag").reset_index(drop=True)
    print(f"Loaded merged dataset: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def add_rolling_features(df):
    for col in FEATURE_COLS:
        if col not in df.columns:
            continue
        for label, window in ROLLING_WINDOWS.items():
            df[f"{col}_rollmean_{label}"] = df[col].rolling(window=window, min_periods=1).mean()
            df[f"{col}_rollstd_{label}"] = df[col].rolling(window=window, min_periods=1).std()
            df[f"{col}_rollmax_{label}"] = df[col].rolling(window=window, min_periods=1).max()
            df[f"{col}_rollmin_{label}"] = df[col].rolling(window=window, min_periods=1).min()
    return df


def add_lag_features(df):
    for col in FEATURE_COLS:
        if col not in df.columns:
            continue
        for lag in LAG_STEPS:
            df[f"{col}_lag{lag}"] = df[col].shift(lag)
    return df


def add_rate_of_change(df):
    for col in FEATURE_COLS:
        if col not in df.columns:
            continue
        df[f"{col}_roc"] = df[col].diff()
    return df


def add_ema(df, span=12):
    for col in FEATURE_COLS:
        if col not in df.columns:
            continue
        df[f"{col}_ema"] = df[col].ewm(span=span, adjust=False).mean()
    return df


if __name__ == "__main__":
    df = load_merged()

    df = add_rolling_features(df).copy()
    df = add_lag_features(df).copy()
    df = add_rate_of_change(df).copy()
    df = add_ema(df).copy()

    # Drop the first few rows where lag features are NaN (no prior data to lag from)
    before = len(df)
    df = df.dropna(subset=[f"{FEATURE_COLS[0]}_lag{max(LAG_STEPS)}"]).reset_index(drop=True)
    after = len(df)
    print(f"Dropped {before - after} rows with insufficient history for lag features.")

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved feature matrix to: {OUTPUT_PATH}")
    print(f"Final shape: {df.shape}")
    print(f"Total columns: {len(df.columns)}")
    print("\nSample of new feature columns:")
    print([c for c in df.columns if "roll" in c or "lag" in c or "roc" in c or "ema" in c][:10])
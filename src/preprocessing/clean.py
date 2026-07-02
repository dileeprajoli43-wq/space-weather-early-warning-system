"""
clean.py
----------------
Cleans and reshapes the raw GOES electron flux data.

Input : datasets/raw/goes/electron_flux_*.csv   (long format: one row per timestamp+energy channel)
Output: datasets/processed/electron_flux_clean.csv (wide format: one row per timestamp, one column per energy channel)
"""

import pandas as pd
import glob
import os

RAW_DIR = os.path.join("datasets", "raw", "goes")
PROCESSED_DIR = os.path.join("datasets", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)


def load_latest_raw_file():
    """Find the most recently saved raw electron flux CSV."""
    files = glob.glob(os.path.join(RAW_DIR, "electron_flux_*.csv"))
    if not files:
        raise FileNotFoundError(f"No raw electron flux files found in {RAW_DIR}")
    latest_file = max(files, key=os.path.getctime)
    print(f"Loading raw file: {latest_file}")
    return pd.read_csv(latest_file)


def clean_data(df):
    """Basic cleaning: drop nulls, remove bad sensor values, fix dtypes."""
    before = len(df)

    # Drop rows with missing flux or energy values
    df = df.dropna(subset=["flux", "energy", "time_tag"])

    # Remove known bad/error sensor readings (NOAA sometimes uses negative
    # or extremely large placeholder values for missing/error data)
    df = df[(df["flux"] > 0) & (df["flux"] < 1e6)]

    # Ensure correct dtypes
    df["time_tag"] = pd.to_datetime(df["time_tag"])
    df["flux"] = df["flux"].astype(float)

    after = len(df)
    print(f"Cleaned rows: {before} -> {after} (removed {before - after})")
    return df


def pivot_to_wide(df):
    """Reshape from long format (one row per timestamp+energy) to wide format
    (one row per timestamp, one column per energy channel)."""

    # If there are multiple satellites, keep only one to avoid duplicate
    # timestamps colliding during pivot. Check unique satellites first.
    satellites = df["satellite"].unique()
    if len(satellites) > 1:
        chosen_sat = satellites[0]
        print(f"Multiple satellites found {list(satellites)}, using satellite {chosen_sat} only.")
        df = df[df["satellite"] == chosen_sat]

    wide_df = df.pivot_table(
        index="time_tag",
        columns="energy",
        values="flux",
        aggfunc="mean"  # in case of duplicate entries at same timestamp+energy
    )

    # Clean up column names, e.g. "134 keV" -> "flux_134keV"
    wide_df.columns = [f"flux_{str(c).replace(' ', '').replace('keV', 'keV')}" for c in wide_df.columns]
    wide_df = wide_df.reset_index()
    wide_df = wide_df.sort_values("time_tag").reset_index(drop=True)

    print(f"Wide format shape: {wide_df.shape}")
    print("Columns:", list(wide_df.columns))
    return wide_df


if __name__ == "__main__":
    raw_df = load_latest_raw_file()
    cleaned_df = clean_data(raw_df)
    wide_df = pivot_to_wide(cleaned_df)

    output_path = os.path.join(PROCESSED_DIR, "electron_flux_clean.csv")
    wide_df.to_csv(output_path, index=False)
    print(f"\nSaved cleaned wide-format data to: {output_path}")
    print("\nSample rows:")
    print(wide_df.head())
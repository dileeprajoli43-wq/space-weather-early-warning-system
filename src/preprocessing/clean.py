"""
clean.py (updated)
----------------
Cleans and reshapes raw GOES flux data (electron, proton, xray) from long
format (one row per timestamp+channel) to wide format (one row per
timestamp, one column per channel).

Input : datasets/raw/goes/{electron,proton,xray}_flux_*.csv
Output: datasets/processed/{electron,proton,xray}_flux_clean.csv
"""

import pandas as pd
import glob
import os

RAW_DIR = os.path.join("datasets", "raw", "goes")
PROCESSED_DIR = os.path.join("datasets", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Each entry: (raw file prefix, output name, channel column to pivot on)
DATASETS = {
    "electron": {"prefix": "electron_flux", "channel_col": "energy", "out": "electron_flux_clean.csv"},
    "proton":   {"prefix": "proton_flux",   "channel_col": "channel", "out": "proton_flux_clean.csv"},
    "xray":     {"prefix": "xray_flux",     "channel_col": "energy", "out": "xray_flux_clean.csv"},
}


def load_latest_raw_file(prefix):
    files = glob.glob(os.path.join(RAW_DIR, f"{prefix}_*.csv"))
    if not files:
        raise FileNotFoundError(f"No raw files found for prefix '{prefix}' in {RAW_DIR}")
    latest_file = max(files, key=os.path.getctime)
    print(f"Loading raw file: {latest_file}")
    return pd.read_csv(latest_file)


def clean_data(df):
    """Basic cleaning: drop nulls, remove bad sensor values, fix dtypes."""
    before = len(df)
    df = df.dropna(subset=["flux", "time_tag"])
    df = df[(df["flux"] > 0) & (df["flux"] < 1e9)]
    df["time_tag"] = pd.to_datetime(df["time_tag"])
    df["flux"] = df["flux"].astype(float)
    after = len(df)
    print(f"Cleaned rows: {before} -> {after} (removed {before - after})")
    return df


def pivot_to_wide(df, channel_col, value_prefix):
    """Reshape from long format to wide format, one column per channel."""

    if "satellite" in df.columns:
        satellites = df["satellite"].unique()
        if len(satellites) > 1:
            chosen_sat = satellites[0]
            print(f"Multiple satellites found {list(satellites)}, using satellite {chosen_sat} only.")
            df = df[df["satellite"] == chosen_sat]

    wide_df = df.pivot_table(
        index="time_tag",
        columns=channel_col,
        values="flux",
        aggfunc="mean"
    )

    def clean_colname(c):
        return f"{value_prefix}_{str(c).replace(' ', '').replace('-', '_')}"

    wide_df.columns = [clean_colname(c) for c in wide_df.columns]
    wide_df = wide_df.reset_index()
    wide_df = wide_df.sort_values("time_tag").reset_index(drop=True)

    print(f"Wide format shape: {wide_df.shape}")
    print("Columns:", list(wide_df.columns))
    return wide_df


if __name__ == "__main__":
    for name, info in DATASETS.items():
        print(f"\n=== Cleaning {name} data ===")
        try:
            raw_df = load_latest_raw_file(info["prefix"])
            cleaned_df = clean_data(raw_df)
            wide_df = pivot_to_wide(cleaned_df, info["channel_col"], value_prefix=info["prefix"])

            output_path = os.path.join(PROCESSED_DIR, info["out"])
            wide_df.to_csv(output_path, index=False)
            print(f"Saved to: {output_path}")
        except Exception as e:
            print(f"Failed to clean {name} data: {e}")

    print("\nDone. All flux datasets cleaned.")
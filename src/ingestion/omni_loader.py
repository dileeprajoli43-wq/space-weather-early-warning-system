"""
omni_loader.py
----------------
Parses the raw OMNIWeb data file (space-separated columns, numbered headers)
into a clean CSV with proper column names, a real timestamp, and fill-value
handling.

Input : datasets/raw/omni/omni_data.csv
Output: datasets/processed/omni_clean.csv
"""

import pandas as pd
import os

RAW_PATH = os.path.join("datasets", "raw", "omni", "omni_data.csv")
PROCESSED_DIR = os.path.join("datasets", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Map OMNIWeb's numbered columns to real variable names
COLUMN_MAP = {
    "1": "spacecraft_id",
    "2": "scalar_B_nT",
    "3": "BX_nT",
    "4": "BY_nT",
    "5": "BZ_nT",
    "6": "sw_temperature_K",
    "7": "sw_proton_density_Ncm3",
    "8": "sw_plasma_speed_kms",
    "9": "flow_pressure_nPa",
    "10": "Kp_index",
    "11": "Dst_index_nT",
    "12": "AE_index_nT",
}

# OMNI2 fill/error values that mean "missing data" for each variable type.
# We'll replace anything matching these with NaN.
FILL_VALUES = [999.9, 9999.0, 9999.99, 99999.0, 999999.0, 9999999.0]


def load_raw():
    """Load the raw whitespace-delimited OMNI file, skipping any stray
    footer/text lines that may have been copy-pasted in along with the data
    (e.g. 'If you have questions...' from the OMNIWeb page)."""
    df = pd.read_csv(RAW_PATH, sep=r"\s+")

    before = len(df)
    # Keep only rows where YEAR looks like a real 4-digit year (numeric)
    df = df[pd.to_numeric(df["YEAR"], errors="coerce").notna()].copy()
    after = len(df)
    if before != after:
        print(f"Dropped {before - after} junk/footer rows that weren't real data.")

    print(f"Loaded raw OMNI file: {df.shape[0]} rows, {df.shape[1]} columns")
    print("Raw columns:", list(df.columns))
    return df


def rename_columns(df):
    """Rename numbered columns to descriptive names."""
    df = df.rename(columns=COLUMN_MAP)
    return df


def build_timestamp(df):
    """Combine YEAR, DOY (day of year), HR (hour) into one datetime column."""
    df["time_tag"] = pd.to_datetime(
        df["YEAR"].astype(str) + df["DOY"].astype(str).str.zfill(3) + df["HR"].astype(str).str.zfill(2),
        format="%Y%j%H",
        utc=True
    )
    df = df.drop(columns=["YEAR", "DOY", "HR"])
    return df


def clean_values(df):
    """Replace OMNI fill/error values with NaN, and fix Kp scaling."""
    numeric_cols = [c for c in df.columns if c not in ("time_tag", "spacecraft_id")]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        # Replace known fill values with NaN
        df.loc[df[col].isin(FILL_VALUES), col] = pd.NA
        # Also catch anything absurdly large as a fill value (safety net)
        df.loc[df[col] > 90000, col] = pd.NA

    # Kp index is stored as Kp*10 in OMNI2 (e.g. 7 -> Kp = 0.7)
    df["Kp_index"] = df["Kp_index"] / 10.0

    # Drop the spacecraft ID metadata column, not needed for modeling
    if "spacecraft_id" in df.columns:
        df = df.drop(columns=["spacecraft_id"])

    return df


if __name__ == "__main__":
    raw_df = load_raw()
    df = rename_columns(raw_df)
    df = build_timestamp(df)
    df = clean_values(df)

    df = df.sort_values("time_tag").reset_index(drop=True)

    # Reorder so time_tag is first
    cols = ["time_tag"] + [c for c in df.columns if c != "time_tag"]
    df = df[cols]

    output_path = os.path.join(PROCESSED_DIR, "omni_clean.csv")
    df.to_csv(output_path, index=False)

    print(f"\nSaved cleaned OMNI data to: {output_path}")
    print(f"Final shape: {df.shape}")
    print("\nMissing values per column:")
    print(df.isna().sum())
    print("\nSample rows:")
    print(df.head())
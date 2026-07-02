"""
goes_loader.py
----------------
Fetches real-time energetic electron flux data from NOAA SWPC (GOES satellites)
and saves it as a clean CSV into datasets/raw/.

Data source: https://services.swpc.noaa.gov/json/goes/primary/differential-electrons-7-day.json
"""

import requests
import pandas as pd
from datetime import datetime
import os

# NOAA SWPC endpoint for GOES differential electron flux (7-day rolling window)
URL = "https://services.swpc.noaa.gov/json/goes/primary/differential-electrons-7-day.json"

# Where to save the output
OUTPUT_DIR = os.path.join("datasets", "raw", "goes")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_electron_flux():
    """Fetch raw JSON data from NOAA and return it as a pandas DataFrame."""
    print(f"Fetching data from: {URL}")
    response = requests.get(URL, timeout=30)
    response.raise_for_status()  # raises an error if request failed

    data = response.json()
    df = pd.DataFrame(data)

    print(f"Fetched {len(df)} rows.")
    print("Columns found:", list(df.columns))
    return df


def clean_and_save(df):
    """Do minimal cleanup and save to CSV with a timestamped filename."""
    # Convert time column to proper datetime if present
    time_col = "time_tag" if "time_tag" in df.columns else df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    # Sort by time
    df = df.sort_values(by=time_col).reset_index(drop=True)

    # Save with today's date in filename so you keep a history of pulls
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"electron_flux_{today_str}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    df.to_csv(filepath, index=False)
    print(f"Saved cleaned data to: {filepath}")
    return filepath


if __name__ == "__main__":
    raw_df = fetch_electron_flux()
    print("\nSample rows:")
    print(raw_df.head())

    saved_path = clean_and_save(raw_df)
    print(f"\nDone. File saved at: {saved_path}")
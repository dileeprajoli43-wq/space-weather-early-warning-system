"""
goes_loader.py (updated)
----------------
Fetches real-time flux data from NOAA SWPC (GOES satellites) for electrons,
protons, and X-rays, and saves each as a clean CSV into datasets/raw/.

Data sources:
  Electrons: https://services.swpc.noaa.gov/json/goes/primary/differential-electrons-7-day.json
  Protons:   https://services.swpc.noaa.gov/json/goes/primary/differential-protons-7-day.json
  X-rays:    https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json
"""

import requests
import pandas as pd
from datetime import datetime
import os

# Each entry: (name, url, subfolder)
SOURCES = {
    "electron": {
        "url": "https://services.swpc.noaa.gov/json/goes/primary/differential-electrons-7-day.json",
        "folder": os.path.join("datasets", "raw", "goes"),
        "prefix": "electron_flux",
    },
    "proton": {
        "url": "https://services.swpc.noaa.gov/json/goes/primary/differential-protons-7-day.json",
        "folder": os.path.join("datasets", "raw", "goes"),
        "prefix": "proton_flux",
    },
    "xray": {
        "url": "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json",
        "folder": os.path.join("datasets", "raw", "goes"),
        "prefix": "xray_flux",
    },
}


def fetch_data(url):
    """Fetch raw JSON data from NOAA and return it as a pandas DataFrame."""
    print(f"Fetching data from: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
    print(f"Fetched {len(df)} rows.")
    print("Columns found:", list(df.columns))
    return df


def clean_and_save(df, folder, prefix):
    """Sort by time and save to CSV with a dated filename."""
    os.makedirs(folder, exist_ok=True)

    time_col = "time_tag" if "time_tag" in df.columns else df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])
    df = df.sort_values(by=time_col).reset_index(drop=True)

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"{prefix}_{today_str}.csv"
    filepath = os.path.join(folder, filename)

    df.to_csv(filepath, index=False)
    print(f"Saved cleaned data to: {filepath}")
    return filepath


if __name__ == "__main__":
    for name, info in SOURCES.items():
        print(f"\n=== Fetching {name} data ===")
        try:
            raw_df = fetch_data(info["url"])
            print(raw_df.head())
            clean_and_save(raw_df, info["folder"], info["prefix"])
        except Exception as e:
            print(f"Failed to fetch {name} data: {e}")

    print("\nDone. All available flux datasets fetched.")
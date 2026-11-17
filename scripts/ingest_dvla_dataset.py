#!/usr/bin/env python3
"""DVLA UK Driving Licence Dataset Ingestion & Processing Script.

Downloads the Kaggle dataset 'qwikfix/dvla-driving-licence-dataset' via kagglehub,
processes the statistical tables (DRL0101 by age/gender, DRL0102 by postcode district),
and generates a normalized benchmark reference JSON for the platform.

Usage:
    python scripts/ingest_dvla_dataset.py
"""

import json
import os
import sys
import pandas as pd

DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "backend",
    "app",
    "data",
)
TARGET_JSON_PATH = os.path.join(DEFAULT_DATA_DIR, "dvla_benchmarks.json")


def ingest_dataset():
    print("=================================================================")
    print("[*] DVLA UK DRIVING LICENCE DATASET INGESTION (KaggleHub)")
    print("=================================================================")

    import kagglehub
    print("[*] Downloading latest version of 'qwikfix/dvla-driving-licence-dataset'...")
    dataset_dir = kagglehub.dataset_download("qwikfix/dvla-driving-licence-dataset")
    print(f"[+] Download path: {dataset_dir}")

    excel_file = os.path.join(dataset_dir, "Driving-licence-data-March2016.xls")
    if not os.path.exists(excel_file):
        # Look for any .xls in the directory
        for f in os.listdir(dataset_dir):
            if f.endswith(".xls") or f.endswith(".xlsx"):
                excel_file = os.path.join(dataset_dir, f)
                break

    if not os.path.exists(excel_file):
        print(f"[ERROR] Could not find Excel dataset file in: {dataset_dir}")
        return 1

    print(f"[*] Processing workbook: {excel_file}")

    # 1. Parse DRL0101 (Age and Gender)
    print("    -> Parsing Table DRL0101 (Age & Gender distributions)...")
    df_age_raw = pd.read_excel(excel_file, sheet_name="DRL0101", header=None)
    age_records = []
    total_prov = 0
    total_full = 0

    for idx in range(29, len(df_age_raw)):
        row = df_age_raw.iloc[idx].tolist()
        age_str = str(row[0]).strip()
        if age_str.isdigit() or age_str.endswith("+"):
            try:
                prov_m = int(row[1]) if pd.notna(row[1]) else 0
                prov_f = int(row[2]) if pd.notna(row[2]) else 0
                full_m = int(row[4]) if pd.notna(row[4]) else 0
                full_f = int(row[5]) if pd.notna(row[5]) else 0
                
                tot_p = prov_m + prov_f
                tot_f = full_m + full_f
                total_prov += tot_p
                total_full += tot_f

                age_records.append({
                    "age": age_str,
                    "provisional_male": prov_m,
                    "provisional_female": prov_f,
                    "provisional_total": tot_p,
                    "full_male": full_m,
                    "full_female": full_f,
                    "full_total": tot_f,
                })
            except Exception:
                pass

    # 2. Parse DRL0102 (Postcode Districts)
    print("    -> Parsing Table DRL0102 (Postcode District distributions)...")
    df_pc_raw = pd.read_excel(excel_file, sheet_name="DRL0102", header=None)
    postcode_districts = {}

    for idx in range(29, len(df_pc_raw)):
        row = df_pc_raw.iloc[idx].tolist()
        district = str(row[0]).strip().upper()
        if district and district != "NAN" and len(district) <= 6:
            try:
                prov_tot = int(row[3]) if pd.notna(row[3]) else 0
                full_tot = int(row[6]) if pd.notna(row[6]) else 0
                postcode_districts[district] = {
                    "provisional_total": prov_tot,
                    "full_total": full_tot,
                    "total_licences": prov_tot + full_tot,
                }
            except Exception:
                pass

    # Assemble Benchmark Output
    benchmark_data = {
        "dataset_name": "qwikfix/dvla-driving-licence-dataset",
        "jurisdiction": "United Kingdom (Great Britain)",
        "issuing_authority": "Driver and Vehicle Licensing Agency (DVLA)",
        "published_period": "March 2016",
        "summary": {
            "total_provisional_licences": total_prov,
            "total_full_licences": total_full,
            "total_licences_recorded": total_prov + total_full,
            "total_postcode_districts": len(postcode_districts),
            "age_brackets_count": len(age_records),
        },
        "age_distribution": age_records,
        "postcode_districts": postcode_districts,
    }

    os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
    with open(TARGET_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)

    print(f"[+] Successfully exported benchmark JSON: {TARGET_JSON_PATH}")
    print(f"    - Total Licences: {total_prov + total_full:,}")
    print(f"    - Postcode Districts: {len(postcode_districts):,}")
    print("=================================================================")
    print(">>> SUCCESS: DVLA Dataset Ingested and Benchmarks Ready <<<")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(ingest_dataset())

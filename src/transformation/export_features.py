"""
Export transformed dbt features from PostgreSQL to compressed Parquet file.
Serves as the training-ready feature store for ML & Deep Learning models.
"""

import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import psycopg2

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5433"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "turbofan_dw")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "features_fd001.parquet"


def export_features_to_parquet():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[*] Connecting to PostgreSQL ({POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB})...")

    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )

    query = "SELECT * FROM analytics.fct_turbofan_features ORDER BY engine_id, cycle;"
    print("[*] Fetching features from analytics.fct_turbofan_features...")
    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"[*] Successfully retrieved {len(df):,} records with {len(df.columns)} columns.")
    print(f"[*] Saving feature store to: {OUTPUT_FILE}")
    df.to_parquet(OUTPUT_FILE, index=False, engine="pyarrow", compression="snappy")

    size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"[OK] Export complete! Parquet file size: {size_mb:.2f} MB.")


if __name__ == "__main__":
    export_features_to_parquet()

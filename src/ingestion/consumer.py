"""
Kafka Telemetry Stream Consumer for NASA Turbofan C-MAPSS.
Consumes streaming events from Kafka and ingests into PostgreSQL raw table.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError
import psycopg2
from psycopg2.extras import execute_values

# Pastikan root directory ada di sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load environment variables
load_dotenv()

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "turbofan_dw")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Kafka Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_TELEMETRY", "turbofan_raw_telemetry")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "turbofan_pg_consumer_group")


def get_db_connection():
    """Membuat koneksi ke database PostgreSQL."""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def init_db():
    """Membuat schema dan tabel raw_turbofan_telemetry jika belum ada."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS raw_turbofan_telemetry (
        id SERIAL PRIMARY KEY,
        engine_id INT NOT NULL,
        cycle INT NOT NULL,
        setting_1 FLOAT8 NOT NULL,
        setting_2 FLOAT8 NOT NULL,
        setting_3 FLOAT8 NOT NULL,
        s_1 FLOAT8 NOT NULL,
        s_2 FLOAT8 NOT NULL,
        s_3 FLOAT8 NOT NULL,
        s_4 FLOAT8 NOT NULL,
        s_5 FLOAT8 NOT NULL,
        s_6 FLOAT8 NOT NULL,
        s_7 FLOAT8 NOT NULL,
        s_8 FLOAT8 NOT NULL,
        s_9 FLOAT8 NOT NULL,
        s_10 FLOAT8 NOT NULL,
        s_11 FLOAT8 NOT NULL,
        s_12 FLOAT8 NOT NULL,
        s_13 FLOAT8 NOT NULL,
        s_14 FLOAT8 NOT NULL,
        s_15 FLOAT8 NOT NULL,
        s_16 FLOAT8 NOT NULL,
        s_17 FLOAT8 NOT NULL,
        s_18 FLOAT8 NOT NULL,
        s_19 FLOAT8 NOT NULL,
        s_20 FLOAT8 NOT NULL,
        s_21 FLOAT8 NOT NULL,
        event_timestamp TIMESTAMPTZ NOT NULL,
        ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_engine_cycle UNIQUE (engine_id, cycle)
    );

    CREATE INDEX IF NOT EXISTS idx_engine_cycle ON raw_turbofan_telemetry (engine_id, cycle);
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
        conn.commit()
    print("[*] PostgreSQL table 'raw_turbofan_telemetry' ready.")


def insert_batch(conn, records: List[Dict[str, Any]]):
    """Melakukan bulk insert ke PostgreSQL menggunakan execute_values (sangat cepat)."""
    if not records:
        return

    insert_query = """
    INSERT INTO raw_turbofan_telemetry (
        engine_id, cycle, setting_1, setting_2, setting_3,
        s_1, s_2, s_3, s_4, s_5, s_6, s_7, s_8, s_9, s_10,
        s_11, s_12, s_13, s_14, s_15, s_16, s_17, s_18, s_19, s_20, s_21,
        event_timestamp
    ) VALUES %s
    ON CONFLICT (engine_id, cycle) DO NOTHING;
    """

    values = [
        (
            r["engine_id"], r["cycle"], r["setting_1"], r["setting_2"], r["setting_3"],
            r["s_1"], r["s_2"], r["s_3"], r["s_4"], r["s_5"], r["s_6"], r["s_7"],
            r["s_8"], r["s_9"], r["s_10"], r["s_11"], r["s_12"], r["s_13"], r["s_14"],
            r["s_15"], r["s_16"], r["s_17"], r["s_18"], r["s_19"], r["s_20"], r["s_21"],
            r["timestamp"]
        )
        for r in records
    ]

    with conn.cursor() as cur:
        execute_values(cur, insert_query, values)
    conn.commit()


def start_consumer(batch_size: int = 100, poll_timeout: float = 1.0):
    """
    Loop consumer untuk membaca data dari Kafka dan menyimpannya ke PostgreSQL.
    """
    init_db()

    consumer_config = {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": KAFKA_GROUP_ID,
        "auto.offset.reset": "earliest",  # Baca dari pesan terawal jika baru pertama kali start
        "enable.auto.commit": True,
    }

    consumer = Consumer(consumer_config)
    consumer.subscribe([KAFKA_TOPIC])

    print(f"[*] Subscribed to Kafka topic: {KAFKA_TOPIC}")
    print(f"[*] Consumer group: {KAFKA_GROUP_ID}")
    print(f"[*] Listening for incoming telemetry events (Batch size: {batch_size})...")

    conn = get_db_connection()
    buffer = []
    total_ingested = 0
    last_flush_time = time.time()

    try:
        while True:
            msg = consumer.poll(timeout=poll_timeout)

            if msg is None:
                # Flush sisa buffer jika waktu idle > 2 detik
                if buffer and (time.time() - last_flush_time > 2.0):
                    insert_batch(conn, buffer)
                    total_ingested += len(buffer)
                    print(f"[>] Ingested {len(buffer)} records to PostgreSQL. Total: {total_ingested:,}")
                    buffer.clear()
                    last_flush_time = time.time()
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"[!] Kafka error: {msg.error()}")
                    break

            # Parse JSON value
            try:
                record = json.loads(msg.value().decode("utf-8"))
                buffer.append(record)
            except Exception as e:
                print(f"[!] Failed to parse message JSON: {e}")
                continue

            # Jika buffer mencapai batch_size, simpan ke database
            if len(buffer) >= batch_size:
                insert_batch(conn, buffer)
                total_ingested += len(buffer)
                print(f"[>] Ingested batch of {len(buffer)} records to PostgreSQL. Total: {total_ingested:,}")
                buffer.clear()
                last_flush_time = time.time()

    except KeyboardInterrupt:
        print("\n[!] Consumer stopped by user.")
    finally:
        if buffer:
            insert_batch(conn, buffer)
            total_ingested += len(buffer)
            print(f"[>] Final flush: {len(buffer)} records inserted.")
        consumer.close()
        conn.close()
        print(f"[OK] Consumer cleanly closed. Total records stored: {total_ingested:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consume telemetry from Kafka to PostgreSQL.")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for DB insert (default: 100)")
    args = parser.parse_args()

    start_consumer(batch_size=args.batch_size)

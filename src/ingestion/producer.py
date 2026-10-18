"""
Kafka Telemetry Stream Producer for NASA Turbofan C-MAPSS.
Simulates real-time fleet operations by replaying engine degradation cycles.
"""

import os
import sys
import time
import argparse
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from confluent_kafka import Producer

# Import data contract
from src.ingestion.schemas import TurbofanTelemetry, RAW_DATA_COLUMNS

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_PATH = BASE_DIR / "data" / "raw" / "train_FD001.txt"
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_TELEMETRY", "turbofan_raw_telemetry")


def delivery_callback(err, msg):
    """Callback untuk melacak konfirmasi penerimaan pesan oleh Kafka Broker."""
    if err is not None:
        print(f"[!] Gagal mengirim pesan: {err}", file=sys.stderr)


def stream_telemetry(data_path: Path, delay: float = 0.02, limit: int = None):
    """
    Membaca dataset C-MAPSS dan melakukan streaming per siklus mesin.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan di: {data_path}. Jalankan download_data.py dulu.")

    print(f"[*] Membaca telemetry dari: {data_path}")
    df = pd.read_csv(data_path, sep=r"\s+", header=None, names=RAW_DATA_COLUMNS)

    # Urutkan berdasarkan cycle lalu engine_id (simulasi armada terbang serentak per siklus)
    df = df.sort_values(by=["cycle", "engine_id"]).reset_index(drop=True)
    total_records = len(df) if limit is None else min(limit, len(df))

    print(f"[*] Total {len(df):,} baris telemetry untuk {df['engine_id'].nunique()} mesin pesawat.")
    print(f"[*] Menghubungkan ke Kafka Broker: {KAFKA_BROKER}")
    print(f"[*] Target Topik: {KAFKA_TOPIC}")

    # Inisialisasi Producer
    producer_config = {
        "bootstrap.servers": KAFKA_BROKER,
        "client.id": "turbofan-producer",
        "acks": "1",  # Leader acknowledgment
    }
    producer = Producer(producer_config)

    print(f"[*] Memulai streaming ({total_records:,} events, delay: {delay}s)...")
    sent_count = 0
    start_time = time.time()

    try:
        for idx, row in df.iterrows():
            if limit and sent_count >= limit:
                break

            # Validasi data dengan Pydantic Schema
            record_dict = row.to_dict()
            telemetry_event = TurbofanTelemetry(**record_dict)

            # Kirim event ke Kafka
            producer.produce(
                topic=KAFKA_TOPIC,
                key=str(telemetry_event.engine_id),
                value=telemetry_event.model_dump_json().encode("utf-8"),
                callback=delivery_callback
            )

            # Layani callback pengiriman
            producer.poll(0)
            sent_count += 1

            if sent_count % 500 == 0:
                elapsed = time.time() - start_time
                eps = sent_count / elapsed if elapsed > 0 else 0
                print(f"[>] Terkirim {sent_count:,}/{total_records:,} events ({eps:.1f} events/detik)...")

            if delay > 0:
                time.sleep(delay)

    except KeyboardInterrupt:
        print("\n[!] Streaming dihentikan oleh user.")
    finally:
        print("[*] Melakukan flush sisa antrean pesan ke Kafka...")
        producer.flush()
        total_time = time.time() - start_time
        print(f"[OK] Streaming selesai. Total event terkirim: {sent_count:,} dalam {total_time:.2f} detik.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream NASA Turbofan telemetry to Apache Kafka.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="Path ke file txt dataset")
    parser.add_argument("--delay", type=float, default=0.01, help="Delay antar pesan (default: 0.01 detik)")
    parser.add_argument("--limit", type=int, default=None, help="Batas maksimal pesan (default: None, semua)")
    args = parser.parse_args()

    stream_telemetry(data_path=args.data, delay=args.delay, limit=args.limit)

"""
NASA C-MAPSS Turbofan Degradation Dataset Downloader.
Downloads and extracts raw benchmark files (FD001 - FD004) to data/raw/.
"""

import os
import shutil
import urllib.request
import zipfile
import tarfile
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

# Reliable mirror sources
DATA_ZIP_URLS = [
    # Official NASA Open Data Portal
    "https://data.nasa.gov/docs/legacy/CMAPSSData.zip",
    "https://ti.arc.nasa.gov/c/6/",
]

GITHUB_FALLBACK_BASE = "https://raw.githubusercontent.com/mapr-demos/predictive-maintenance/master/Dataset/CMAPSSData"

EXPECTED_FILES = [
    "train_FD001.txt",
    "test_FD001.txt",
    "RUL_FD001.txt",
]


def download_and_extract():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if files already exist
    all_exist = all((RAW_DATA_DIR / f).exists() for f in EXPECTED_FILES)
    if all_exist:
        print("[OK] Raw dataset files already present in data/raw/:")
        for f in EXPECTED_FILES:
            size_kb = (RAW_DATA_DIR / f).stat().st_size / 1024
            print(f"    - {f} ({size_kb:.1f} KB)")
        return

    download_success = False
    temp_archive = RAW_DATA_DIR / "temp_archive"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for url in DATA_ZIP_URLS:
        try:
            print(f"[*] Attempting ZIP download from: {url}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response, open(temp_archive, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

            if zipfile.is_zipfile(temp_archive):
                print("[*] Extracting ZIP archive...")
                with zipfile.ZipFile(temp_archive, "r") as zip_ref:
                    zip_ref.extractall(RAW_DATA_DIR)
                download_success = True
                break
            elif tarfile.is_tarfile(temp_archive):
                print("[*] Extracting TAR archive...")
                with tarfile.open(temp_archive, "r:*") as tar_ref:
                    tar_ref.extractall(RAW_DATA_DIR)
                download_success = True
                break
        except Exception as e:
            print(f"[!] Failed to download from {url}: {e}")
            if temp_archive.exists():
                temp_archive.unlink()

    if temp_archive.exists():
        temp_archive.unlink()

    # Fallback: Download individual files from GitHub mirror if zip extraction failed
    if not download_success:
        print("[*] Attempting fallback: downloading individual dataset files...")
        try:
            for filename in EXPECTED_FILES + ["readme.txt"]:
                file_url = f"{GITHUB_FALLBACK_BASE}/{filename}"
                print(f"[*] Fetching: {file_url}")
                req = urllib.request.Request(file_url, headers=headers)
                target_path = RAW_DATA_DIR / filename
                with urllib.request.urlopen(req, context=ctx, timeout=30) as response, open(target_path, "wb") as out_file:
                    shutil.copyfileobj(response, out_file)
            download_success = True
        except Exception as e:
            print(f"[!] Failed downloading individual files: {e}")

    if not download_success:
        raise RuntimeError("Failed to download NASA C-MAPSS dataset from all mirrors.")

    print("\n[OK] Successfully downloaded and extracted dataset into data/raw/!")
    for f in EXPECTED_FILES:
        target = RAW_DATA_DIR / f
        if target.exists():
            with open(target, "r") as file_obj:
                lines = sum(1 for _ in file_obj)
            size_kb = target.stat().st_size / 1024
            print(f"    - {f}: {lines:,} records ({size_kb:.1f} KB)")


if __name__ == "__main__":
    download_and_extract()

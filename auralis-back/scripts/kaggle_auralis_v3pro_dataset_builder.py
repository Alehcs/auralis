"""Kaggle one-cell builder for the V3 PRO processed dataset.

Kaggle sessions are interruptible, so the script restores processed tensors,
resumes the JSOC queue, and uploads progress before the runtime is likely to
stop. Re-running the cell resumes from ``download_log.json``.
"""

import os, sys, time, json, shutil, subprocess, zipfile, urllib.request
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime, timedelta
from pathlib import Path

# Dataset and sampling configuration.
KAGGLE_USERNAME  = 'alehhh'
DATASET_NAME     = 'auralis-magnetograms'
SAMPLE_HOURS     = 6
TARGET_SIZE      = 512
SSN_THRESHOLD    = 200.0
DATE_RANGES = [
    ("2008-01-01", "2010-04-30"),
    ("2010-05-01", "2018-12-31"),
    ("2019-01-01", "2020-12-31"),
    ("2021-01-01", "2026-04-30"),
]

# Kaggle working directories. These are separate from the local repository
# layout because the script runs inside Kaggle's transient filesystem.
BASE_DIR = Path('/kaggle/working/auralis')
NPY_DIR  = BASE_DIR / 'processed_npy'
RAW_DIR  = BASE_DIR / 'raw_fits'
LOG_DIR  = BASE_DIR / 'logs'
for d in [NPY_DIR, RAW_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / 'download_log.json'

# Kaggle images do not ship with the solar stack used by the project.
print("Installing dependencies...")
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
                'drms', 'sunpy', 'scikit-image', 'tqdm', 'astropy', 'reproject', 'kaggle'],
               check=True)
print("Dependencies ready")

# Configure the Kaggle API from notebook Secrets. The token is never stored in
# the repository; only the runtime-local kaggle.json is written.
from kaggle_secrets import UserSecretsClient
secret = UserSecretsClient()
kaggle_token = secret.get_secret("KAGGLE_TOKEN")

kaggle_dir = Path('/root/.kaggle')
kaggle_dir.mkdir(exist_ok=True)
kaggle_json = kaggle_dir / 'kaggle.json'
kaggle_json.write_text(json.dumps({
    "username": KAGGLE_USERNAME,
    "key": kaggle_token
}))
kaggle_json.chmod(0o600)
print("Kaggle API configured")

# Restore progress from the dataset version uploaded by the previous session.
print("Restoring previous progress from Kaggle dataset...")
try:
    subprocess.run([
        'kaggle', 'datasets', 'download',
        f'{KAGGLE_USERNAME}/{DATASET_NAME}',
        '--path', str(BASE_DIR),
        '--unzip', '--quiet'
    ], check=True, capture_output=True)

    # Move restored tensors back into the processing directory.
    restored = 0
    for npy in BASE_DIR.glob('*.npy'):
        dest = NPY_DIR / npy.name
        if not dest.exists():
            shutil.move(str(npy), str(dest))
            restored += 1

    # Restore the progress log if it was present in the dataset.
    prev_log = BASE_DIR / 'download_log.json'
    if prev_log.exists() and not LOG_FILE.exists():
        shutil.move(str(prev_log), str(LOG_FILE))

    print(f"Restored {restored} .npy files")
except Exception as e:
    print(f"No previous data found; assuming first session: {e}")

def load_progress():
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"processed": [], "failed": [], "downloaded": []}

def save_progress(progress):
    with open(LOG_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

# Preprocessing mirrors ``src/processing/prepare_dataset.py``: compute the
# activity proxy before resize, then store a symlog dual-channel tensor.
import numpy as np

def log_scale(x):
    return np.sign(x) * np.log1p(np.abs(x))

def fits_to_npy(fits_path, target_size=512, threshold=200.0):
    import sunpy.map
    from skimage.transform import resize

    solar_map = sunpy.map.Map(str(fits_path))
    data = solar_map.data.astype(np.float32)
    data = np.nan_to_num(data, nan=0.0)

    sunspot_index = float(np.sum(np.abs(data) > threshold) / data.size * 100.0)

    data = resize(data, (target_size, target_size),
                  mode='reflect', anti_aliasing=True,
                  preserve_range=True).astype(np.float32)
    data = np.nan_to_num(data, nan=0.0)

    data_log = log_scale(data)
    b_pos = np.maximum(data_log, 0.0)
    b_neg = np.maximum(-data_log, 0.0)

    tensor = np.stack([b_pos, b_neg], axis=0).astype(np.float32)
    return tensor, sunspot_index

def build_timestamps(date_ranges, sample_hours):
    timestamps = []
    for start_str, end_str in date_ranges:
        current = datetime.strptime(start_str, "%Y-%m-%d")
        end     = datetime.strptime(end_str, "%Y-%m-%d")
        while current <= end:
            timestamps.append(current)
            current += timedelta(hours=sample_hours)
    return sorted(timestamps)

def upload_to_kaggle(npy_dir, log_file, username, dataset_name):
    print("\nUploading progress to Kaggle dataset...")
    upload_dir = Path('/kaggle/working/upload_staging')
    upload_dir.mkdir(exist_ok=True)

    # The dataset version is the resume checkpoint for the next Kaggle session.
    for f in npy_dir.glob('*.npy'):
        shutil.copy2(str(f), str(upload_dir / f.name))
    if log_file.exists():
        shutil.copy2(str(log_file), str(upload_dir / 'download_log.json'))

    meta = {
        "title": dataset_name,
        "id": f"{username}/{dataset_name}",
        "licenses": [{"name": "MIT"}]
    }
    (upload_dir / 'dataset-metadata.json').write_text(json.dumps(meta))

    try:
        result = subprocess.run([
            'kaggle', 'datasets', 'version',
            '-p', str(upload_dir),
            '-m', f"Auto-update {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            '--quiet'
        ], capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print("Dataset updated")
        else:
            print(f"Upload failed: {result.stderr}")
    except Exception as e:
        print(f"Upload error: {e}")
    finally:
        shutil.rmtree(str(upload_dir), ignore_errors=True)

# Main download loop.
import drms
from tqdm.notebook import tqdm

progress   = load_progress()
timestamps = build_timestamps(DATE_RANGES, SAMPLE_HOURS)
already_done = set(progress['processed'])
pending = [t for t in timestamps if t.strftime('%Y%m%d_%H%M') not in already_done]

print("=" * 60)
print("  AURALIS — V3 PRO Dataset Builder")
print("=" * 60)
print(f"  Target total    : {len(timestamps):,} images")
print(f"  Already done    : {len(already_done):,}")
print(f"  Pending         : {len(pending):,}")
print("=" * 60)

client   = drms.Client()
new_ok   = 0
new_fail = 0
SESSION_START = datetime.utcnow()
MAX_SESSION_HOURS = 8  # Upload progress before Kaggle is likely to stop the runtime.

for ts in tqdm(timestamps, desc='Downloading magnetograms'):
    ts_key = ts.strftime('%Y%m%d_%H%M')

    if ts_key in already_done:
        continue

    # Save a resumable checkpoint during long sessions.
    elapsed = (datetime.utcnow() - SESSION_START).total_seconds() / 3600
    if elapsed >= MAX_SESSION_HOURS:
        save_progress(progress)
        upload_to_kaggle(NPY_DIR, LOG_FILE, KAGGLE_USERNAME, DATASET_NAME)
        print("Progress saved. The run can continue or be restarted safely.")
        SESSION_START = datetime.utcnow()

    npy_name = f"hmi.m_45s.{ts.strftime('%Y.%m.%d_%H_%M_00')}_TAI.magnetogram_processed.npy"
    npy_path = NPY_DIR / npy_name

    if npy_path.exists():
        progress['processed'].append(ts_key)
        already_done.add(ts_key)
        continue

    fits_path = None
    for attempt in range(3):
        try:
            t_str     = ts.strftime('%Y.%m.%d_%H:%M:00_TAI')
            keys, segs = client.query(
                f"hmi.M_45s[{t_str}/10m@10m]",
                key='T_REC', seg='magnetogram'
            )
            if keys is None or len(keys) == 0:
                break

            url       = 'http://jsoc.stanford.edu' + segs.magnetogram.iloc[0]
            fits_name = url.split('/')[-1]
            fits_dest = RAW_DIR / fits_name
            urllib.request.urlretrieve(url, str(fits_dest))
            fits_path = str(fits_dest)
            break

        except Exception as e:
            wait = 15 * (2 ** attempt)
            print(f"\n  Attempt {attempt+1}/3 for {ts}: {e}")
            if attempt < 2:
                time.sleep(wait)

    if not fits_path:
        progress['failed'].append(ts_key)
        new_fail += 1
        save_progress(progress)
        continue

    try:
        tensor, ssn_index = fits_to_npy(fits_path, TARGET_SIZE, SSN_THRESHOLD)
        np.save(str(npy_path), tensor)
        Path(fits_path).unlink(missing_ok=True)

        progress['processed'].append(ts_key)
        progress['downloaded'].append({
            'ts': ts_key,
            'file': npy_name,
            'sunspot_index': round(ssn_index, 4)
        })
        already_done.add(ts_key)
        new_ok += 1

        if new_ok % 100 == 0:
            save_progress(progress)
            print(f"\n  {new_ok} new images saved")

    except Exception as e:
        print(f"\n  Processing error for {fits_path}: {e}")
        progress['failed'].append(ts_key)
        new_fail += 1
        Path(fits_path).unlink(missing_ok=True)
        save_progress(progress)

    time.sleep(1.2)

# Final upload after the queue is exhausted.
save_progress(progress)
upload_to_kaggle(NPY_DIR, LOG_FILE, KAGGLE_USERNAME, DATASET_NAME)

print("\n" + "=" * 60)
print(f"  Newly processed : {new_ok:,}")
print(f"  Failed          : {new_fail:,}")
print(f"  Total processed : {len(progress['processed']):,}")
print(f"  Dataset         : kaggle.com/datasets/{KAGGLE_USERNAME}/{DATASET_NAME}")
print("=" * 60)

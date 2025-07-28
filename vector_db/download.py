# file: download.py
import os
from pathlib import Path
from s3_config import S3, BUCKET, PREFIX

LOCAL_DIR = Path("data/queplan")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

paginator = S3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=BUCKET, Prefix=PREFIX):
    for obj in page.get("Contents", []):
        key = obj["Key"]
        local_path = LOCAL_DIR / key[len(PREFIX):]
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if local_path.exists():
            print("✔ Already have", local_path)
            continue

        print("Downloading", key, "→", local_path)
        S3.download_file(BUCKET, key, str(local_path))

print("🎉 All files downloaded to ./data")
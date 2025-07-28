# file: list_files.py
from s3_config import S3, BUCKET, PREFIX

paginator = S3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=BUCKET, Prefix=PREFIX):
    for obj in page.get("Contents", []):
        print(obj["Key"], f"{obj['Size']/1024:.1f} KB")
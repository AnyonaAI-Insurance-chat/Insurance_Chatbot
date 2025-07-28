# file: s3_config.py
import boto3

SESSION = boto3.Session(
    aws_access_key_id="AKIA2JHUK4EGBVSQ5RUW",
    aws_secret_access_key="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",
    region_name="us-east-1"      # S3 is global, but boto3 needs a region
)

S3 = SESSION.client("s3")
BUCKET = "anyoneai-datasets"
PREFIX  = "queplan_insurance/"
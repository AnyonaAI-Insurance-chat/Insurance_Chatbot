## Descargar el dataset como cliente S3

import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Cargar .env desde el mismo directorio que el script
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION")
)

bucket_name = 'anyoneai-datasets'
prefix = 'queplan_insurance/'

response = s3.list_objects_v2(
    Bucket=bucket_name,
    Prefix=prefix
)

for obj in response.get('Contents', []):
    key = obj['Key']
    print(key)
    # Evitar descargar "carpetas" (terminan en '/')
    if key.endswith('/'):
        continue
    local_filename = os.path.basename(key)
    try:
        s3.download_file(bucket_name, key, local_filename)
        print(f"Descargado: {local_filename}")
    except ClientError as e:
        print(f"Error al descargar {key}: {e.response['Error']['Message']}")
        continue
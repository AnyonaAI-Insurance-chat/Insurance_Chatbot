import boto3
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()

# Usar las credenciales cargadas
session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

s3 = session.resource('s3')
bucket = s3.Bucket('anyoneai-datasets')

print("Intentando conectar con S3 y listar objetos...")
try:
    # Listar solo los primeros 5 objetos para una prueba rápida
    for i, obj in enumerate(bucket.objects.filter(Prefix='queplan_insurance/')):
        print(f"  -> Encontrado: {obj.key}")
        if i >= 4:
            break
    print("\n✅ ¡Éxito! Conexión y listado de archivos correctos.")
except Exception as e:
    print(f"\n❌ ¡Error! No se pudo conectar o listar. Revisa las credenciales y permisos.")
    print(f"   Detalle del error: {e}")

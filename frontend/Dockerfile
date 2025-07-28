FROM python:3.11-slim
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
# Copiamos la app después de instalar para aprovechar el caché de Docker
COPY ./app /code/app
# Este CMD se usará si no especificamos un 'command' en docker-compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

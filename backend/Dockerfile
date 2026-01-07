FROM python:3.10-slim-bookworm

WORKDIR /app

# Añadir capa de dependencias por separado y evitar problemas de red en apt-get
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev wget curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requisitos y actualizarlos por separado
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando para iniciar el servidor de FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.4

WORKDIR /app

# Instalar Python 3.10 y dependencias esenciales
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-dev python3-pip \
    build-essential libpq-dev wget curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear symlink para python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# Copiar requisitos y actualizarlos por separado
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando para iniciar el servidor de FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
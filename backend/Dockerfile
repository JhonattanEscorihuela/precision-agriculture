# Usamos una imagen base de Python
FROM python:3.9

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos los archivos de dependencia
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código fuente
COPY . .

# Exponemos el puerto del backend
EXPOSE 8000

# Comando para iniciar el servidor FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
# Dockerfile para UserAPI - FastAPI
FROM python:3.12-slim

# Crear usuario no-root para mayor seguridad
RUN useradd -m -u 1000 appuser

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar solo archivos necesarios (no todo el directorio)
COPY main.py routes.py models.py schemas.py database.py auth.py services.py ./

# Crear directorios necesarios y dar permisos al usuario
RUN mkdir -p uploaded_cvs profile_pictures temp_files temp_registrations && \
    chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8080

# Variable de entorno para Cloud Run
ENV PORT=8080

# Comando para ejecutar la aplicación
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}

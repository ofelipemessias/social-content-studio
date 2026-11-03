FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Gera um carrossel de exemplo (modo offline, sem chave de IA) em /app/out
CMD ["python", "-m", "content_studio.cli", "generate", \
     "--profile", "samples/perfil-aurora.json", \
     "--topic", "5 direitos do trabalhador demitido sem justa causa", \
     "--mode", "offline", "--out", "/app/out"]

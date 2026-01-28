# ChirpStack CSV Importer - Docker Image
# Image légère basée sur Python Alpine (~50MB)
# Build depuis la racine du repo: docker compose up -d --build

FROM python:3.12-alpine

LABEL description="ChirpStack CSV Importer - Outil web pour importer des devices LoRaWAN"

# Créer un utilisateur non-root pour la sécurité
RUN adduser -D -u 1000 appuser

WORKDIR /app

RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Copier depuis la racine du repo (context: ..)
COPY --chown=appuser:appuser docker/server.py ./
COPY --chown=appuser:appuser main.html ./

USER appuser

ENV PORT=8000 HOST=0.0.0.0 DATA_DIR=/app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

CMD ["python", "server.py"]

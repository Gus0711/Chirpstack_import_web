# ChirpStack CSV Importer - Version Docker

Configuration Docker pour lancer l'application automatiquement au démarrage du serveur.

## Prérequis

- Docker et Docker Compose installés

## Installation

### 1. Cloner le repo

```bash
git clone https://github.com/VOTRE-USER/Chirpstack_import_web.git
cd Chirpstack_import_web/docker
```

### 2. Construire et lancer

```bash
docker compose up -d --build
```

### 3. Accéder à l'application

Ouvrir http://localhost:4000 dans votre navigateur.

## Commandes utiles

```bash
# Arrêter l'application
docker-compose down

# Redémarrer
docker-compose restart

# Reconstruire après modification
docker-compose up -d --build

# Voir les logs en temps réel
docker-compose logs -f

# État de santé du conteneur
docker inspect chirpstack-importer --format='{{.State.Health.Status}}'
```

## Configuration

### Changer le port

Modifier dans `docker-compose.yml` :

```yaml
ports:
  - "9000:8000"  # Accessible sur le port 9000
```

### Persistance des données

Les profils et serveurs sont stockés dans un volume Docker nommé `importer-data`.

Pour voir où sont stockées les données :
```bash
docker volume inspect docker_importer-data
```

Pour sauvegarder les données :
```bash
docker cp chirpstack-importer:/app/data ./backup-data
```

Pour restaurer des données :
```bash
docker cp ./backup-data/. chirpstack-importer:/app/data/
```

## Comportement au démarrage

Grâce à `restart: unless-stopped`, le conteneur :
- Redémarre automatiquement au boot du serveur
- Redémarre en cas de crash
- Reste arrêté si vous l'arrêtez manuellement (`docker-compose down`)

## Health Check

L'application expose un endpoint `/health` pour vérifier son état :

```bash
curl http://localhost:8000/health
# Réponse: {"status": "healthy", "service": "chirpstack-importer"}
```

## Résolution de problèmes

### Le conteneur ne démarre pas

```bash
# Voir les logs détaillés
docker-compose logs

# Vérifier que le port n'est pas utilisé
netstat -an | grep 8000
```

### Erreur "main.html not found"

Assurez-vous d'avoir copié `main.html` dans ce dossier avant le build :
```bash
cp ../main.html .
docker-compose up -d --build
```

### Réinitialiser les données

```bash
# Supprimer le volume (perte des profils/serveurs)
docker-compose down -v
docker-compose up -d
```

## Architecture

```
docker/
├── Dockerfile          # Image Docker
├── docker-compose.yml  # Orchestration
├── server.py           # Serveur Python adapté pour Docker
├── main.html           # Interface web (à copier depuis parent)
├── .dockerignore       # Fichiers exclus du build
└── README.md           # Cette documentation
```

## Différences avec la version standalone

| Aspect | Standalone | Docker |
|--------|-----------|--------|
| Bind address | 127.0.0.1 | 0.0.0.0 |
| Stockage données | Même dossier | /app/data (volume) |
| Redémarrage auto | Non | Oui |
| Health check | Non | Oui |
| Isolation | Non | Oui |

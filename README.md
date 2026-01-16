# ChirpStack CSV Importer

Outil web pour importer des devices LoRaWAN dans ChirpStack v4 depuis un fichier CSV.

## Fonctionnalités

- **Upload CSV** : Drag & drop ou sélection de fichier
- **Détection automatique** : Séparateur CSV (`;`, `,`, `tab`) modifiable à la volée
- **Auto-mapping** : Détection intelligente des colonnes (dev_eui, app_key, name, etc.)
- **Mapping manuel** : Association personnalisée des colonnes CSV aux champs ChirpStack
- **Tags** : Support des tags depuis colonnes CSV ou valeurs fixes manuelles
- **Détection clé API** : Distingue automatiquement clé admin vs clé tenant
- **Gestion erreurs** : Messages d'erreur clairs + correction sans revenir en arrière
- **100% client-side** : Tout tourne dans le navigateur (via proxy local)

---

## Prérequis

- **Python 3.x** (pour le serveur proxy local)
- **ChirpStack v4** avec accès API
- **Navigateur moderne** (Chrome, Firefox, Edge)

---

## Installation

### Fichiers requis

```
Chirpstack_import_web/
├── main.html      # Interface web
├── server.py      # Serveur proxy Python
└── README.md      # Cette documentation
```

### Lancement

```bash
# Windows
py server.py

# Linux/Mac
python3 server.py

# Avec port personnalisé
py server.py 8080
```

Puis ouvrir : **http://localhost:8000**

---

## Utilisation

### Étape 1 : Connexion

1. Entrer l'**URL ChirpStack** (ex: `http://192.168.1.10:8080`)
2. Entrer le **Token API**
3. Cliquer sur **"Tester la connexion"**

**Comportement selon le type de clé :**

| Type de clé | Comportement |
|-------------|--------------|
| Clé Admin | Liste automatiquement les tenants disponibles |
| Clé Tenant | Demande de saisir le Tenant ID manuellement |

> **Où trouver le Tenant ID ?**
> Dans l'URL ChirpStack : `/#/tenants/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/...`

### Étape 2 : Sélection Application

Sélectionner l'application cible dans la liste déroulante.

### Étape 3 : Import CSV

1. **Configuration** : Sélectionner un Device Profile (optionnel si présent dans le CSV)
2. **Upload CSV** : Glisser-déposer ou cliquer pour parcourir
3. **Séparateur** : Modifier si nécessaire (le fichier se recharge automatiquement)
4. **Mapping** : Vérifier/ajuster l'association des colonnes
5. **Tags** : Ajouter des tags depuis colonnes CSV ou manuellement
6. **Import** : Cliquer sur "Lancer l'import"

---

## Format CSV

### Colonnes supportées

| Colonne | Obligatoire | Description |
|---------|-------------|-------------|
| `dev_eui` | Oui | DevEUI du device (16 caractères hex) |
| `name` | Non | Nom du device (défaut: dev_eui) |
| `description` | Non | Description du device |
| `app_key` / `nwk_key` | Non | Clé applicative (32 caractères hex) |
| `device_profile_id` | Non* | UUID du device profile |

> *`device_profile_id` est obligatoire soit dans le CSV, soit sélectionné dans l'interface.

### Exemple CSV

```csv
dev_eui;name;app_key;description
70B3D52DD301B337;Capteur-01;2B7E151628AED2A6ABF7158809CF4F3C;Bureau 1er étage
70B3D52DD301B8B8;Capteur-02;3C4F9C0809158F7FBA6A2DEA826151E7B2;Bureau RDC
```

### Auto-mapping

L'outil détecte automatiquement les colonnes suivantes :
- `deveui`, `dev_eui`, `DevEUI` → dev_eui
- `appkey`, `app_key`, `AppKey`, `nwkkey`, `nwk_key` → app_key
- `name`, `Name`, `nom` → name
- `description`, `Description` → description
- `device_profile_id`, `deviceprofileid` → device_profile_id

---

## Tags

### Tags depuis colonnes CSV

Cocher les colonnes à utiliser comme tags. Chaque valeur de la colonne devient un tag pour le device correspondant.

### Tags manuels

Ajouter des tags avec une valeur fixe appliquée à tous les devices importés.

**Exemple :**
- Tag CSV : colonne `batiment` → chaque device aura le tag `batiment: <valeur>`
- Tag manuel : `projet: Migration2024` → tous les devices auront ce tag

---

## Gestion des erreurs

### Messages d'erreur clarifiés

| Erreur API | Message affiché |
|------------|-----------------|
| `invalid length: expected 32, found 0` | Device Profile ID manquant |
| `object already exists` | Ce device existe déjà (dev_eui en doublon) |
| `invalid DevEUI` | DevEUI invalide (doit être 16 caractères hex) |
| `invalid AppKey` | AppKey invalide (doit être 32 caractères hex) |

### Correction sans retour arrière

Si l'erreur est **"Device Profile manquant"** :
1. Un sélecteur apparaît directement dans les résultats
2. Sélectionner le Device Profile voulu
3. Cliquer sur "Relancer l'import"
4. Seules les lignes en erreur sont ré-importées

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Navigateur   │────▶│  server.py      │────▶│   ChirpStack    │
│   (main.html)   │     │  (proxy:8000)   │     │   API (:8080)   │
│                 │◀────│                 │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Pourquoi un proxy ?**

Les navigateurs bloquent les requêtes cross-origin (CORS). Le proxy Python :
- Sert la page HTML
- Relaie les requêtes vers ChirpStack
- Ajoute les headers CORS nécessaires

---

## Configuration avancée

### Changer le port

```bash
py server.py 9000
```

### Sans proxy (modification ChirpStack)

Si vous pouvez modifier la configuration ChirpStack (`chirpstack.toml`) :

```toml
[api]
  cors_allow_origin = "*"
```

Puis ouvrir `main.html` directement (sans server.py).

> **Note sécurité** : `cors_allow_origin = "*"` autorise toutes les origines. Pour plus de sécurité, spécifier une origine précise.

---

## Démarrage automatique (production)

### Option 1 : Service Windows (NSSM)

```bash
nssm install ChirpStackImporter "C:\Python\python.exe" "C:\path\server.py"
nssm start ChirpStackImporter
```

### Option 2 : Tâche planifiée Windows

1. Ouvrir "Planificateur de tâches"
2. Créer une tâche basique
3. Déclencheur : "Au démarrage"
4. Action : Démarrer `python.exe` avec argument `C:\path\server.py`

### Option 3 : Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY main.html server.py ./
EXPOSE 8000
CMD ["python", "server.py"]
```

```bash
docker build -t chirpstack-importer .
docker run -d --restart=always -p 8000:8000 chirpstack-importer
```

---

## Troubleshooting

### "Failed to fetch" ou erreur CORS

- Vérifier que `server.py` tourne
- Accéder via `http://localhost:8000` (pas `file://`)

### "401 Unauthorized"

- Token API invalide ou expiré
- Créer un nouveau token dans ChirpStack

### "Device Profile ID manquant"

- Sélectionner un Device Profile dans l'interface
- Ou ajouter une colonne `device_profile_id` dans le CSV

### Le séparateur ne fonctionne pas

- Vérifier l'encodage du fichier (UTF-8 recommandé)
- Essayer les différents séparateurs

### Clé tenant : impossible de lister les tenants

- Normal ! Les clés tenant n'ont pas accès à `/api/tenants`
- Saisir le Tenant ID manuellement

---

## API ChirpStack utilisée

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/tenants` | GET | Liste des tenants (admin uniquement) |
| `/api/applications` | GET | Liste des applications d'un tenant |
| `/api/device-profiles` | GET | Liste des device profiles d'un tenant |
| `/api/devices` | POST | Création d'un device |
| `/api/devices/{dev_eui}/keys` | POST | Ajout des clés (app_key) |

---

## Licence

Usage interne.

---

## Auteur

Généré avec Claude Code.

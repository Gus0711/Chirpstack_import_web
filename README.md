# ChirpStack Device Manager

Outil web pour gérer les devices LoRaWAN dans ChirpStack v4 : import, export, suppression en masse, migration, changement de profil, recherche cross-app, mise à jour des tags.

## Fonctionnalités

### Import
- **Upload CSV/Excel** : Drag & drop ou sélection de fichier (formats CSV, XLS, XLSX)
- **Import manuel** : Ajout de 1 à 5 devices sans fichier CSV
- **Détection automatique** : Séparateur CSV (`;`, `,`, `tab`) modifiable à la volée
- **Auto-mapping** : Détection intelligente des colonnes (dev_eui, app_key, name, etc.)
- **Mapping manuel** : Association personnalisée des colonnes CSV aux champs ChirpStack
- **Tags** : Support des tags depuis colonnes CSV ou valeurs fixes manuelles
- **Profils d'import** : Gestion de profils avec tags obligatoires (stockage serveur)
- **Validation des tags** : Vérification automatique des tags requis avant import
- **Détection de doublons** : Avant chaque import, vérifie les DevEUI déjà présents et propose d'ignorer, écraser ou annuler
- **Validation pré-import** : Vérification des formats (DevEUI 16 hex, AppKey 32 hex, doublons internes) avec cellules en rouge dans l'aperçu
- **Annulation d'import** : Bouton pour supprimer tous les devices créés lors du dernier import (fichier ou manuel)

### Export
- **Export CSV/XLSX** : Exporte tous les devices d'une application avec pagination automatique
- **Clés optionnelles** : Possibilité d'inclure les nwkKey/appKey (avec avertissement sécurité)
- **Tags dynamiques** : Toutes les clés de tags découvertes automatiquement comme colonnes
- **Aperçu** : Visualisation des données avant téléchargement
- **Filtres** : Filtrage par Device Profile, activité (actif/inactif/jamais vu) ou tag avant export

### Suppression en masse
- **Chargement paginé** : Charge tous les devices avec barre de progression
- **Recherche en temps réel** : Filtrage par nom ou DevEUI
- **Sélection multiple** : Checkboxes avec tout sélectionner / tout désélectionner
- **Confirmation sécurisée** : Saisie du nombre exact de devices pour confirmer
- **Log en temps réel** : Suivi de chaque suppression

### Migration entre applications
- **Déplacement de devices** : Migrer des devices d'une application vers une autre
- **Conservation complète** : Clés (nwkKey/appKey) et tags conservés lors de la migration
- **Sélection multiple** : Même pattern checkboxes avec recherche et filtrage
- **Avertissement sécurité** : Warning explicite car la migration supprime puis recrée le device

### Changement de Device Profile en masse
- **Modification groupée** : Changer le Device Profile de plusieurs devices en une opération
- **Affichage du profil actuel** : Chaque device affiche son profil actuel pour comparaison
- **Sélection multiple** : Checkboxes avec recherche et filtrage

### Recherche cross-app
- **Recherche directe** : DevEUI exact (16 hex) → requête directe instantanée
- **Recherche partielle** : Texte partiel → scan de toutes les applications du tenant
- **Résultats complets** : DevEUI, nom, application, profil, dernier vu

### Mise à jour des tags
- **Import fichier** : Upload CSV/XLSX avec colonne `dev_eui` + colonnes de tags
- **Mode fusion** : Ajoute/modifie les tags sans supprimer les existants
- **Mode remplacement** : Remplace tous les tags par ceux du fichier
- **Aperçu** : Visualisation avant exécution

### Template CSV
- **Génération de modèle** : CSV pré-configuré selon le Device Profile et le profil d'import sélectionnés
- **Colonnes adaptées** : Inclut automatiquement les tags obligatoires du profil

### Général
- **Compteur de devices** : Nombre de devices de l'application affiché dans le hub (rafraîchi automatiquement)
- **Copier-coller rapide** : Boutons "copier" à côté de chaque DevEUI dans tous les tableaux
- **Détection clé API** : Distingue automatiquement clé admin vs clé tenant
- **Dashboard tenant** : Statistiques devices (actifs/inactifs/jamais vus) et gateways
- **Serveurs sauvegardés** : Mémorisation des URLs de serveurs pour accès rapide
- **Gestion erreurs** : Messages d'erreur clairs + correction sans revenir en arrière
- **100% client-side** : Tout tourne dans le navigateur (via proxy local)

---

## Prérequis

- **Python 3.x** (pour le serveur proxy local)
- **ChirpStack v4** avec accès API
- **Navigateur moderne** (Chrome, Firefox, Edge)

---

<img width="972" height="946" alt="image" src="https://github.com/user-attachments/assets/f0c7b378-5b1c-4722-9fad-ce2912f7cddb" />


## Installation

### Fichiers requis

```
Chirpstack_import_web/
├── main.html      # Interface web (SPA)
├── server.py      # Serveur proxy Python
├── profiles.json  # Stockage des profils (généré automatiquement)
├── servers.json   # Stockage des serveurs sauvegardés (généré automatiquement)
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

1. Entrer l'**URL ChirpStack** (ex: `http://192.168.1.10:8080`) ou sélectionner un serveur sauvegardé
2. Entrer le **Token API**
3. Cliquer sur **"Tester la connexion"**

**Serveurs sauvegardés :**
- Utiliser le menu déroulant pour sélectionner un serveur enregistré
- Cliquer sur **"+"** pour sauvegarder un nouveau serveur (nom + URL)
- Seules les URLs sont stockées, jamais les tokens (sécurité)

**Comportement selon le type de clé :**

| Type de clé | Comportement |
|-------------|--------------|
| Clé Admin | Liste automatiquement les tenants disponibles |
| Clé Tenant | Demande de saisir le Tenant ID manuellement |

> **Où trouver le Tenant ID ?**
> Dans l'URL ChirpStack : `/#/tenants/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/...`

**Dashboard tenant :**

À la sélection du tenant, un dashboard s'affiche avec :
- **Devices actifs** : vus dans les dernières 24h
- **Devices inactifs** : non vus depuis plus de 24h
- **Devices jamais vus** : aucune communication enregistrée
- **Gateways** : nombre de gateways actives / total

### Étape 2 : Sélection Application

Sélectionner l'application cible dans la liste déroulante.

### Étape 3 : Hub d'outils

Après sélection de l'application, un hub affiche 8 outils sous forme de cartes cliquables (avec le compteur de devices de l'application) :

#### Import

Deux modes d'import disponibles :

**Mode Fichier (CSV/Excel) :**

1. **Profil d'import** : Sélectionner un profil d'import (obligatoire) — définit les tags requis
2. **Device Profile** : Sélectionner un Device Profile (optionnel si présent dans le fichier)
3. **Upload fichier** : Glisser-déposer ou cliquer pour parcourir (CSV, XLS, XLSX)
4. **Séparateur** : Pour les CSV, modifier si nécessaire (auto-détecté)
5. **Mapping** : Vérifier/ajuster l'association des colonnes
6. **Tags obligatoires** : Remplir les tags requis par le profil sélectionné
7. **Tags additionnels** : Ajouter des tags depuis colonnes ou manuellement
8. **Validation** : Les erreurs de format (DevEUI, AppKey) sont surlignées en rouge dans l'aperçu
9. **Import** : Cliquer sur "Lancer l'import"
10. **Doublons** : Si des DevEUI existent déjà, choisir entre ignorer, écraser ou annuler
11. **Annulation** : Après l'import, un bouton permet de supprimer tous les devices créés en cas d'erreur

**Mode Manuel (1-5 devices) :**

1. Basculer en mode "Ajout manuel"
2. Remplir DevEUI, AppKey (optionnel), Nom
3. Remplir les tags obligatoires du profil
4. Cliquer sur "Importer les devices"

> **Note** : Le mode manuel est limité à 5 devices. Pour plus, utiliser un fichier CSV/Excel.

#### Export

1. Cocher "Inclure les clés" si besoin (attention : données sensibles en clair)
2. Choisir le format : CSV ou XLSX
3. Cliquer sur "Charger les devices" — pagination automatique
4. **Filtrer** (optionnel) : par Device Profile, activité ou tag (cle=valeur)
5. Vérifier l'aperçu puis cliquer sur "Télécharger" (seuls les devices filtrés sont exportés)

#### Suppression en masse

1. Cliquer sur "Charger les devices"
2. Utiliser la barre de recherche pour filtrer par nom ou DevEUI
3. Cocher les devices à supprimer (ou "Tout sélectionner")
4. Cliquer sur "Supprimer la sélection"
5. Confirmer en tapant le nombre exact de devices

> **Attention** : La suppression est irréversible. Tester sur une application de test.

#### Migration

1. Sélectionner l'**application de destination** dans la liste déroulante
2. Cliquer sur "Charger les devices" pour lister les devices de l'application source
3. Cocher les devices à migrer (recherche et sélection groupée disponibles)
4. Cliquer sur "Migrer la sélection" et confirmer

> **Attention** : La migration supprime le device de l'app source puis le recrée dans l'app destination. Si la recréation échoue, le device pourrait être perdu. Tester d'abord sur une application de test.

#### Changement de Device Profile

1. Sélectionner le **nouveau Device Profile** dans la liste déroulante
2. Cliquer sur "Charger les devices"
3. Cocher les devices à modifier (le profil actuel est affiché pour chaque device)
4. Cliquer sur "Appliquer le changement" et confirmer

#### Recherche

1. Saisir un **DevEUI** (complet ou partiel, minimum 4 caractères)
2. Cliquer sur "Rechercher"
   - DevEUI exact (16 hex) : recherche directe via API (instantané)
   - Partiel : scan de toutes les applications (plus lent)
3. Les résultats affichent le device, son application et son profil

#### Mise à jour des tags

1. Choisir le mode : **Fusionner** (ajouter/modifier sans supprimer) ou **Remplacer** (remplacer tous les tags)
2. Glisser-déposer un fichier CSV/XLSX contenant `dev_eui` + colonnes de tags
3. Vérifier l'aperçu
4. Cliquer sur "Lancer la mise à jour"

#### Template CSV

1. Cliquer sur la carte "Template CSV"
2. Sélectionner un Device Profile et/ou un profil d'import (optionnel)
3. Télécharger le fichier modèle pré-configuré

---

## Format des fichiers

### Formats acceptés

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | Séparateurs : `;`, `,`, `tab` (auto-détecté) |
| Excel | `.xls`, `.xlsx` | Première feuille utilisée |

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

## Profils d'import

Les profils d'import permettent de définir des modèles avec des **tags obligatoires** pour standardiser les imports.

### Gestion des profils

Accéder à la gestion via le bouton engrenage (⚙) à côté du sélecteur de profil ou via le bouton flottant en bas à droite.

**Fonctionnalités :**
- Créer/modifier/supprimer des profils
- Définir une liste de tags obligatoires par profil
- Les profils sont stockés côté serveur (`profiles.json`)

### Sélection obligatoire

Avant de pouvoir charger un fichier, vous devez sélectionner :
- Un **profil existant** : les tags définis seront obligatoires
- **"Sans profil"** : import simple sans tags obligatoires

### Exemple de profil

```json
{
  "name": "CHCM",
  "requiredTags": ["Site", "Batiment", "Etage", "Emplacement"]
}
```

Lors de l'import avec ce profil, l'utilisateur devra mapper ou renseigner manuellement ces 4 tags pour chaque device.

---

## Tags

### Tags depuis colonnes CSV/Excel

Cocher les colonnes à utiliser comme tags. Chaque valeur de la colonne devient un tag pour le device correspondant.

### Tags obligatoires (profil)

Si un profil avec tags obligatoires est sélectionné, des champs apparaissent pour :
- Mapper chaque tag requis vers une colonne du fichier
- Ou saisir une valeur fixe appliquée à tous les devices

### Tags manuels

Ajouter des tags avec une valeur fixe appliquée à tous les devices importés.

**Exemple :**
- Tag depuis colonne : colonne `batiment` → chaque device aura le tag `batiment: <valeur>`
- Tag manuel : `projet: Migration2024` → tous les devices auront ce tag
- Tag obligatoire (profil) : mappé vers colonne ou valeur fixe

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

### Option 3 : Docker (recommandé)

Une configuration Docker complète est disponible dans le dossier `docker/`.

**Déploiement :**

```bash
git clone https://github.com/augustmusic/Chirpstack_import_web.git
cd Chirpstack_import_web/docker
docker compose up -d --build
```

L'application est accessible sur `http://IP_SERVEUR:4000`

**Mise à jour :**

```bash
cd Chirpstack_import_web
git pull
cd docker
docker compose up -d --build
```

**Commandes utiles :**

```bash
docker compose logs -f      # Voir les logs
docker compose restart      # Redémarrer
docker compose down         # Arrêter
```

**Avantages :**
- Redémarrage automatique au boot du serveur
- Données persistantes (volume Docker)
- Health check intégré (`/health`)
- Isolation complète

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

### Le séparateur ne fonctionne pas (CSV)

- Vérifier l'encodage du fichier (UTF-8 recommandé)
- Essayer les différents séparateurs
- Utiliser un fichier Excel (.xlsx) comme alternative

### Impossible de charger un fichier

- Vérifier qu'un **profil d'import** est sélectionné (obligatoire)
- Utiliser "Sans profil" pour un import simple

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
| `/api/devices` | GET | Liste des devices d'une application (pagination) |
| `/api/devices` | POST | Création d'un device |
| `/api/devices/{dev_eui}` | GET | Récupération d'un device (mise à jour tags) |
| `/api/devices/{dev_eui}` | PUT | Mise à jour d'un device (tags) |
| `/api/devices/{dev_eui}` | DELETE | Suppression d'un device |
| `/api/devices/{dev_eui}/keys` | GET | Récupération des clés (export) |
| `/api/devices/{dev_eui}/keys` | POST | Ajout des clés (app_key) |
| `/api/gateways` | GET | Liste des gateways d'un tenant (dashboard) |

## API locale (profils)

Le serveur Python expose une API REST pour la gestion des profils d'import :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/profiles` | GET | Liste tous les profils |
| `/api/profiles` | POST | Crée un nouveau profil |
| `/api/profiles/{id}` | PUT | Met à jour un profil |
| `/api/profiles/{id}` | DELETE | Supprime un profil |

Les profils sont stockés dans `profiles.json`.

## API locale (serveurs)

Gestion des serveurs ChirpStack sauvegardés (URLs uniquement, pas les tokens) :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/servers` | GET | Liste tous les serveurs sauvegardés |
| `/api/servers` | POST | Sauvegarde un nouveau serveur |
| `/api/servers/{id}` | DELETE | Supprime un serveur |

Les serveurs sont stockés dans `servers.json` (non versionné pour sécurité).

> **Note sécurité** : Seules les URLs sont stockées, jamais les tokens API.

---

## Licence

Usage interne.

---

## Auteur

Généré avec Claude Code.

# Changelog - Tools Hub (5 nouvelles fonctionnalites)

## Resume des modifications

Un seul fichier modifie : `main.html`
Aucun changement sur `server.py` ou `docker/server.py`.

Le Step 3 "Import CSV" a ete transforme en **Hub d'outils** avec 5 cartes :

```
Step 1: Connexion  →  Step 2: Application  →  Step 3: Outils (Hub)
                                                  ├── Import (existant, inchange)
                                                  ├── Export
                                                  ├── Supprimer en masse
                                                  ├── Mise a jour des tags
                                                  └── Template CSV (telecharge directement)
```

Le titre de l'app passe de "ChirpStack CSV Importer" a "ChirpStack Device Manager".

---

## Fonctionnalites ajoutees

### 1. Tools Hub (refactoring)
- Le step 3 affiche maintenant une grille de 5 cartes cliquables
- Chaque outil s'ouvre en sous-vue avec un bouton "Retour" en haut
- Le stepper reste a 3 etapes, le label passe de "Import CSV" a "Outils"
- L'import existant fonctionne exactement comme avant, juste encapsule dans une sous-vue

### 2. Template CSV
- Clic sur la carte "Template CSV" ouvre un modal
- On peut choisir un Device Profile (optionnel) et un Profil d'import (optionnel)
- Genere un fichier CSV avec les colonnes de base (`name;dev_eui;description;app_key`) + `device_profile_id` si pas de DP selectionne + colonnes des tags du profil
- Separateur `;`, une ligne d'exemple incluse

### 3. Detection de doublons avant import
- Avant chaque import fichier, le systeme charge tous les devices existants de l'application
- Compare les DevEUI du CSV avec ceux deja presents
- Si doublons trouves, affiche un tableau avec 3 options :
  - **Ignorer** : importe uniquement les devices non-doublons
  - **Ecraser** : supprime les devices existants puis les recree depuis le CSV
  - **Annuler** : revient a l'ecran precedent
- Si aucun doublon, l'import se lance directement comme avant

### 4. Export de devices
- Charge tous les devices de l'application (pagination automatique)
- Option "Inclure les cles" (nwkKey/appKey) avec avertissement securite
- Format CSV ou XLSX (Excel via SheetJS)
- Apercu des 5 premieres lignes avant telechargement
- Colonnes : `dev_eui`, `name`, `description`, `device_profile_id`, `device_profile_name`, `created_at`, `last_seen_at`, + tous les tags (decouverts dynamiquement), + optionnellement `nwk_key`/`app_key`

### 5. Suppression en masse
- Charge tous les devices avec barre de progression
- Liste avec checkboxes, barre de recherche en temps reel (filtre par nom ou DevEUI)
- Boutons "Tout selectionner" / "Tout deselectionner"
- Compteur de selection
- Modal de confirmation : il faut taper le nombre exact de devices a supprimer
- Suppression sequentielle avec 50ms de delai entre chaque appel API
- Log des resultats en temps reel

### 6. Mise a jour des tags en masse
- Upload d'un fichier CSV/XLSX contenant `dev_eui` + colonnes de tags
- Deux modes :
  - **Fusionner** : ajoute/modifie les tags sans supprimer les existants
  - **Remplacer** : remplace tous les tags par ceux du fichier
- Apercu avant execution
- Pour chaque ligne : GET device → modification des tags → PUT device
- Log des resultats en temps reel

---

## Modifications techniques

- `apiCall()` gere maintenant les reponses vides (DELETE retourne souvent un body vide)
- Nouvelle fonction utilitaire `loadAllDevicesFromApp(appId, progressCallback)` avec pagination automatique (limit=100, boucle sur offset)
- Nouvelle fonction utilitaire `triggerDownload(content, filename, mimeType)` pour les telechargements
- Nouvelles classes CSS : `.tools-hub-grid`, `.tool-card`, `.tool-subview`, `.btn-danger`, `.progress-bar`, `.delete-search`, `.warning-box`, `.drop-zone-small`, `.mode-selector`

---

## Comment tester

### Pre-requis
- Lancer `python server.py` (ou Docker)
- Ouvrir `http://localhost:8000`
- Avoir un ChirpStack accessible avec une API key et au moins une application avec quelques devices

### Test 1 : Navigation Tools Hub
1. Se connecter (step 1), selectionner une app (step 2)
2. **Verifier** : le step 3 affiche bien les 5 cartes
3. Cliquer sur "Import" → verifier que l'import existant fonctionne comme avant
4. Cliquer "Retour" → verifier le retour au hub
5. Tester chaque carte : elles doivent chacune ouvrir leur sous-vue

### Test 2 : Template CSV
1. Depuis le hub, cliquer "Template CSV"
2. Le modal s'ouvre avec les selects Device Profile et Profil d'import
3. Tester sans selection → le CSV doit contenir `name;dev_eui;description;app_key;device_profile_id`
4. Selectionner un Device Profile → `device_profile_id` ne doit plus apparaitre comme colonne
5. Selectionner un profil d'import avec des tags → les tags doivent apparaitre comme colonnes
6. Verifier que le fichier telecharge est bien un CSV valide avec une ligne d'exemple

### Test 3 : Detection de doublons
1. Importer un device normalement via l'outil Import (avec un CSV)
2. Relancer l'import avec le meme CSV (memes DevEUI)
3. **Verifier** : la section "Doublons detectes" apparait avec le tableau
4. Tester "Ignorer les doublons" → seuls les nouveaux devices doivent etre importes
5. Tester "Ecraser" → les devices existants doivent etre supprimes puis recrees
6. Tester "Annuler" → retour a l'ecran sans import

### Test 4 : Export
1. Depuis le hub, cliquer "Export"
2. Cliquer "Charger les devices" → la barre de progression doit avancer
3. **Verifier** : le tableau d'apercu montre les 5 premiers devices
4. Tester export CSV → verifier le contenu du fichier (separateur `;`)
5. Tester export XLSX → verifier que le fichier s'ouvre dans Excel
6. Cocher "Inclure les cles" → recharger → verifier que les colonnes `nwk_key`/`app_key` sont presentes
7. Verifier que les tags sont bien exportes (colonnes dynamiques)

### Test 5 : Suppression en masse
1. Depuis le hub, cliquer "Supprimer en masse"
2. Cliquer "Charger les devices" → la liste s'affiche
3. Tester la recherche : taper un nom ou DevEUI partiel → la liste se filtre
4. Selectionner quelques devices avec les checkboxes
5. **Verifier** : le compteur se met a jour
6. Tester "Tout selectionner" / "Tout deselectionner"
7. Cliquer "Supprimer la selection" → le modal de confirmation apparait
8. Taper un mauvais nombre → ca ne doit pas passer
9. Taper le bon nombre → la suppression se lance avec log en temps reel
10. **Verifier dans ChirpStack** que les devices sont bien supprimes

> **ATTENTION** : tester sur une application de test, pas en production !

### Test 6 : Mise a jour des tags
1. Preparer un fichier CSV avec :
   ```
   dev_eui;mon_tag;autre_tag
   70B3D52DD3000001;valeur1;valeur2
   ```
   (utiliser des DevEUI existants dans l'application)
2. Depuis le hub, cliquer "Mise a jour des tags"
3. Selectionner le mode "Fusionner"
4. Glisser ou selectionner le fichier
5. **Verifier** : l'apercu montre les lignes et colonnes detectees
6. Cliquer "Lancer la mise a jour"
7. **Verifier dans ChirpStack** que les tags ont ete ajoutes/modifies sans supprimer les anciens
8. Refaire le test avec le mode "Remplacer" → les anciens tags doivent disparaitre

### Test responsive
- Tester sur mobile / tablette : la grille du hub passe de 3 colonnes a 2 puis 1

---

## A ajouter au README

Suggestion de section a ajouter :

```markdown
## Fonctionnalites

- **Import** : import de devices depuis CSV/XLS/XLSX ou saisie manuelle, avec profils d'import et detection de doublons
- **Export** : export de tous les devices d'une application en CSV ou XLSX, avec option d'inclure les cles
- **Suppression en masse** : selection, recherche et suppression de plusieurs devices avec confirmation
- **Mise a jour des tags** : modification des tags de vos devices en masse via fichier CSV/XLSX (fusion ou remplacement)
- **Template CSV** : generation d'un modele CSV pre-configure selon le device profile et le profil d'import
```

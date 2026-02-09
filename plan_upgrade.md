# Plan d'upgrade - ChirpStack Device Manager

## Vue d'ensemble

8 fonctionnalites a ajouter, classees en 2 categories :
- **Fonctionnalites majeures** (Phases 1-4) : nouvelles capacites
- **Qualite de vie** (Phases 5-8) : ameliorations UX

Toutes les modifications dans `main.html` uniquement. Aucun changement serveur.

---

## Phase 1 : Annuler le dernier import

### Objectif
Apres un import (fichier ou manuel), proposer un bouton "Annuler" qui supprime tous les devices qui viennent d'etre crees. Pratique en cas d'erreur de fichier ou d'application.

### Principe
On stocke deja les DevEUI des devices importes avec succes dans le flux `startImport()` / `importManualDevices()`. Il suffit de les sauvegarder dans une variable globale et d'afficher un bouton dans la section resultats.

### Variables globales a ajouter
```js
let lastImportedDevEuis = []; // DevEUI des devices crees lors du dernier import
```

### Modifications JS

**Dans `startImport()` (ligne ~3722) :**
- Au debut (hors retry) : `lastImportedDevEuis = [];`
- Apres chaque `apiCall('/api/devices', 'POST', ...)` reussi : `lastImportedDevEuis.push(devEui);`

**Dans `executeImportWithDuplicateHandling()` (ligne ~5061) :**
- Meme logique : reset au debut, push apres chaque succes

**Dans `importManualDevices()` (ligne ~4755) :**
- Meme logique

**Nouvelle fonction `undoLastImport()` :**
```js
async function undoLastImport() {
    if (lastImportedDevEuis.length === 0) return;
    if (!confirm(`Supprimer les ${lastImportedDevEuis.length} devices qui viennent d'etre importes ?`)) return;

    log('\n── Annulation du dernier import ──', 'info');
    let deleted = 0;
    let errors = 0;

    for (const devEui of lastImportedDevEuis) {
        try {
            await apiCall(`/api/devices/${devEui}`, 'DELETE');
            log(`✓ ${devEui} supprime`, 'success');
            deleted++;
        } catch (err) {
            log(`✗ ${devEui}: ${err.message}`, 'error');
            errors++;
        }
        await new Promise(r => setTimeout(r, 50));
    }

    log(`── Annulation terminee: ${deleted} supprime(s), ${errors} erreur(s) ──`, deleted > 0 ? 'success' : 'error');
    lastImportedDevEuis = [];
    document.getElementById('btnUndoImport').classList.add('hidden');
}
```

### Modifications HTML

**Dans la section `#resultsSection` (apres les stats, avant le log) :**
```html
<div style="text-align: center; margin: 1rem 0;">
    <button class="btn-danger btn-small hidden" id="btnUndoImport" onclick="undoLastImport()">
        Annuler l'import (supprimer les devices crees)
    </button>
</div>
```

**Affichage du bouton :** a la fin de `startImport()` et `executeImportWithDuplicateHandling()`, si `lastImportedDevEuis.length > 0` :
```js
document.getElementById('btnUndoImport').classList.remove('hidden');
```

### Estimation
~40 lignes JS + ~5 lignes HTML

---

## Phase 2 : Migration entre applications

### Objectif
Deplacer des devices d'une application a une autre, en conservant les cles et les tags.

### Principe
1. Charger les devices de l'app courante
2. Selectionner les devices a migrer (meme pattern que la suppression)
3. Choisir l'application de destination
4. Pour chaque device : GET device complet → GET keys → DELETE dans l'app source → POST dans l'app dest → POST keys

### Nouvelle carte dans le Hub
```html
<div class="tool-card" onclick="showTool('migrate')">
    <svg><!-- icone fleches --></svg>
    <h3>Migration</h3>
    <p>Deplacer des devices vers une autre application</p>
</div>
```

### Nouveau sub-view `#migrateSubView`
```html
<div id="migrateSubView" class="tool-subview hidden">
    <div class="tool-subview-header">
        <button class="btn-back" onclick="backToToolsHub()">← Retour</button>
        <h2>Migration de devices</h2>
    </div>
    <div class="card" style="max-width: 700px; margin: 0 auto 1.5rem auto;">
        <p>Application source : <span id="migrateSourceApp">-</span></p>

        <label>Application de destination</label>
        <select id="migrateDestApp">
            <!-- Rempli dynamiquement avec toutes les apps sauf la courante -->
        </select>

        <button class="btn-primary" onclick="loadDevicesForMigration()">Charger les devices</button>
        <!-- Barre de progression -->
    </div>
    <!-- Liste avec checkboxes (meme pattern que delete) -->
    <div class="card hidden" id="migrateListCard">
        <input type="text" class="delete-search" placeholder="Rechercher..." oninput="filterMigrateList(this.value)">
        <div class="delete-actions-bar">
            <button class="btn-secondary btn-small" onclick="selectAllForMigration()">Tout selectionner</button>
            <button class="btn-secondary btn-small" onclick="deselectAllMigration()">Tout deselectionner</button>
            <span class="selection-count"><span id="migrateSelectionCount">0</span> device(s)</span>
        </div>
        <div class="preview-table" style="max-height: 400px; overflow-y: auto;">
            <table id="migrateTable">
                <thead><tr><th></th><th>Nom</th><th>DevEUI</th><th>Profil</th></tr></thead>
                <tbody></tbody>
            </table>
        </div>
        <div style="margin-top: 1rem; text-align: center;">
            <button class="btn-primary" id="btnMigrate" onclick="executeMigration()" disabled>Migrer la selection</button>
        </div>
    </div>
    <!-- Resultats -->
    <div class="card hidden" id="migrateResultsCard">
        <h2>Resultats</h2>
        <div class="progress-bar"><div class="progress-bar-fill" id="migrateProgressBar"></div></div>
        <p class="progress-text" id="migrateProgressText"></p>
        <div class="log-container" id="migrateLogContainer"></div>
    </div>
</div>
```

### Variables globales
```js
let migrateDevices = [];
let migrateSelection = new Set();
let migrateFilterQuery = '';
```

### Fonctions JS principales

```js
function showMigrateTool() {
    document.getElementById('migrateSourceApp').textContent = selectedApplicationName;
    // Remplir le select destination avec toutes les apps sauf la courante
    const destSelect = document.getElementById('migrateDestApp');
    destSelect.innerHTML = '<option value="">-- Choisir --</option>' +
        applications.filter(a => a.id !== selectedApplicationId)
            .map(a => `<option value="${a.id}">${a.name}</option>`).join('');
}

async function loadDevicesForMigration() { /* Meme pattern que loadDevicesForDelete */ }
function renderMigrateList() { /* Meme pattern que renderDeleteList */ }
function filterMigrateList(query) { /* Meme pattern */ }
function selectAllForMigration() { /* Meme pattern */ }
function deselectAllMigration() { /* Meme pattern */ }

async function executeMigration() {
    const destAppId = document.getElementById('migrateDestApp').value;
    if (!destAppId) { alert('Selectionnez une application de destination'); return; }

    for (const devEui of migrateSelection) {
        try {
            // 1. GET device complet
            const deviceData = await apiCall(`/api/devices/${devEui}`);
            const device = deviceData.device;

            // 2. GET keys (peut echouer si pas de cles)
            let keys = null;
            try {
                const keysData = await apiCall(`/api/devices/${devEui}/keys`);
                keys = keysData.deviceKeys;
            } catch (e) { /* pas de cles */ }

            // 3. DELETE dans l'app source
            await apiCall(`/api/devices/${devEui}`, 'DELETE');

            // 4. POST dans l'app destination
            device.applicationId = destAppId;
            await apiCall('/api/devices', 'POST', { device });

            // 5. POST keys si existantes
            if (keys) {
                await apiCall(`/api/devices/${devEui}/keys`, 'POST', { deviceKeys: keys });
            }

            log(`✓ ${device.name} migre`, 'success');
        } catch (err) {
            log(`✗ ${devEui}: ${err.message}`, 'error');
        }
        await new Promise(r => setTimeout(r, 50));
    }
}
```

### Point d'attention
- Si le DELETE reussit mais le POST echoue, le device est perdu. On pourrait stocker les devices en memoire pour un rollback, mais ca complexifie. Alternative : afficher un warning clair avant de lancer.
- Les device profiles doivent exister dans le tenant (ils sont partages au niveau tenant, pas app, donc ca devrait aller).

### Estimation
~200 lignes (HTML + JS)

---

## Phase 3 : Changement de Device Profile en masse

### Objectif
Selectionner des devices et changer leur Device Profile d'un coup.

### Principe
Reutiliser le pattern de la suppression en masse (chargement + checkboxes + selection) mais au lieu de DELETE, faire GET device → modifier `deviceProfileId` → PUT device.

### Nouvelle carte dans le Hub
```html
<div class="tool-card" onclick="showTool('dpChange')">
    <svg><!-- icone engrenage/switch --></svg>
    <h3>Changer le profil</h3>
    <p>Modifier le Device Profile de plusieurs devices</p>
</div>
```

### Nouveau sub-view `#dpChangeSubView`
Structure similaire a deleteSubView :
- Bouton "Charger les devices" + barre de progression
- Select du nouveau Device Profile (rempli depuis `deviceProfiles` global)
- Liste avec checkboxes (meme pattern)
- Bouton "Appliquer le changement"
- Log des resultats

### Fonctions JS principales
```js
let dpChangeDevices = [];
let dpChangeSelection = new Set();

async function loadDevicesForDpChange() { /* Meme pattern que delete */ }
function renderDpChangeList() { /* Avec affichage du DP actuel par device */ }

async function executeDpChange() {
    const newDpId = document.getElementById('dpChangeSelect').value;
    if (!newDpId) { alert('Selectionnez un Device Profile'); return; }

    for (const devEui of dpChangeSelection) {
        try {
            const deviceData = await apiCall(`/api/devices/${devEui}`);
            const device = deviceData.device;
            device.deviceProfileId = newDpId;
            await apiCall(`/api/devices/${devEui}`, 'PUT', { device });
            log(`✓ ${device.name}: profil mis a jour`, 'success');
        } catch (err) {
            log(`✗ ${devEui}: ${err.message}`, 'error');
        }
        await new Promise(r => setTimeout(r, 50));
    }
}
```

### Detail de la liste
Le tableau doit afficher le Device Profile actuel pour chaque device, pour que l'utilisateur sache ce qu'il change :
```
[ ] | Nom | DevEUI | Profil actuel | Dernier vu
```

### Estimation
~150 lignes (HTML + JS). Beaucoup de reutilisation du pattern delete.

---

## Phase 4 : Validation pre-import

### Objectif
Avant d'appeler l'API, verifier cote client les formats et afficher les erreurs en rouge dans l'apercu. Evite de decouvrir les erreurs une par une pendant l'import.

### Regles de validation
| Champ | Regle | Message |
|-------|-------|---------|
| `dev_eui` | Exactement 16 caracteres hex `[0-9a-fA-F]` | "DevEUI invalide (16 hex attendus)" |
| `app_key` | Exactement 32 caracteres hex (si renseigne) | "AppKey invalide (32 hex attendus)" |
| `device_profile_id` | Format UUID 32 hex (si utilise depuis CSV) | "Device Profile ID invalide (UUID attendu)" |
| `name` | Non vide (si mappe) | "Nom vide" |
| `dev_eui` doublons | Pas de DevEUI en double dans le CSV lui-meme | "DevEUI en doublon dans le fichier" |

### Nouvelle fonction `validateImportData()`
```js
function validateImportData() {
    const mapping = getMapping();
    if (!mapping.dev_eui) return { valid: false, errors: ['Mapping dev_eui obligatoire'] };

    const errors = []; // { row: index, field: string, message: string }
    const seenDevEuis = new Set();

    csvData.forEach((row, i) => {
        const devEui = (row[mapping.dev_eui] || '').trim();

        // DevEUI : 16 hex
        if (!devEui || !/^[0-9a-fA-F]{16}$/.test(devEui)) {
            errors.push({ row: i, field: 'dev_eui', message: 'DevEUI invalide (16 hex attendus)' });
        }

        // Doublon interne
        if (seenDevEuis.has(devEui.toLowerCase())) {
            errors.push({ row: i, field: 'dev_eui', message: 'DevEUI en doublon dans le fichier' });
        }
        seenDevEuis.add(devEui.toLowerCase());

        // AppKey : 32 hex si renseigne
        if (mapping.app_key) {
            const appKey = (row[mapping.app_key] || '').trim();
            if (appKey && !/^[0-9a-fA-F]{32}$/.test(appKey)) {
                errors.push({ row: i, field: 'app_key', message: 'AppKey invalide (32 hex attendus)' });
            }
        }

        // Device Profile ID : UUID si utilise depuis CSV
        if (mapping.device_profile_id && !document.getElementById('deviceProfileSelect').value) {
            const dpId = (row[mapping.device_profile_id] || '').trim();
            if (!dpId || !/^[0-9a-fA-F-]{32,36}$/.test(dpId)) {
                errors.push({ row: i, field: 'device_profile_id', message: 'Device Profile ID invalide' });
            }
        }
    });

    return { valid: errors.length === 0, errors };
}
```

### Modifications de `updatePreview()`
Apres le rendu du tableau d'apercu, appeler `validateImportData()` et colorer en rouge les cellules en erreur :
```js
function updatePreview() {
    // ... rendu existant ...

    // Validation
    const validation = validateImportData();
    if (!validation.valid) {
        // Mettre en rouge les lignes en erreur dans le tableau
        // Afficher un resume sous l'apercu
        document.getElementById('validationSummary').innerHTML =
            `⚠ ${validation.errors.length} erreur(s) detectee(s)`;
        document.getElementById('validationSummary').classList.remove('hidden');
        document.getElementById('importBtn').disabled = true;
    } else {
        document.getElementById('validationSummary').classList.add('hidden');
        document.getElementById('importBtn').disabled = false;
    }
}
```

### Modifications HTML
Ajouter sous la section `#previewSection` :
```html
<p id="validationSummary" class="hidden" style="color: var(--error); font-size: 0.9rem; margin-top: 0.75rem; font-weight: 500;"></p>
```

Dans le tableau d'apercu, les cellules en erreur recevront un style inline :
```css
td.cell-error {
    color: var(--error);
    border: 1px solid var(--error);
    background: rgba(255, 92, 92, 0.1);
}
```

### Modifications de `startImport()`
Au debut de `startImport()`, ajouter :
```js
const validation = validateImportData();
if (!validation.valid) {
    alert(`${validation.errors.length} erreur(s) de format detectee(s). Corrigez votre fichier.`);
    return;
}
```

### Estimation
~80 lignes (JS + CSS + HTML)

---

## Phase 5 : Recherche de device cross-app

### Objectif
Champ de recherche par DevEUI qui cherche dans toutes les applications du tenant.

### Nouvelle carte dans le Hub
```html
<div class="tool-card" onclick="showTool('search')">
    <svg><!-- icone loupe --></svg>
    <h3>Rechercher</h3>
    <p>Trouver un device par DevEUI dans toutes les applications</p>
</div>
```

### Nouveau sub-view `#searchSubView`
```html
<div id="searchSubView" class="tool-subview hidden">
    <div class="tool-subview-header">
        <button class="btn-back" onclick="backToToolsHub()">← Retour</button>
        <h2>Recherche de device</h2>
    </div>
    <div class="card" style="max-width: 700px; margin: 0 auto;">
        <label>DevEUI a rechercher</label>
        <div style="display: flex; gap: 0.75rem;">
            <input type="text" id="searchDevEui" placeholder="70B3D52DD3000001"
                   maxlength="16" style="flex: 1; text-transform: uppercase;">
            <button class="btn-primary" onclick="searchDevice()">Rechercher</button>
        </div>
        <div id="searchProgress" class="hidden" style="margin-top: 1rem;">
            <p class="progress-text" id="searchProgressText">Recherche...</p>
            <div class="progress-bar"><div class="progress-bar-fill" id="searchProgressBar"></div></div>
        </div>
        <div id="searchResults" class="hidden" style="margin-top: 1.5rem;"></div>
    </div>
</div>
```

### Logique JS
```js
async function searchDevice() {
    const devEui = document.getElementById('searchDevEui').value.trim().toLowerCase();
    if (!devEui || devEui.length < 4) { alert('Saisissez au moins 4 caracteres'); return; }

    const resultsDiv = document.getElementById('searchResults');
    const progress = document.getElementById('searchProgress');
    progress.classList.remove('hidden');
    resultsDiv.classList.add('hidden');

    const found = [];

    // Parcourir toutes les applications
    for (let i = 0; i < applications.length; i++) {
        const app = applications[i];
        document.getElementById('searchProgressText').textContent =
            `Recherche dans ${app.name} (${i+1}/${applications.length})...`;
        document.getElementById('searchProgressBar').style.width =
            Math.round(((i+1) / applications.length) * 100) + '%';

        try {
            const devices = await loadAllDevicesFromApp(app.id);
            devices.forEach(d => {
                if (d.devEui.toLowerCase().includes(devEui)) {
                    found.push({ ...d, applicationName: app.name, applicationId: app.id });
                }
            });
        } catch (e) { /* ignorer les erreurs d'acces */ }
    }

    // Afficher les resultats
    resultsDiv.classList.remove('hidden');
    if (found.length === 0) {
        resultsDiv.innerHTML = '<p style="color: var(--text-dim);">Aucun device trouve.</p>';
    } else {
        resultsDiv.innerHTML = `
            <p style="margin-bottom: 1rem;">${found.length} resultat(s)</p>
            <div class="preview-table">
                <table>
                    <thead><tr><th>DevEUI</th><th>Nom</th><th>Application</th><th>Profil</th><th>Dernier vu</th></tr></thead>
                    <tbody>${found.map(d => `
                        <tr>
                            <td style="font-family: 'JetBrains Mono', monospace;">${d.devEui}</td>
                            <td>${escapeHtml(d.name || '-')}</td>
                            <td>${escapeHtml(d.applicationName)}</td>
                            <td>${escapeHtml(d.deviceProfileName || '-')}</td>
                            <td>${d.lastSeenAt ? new Date(d.lastSeenAt).toLocaleString('fr-FR') : 'Jamais'}</td>
                        </tr>
                    `).join('')}</tbody>
                </table>
            </div>`;
    }
}
```

### Point d'attention
- Si le tenant a beaucoup d'applications avec beaucoup de devices, cette recherche peut etre lente. L'API ChirpStack ne propose pas de recherche globale par DevEUI, donc on est oblige de tout charger.
- Alternative rapide : tenter directement `GET /api/devices/{devEui}`. Si le device existe, on aura sa reponse avec l'`applicationId`. Mais ca ne marche qu'avec un DevEUI exact. On peut combiner les deux approches : d'abord essayer le GET direct, puis proposer une recherche etendue si pas trouve.

### Recherche directe optimisee (alternative)
```js
async function searchDevice() {
    const devEui = document.getElementById('searchDevEui').value.trim();

    // Si 16 caracteres exacts, tenter un GET direct (instantane)
    if (/^[0-9a-fA-F]{16}$/.test(devEui)) {
        try {
            const data = await apiCall(`/api/devices/${devEui}`);
            if (data.device) {
                // Trouve ! Afficher directement
                const appName = applications.find(a => a.id === data.device.applicationId)?.name || data.device.applicationId;
                // ... affichage ...
                return;
            }
        } catch (e) { /* pas trouve, continuer avec recherche etendue */ }
    }

    // Sinon : recherche partielle dans toutes les apps (lent)
    // ... code ci-dessus ...
}
```

### Estimation
~100 lignes (HTML + JS)

---

## Phase 6 : Compteur de devices dans le Hub

### Objectif
Afficher le nombre de devices de l'application courante sur les cartes du hub ("Export (47 devices)").

### Principe
Au chargement du hub (dans `selectApplication()` ou `backToToolsHub()`), faire un seul appel API `GET /api/devices?applicationId=X&limit=1` pour recuperer `totalCount` sans charger les devices.

### Modifications JS

**Nouvelle fonction :**
```js
async function loadHubDeviceCount() {
    try {
        const data = await apiCall(`/api/devices?applicationId=${selectedApplicationId}&limit=1`);
        const count = parseInt(data.totalCount) || 0;
        document.getElementById('hubDeviceCount').textContent = `${count} device(s)`;
    } catch (e) {
        document.getElementById('hubDeviceCount').textContent = '';
    }
}
```

**Appel dans `selectApplication()` :** apres `goToStep(3)`, appeler `loadHubDeviceCount()`.
**Appel dans `backToToolsHub()` :** appeler aussi `loadHubDeviceCount()` pour rafraichir apres une operation.

### Modifications HTML
Dans le hub, sous le nom de l'app, ajouter un compteur :
```html
<p style="color: var(--text-dim); font-size: 0.85rem;">
    Application : <span id="hubAppName">-</span>
    — <span id="hubDeviceCount" style="color: var(--accent);"></span>
</p>
```

### Estimation
~15 lignes

---

## Phase 7 : Export filtre

### Objectif
Dans l'outil d'export, pouvoir filtrer les devices avant telechargement par Device Profile, tag ou activite.

### Modifications HTML dans `#exportSubView`
Ajouter apres le bouton "Charger les devices", dans la card preview :
```html
<div id="exportFilters" class="hidden" style="margin-bottom: 1rem; padding: 1rem; background: var(--bg-input); border-radius: 8px;">
    <label>Filtrer par Device Profile</label>
    <select id="exportFilterDp" onchange="applyExportFilters()">
        <option value="">-- Tous --</option>
        <!-- Rempli dynamiquement -->
    </select>

    <label>Filtrer par activite</label>
    <select id="exportFilterActivity" onchange="applyExportFilters()">
        <option value="">-- Tous --</option>
        <option value="active">Actifs (vus < 24h)</option>
        <option value="inactive">Inactifs (vus > 24h)</option>
        <option value="never">Jamais vus</option>
    </select>

    <label>Filtrer par tag (cle=valeur)</label>
    <input type="text" id="exportFilterTag" placeholder="Ex: site=Paris" oninput="applyExportFilters()">
</div>
```

### Variables globales
```js
let exportFilteredDevices = []; // Sous-ensemble filtre de exportDevices
```

### Fonctions JS

```js
function applyExportFilters() {
    const dpFilter = document.getElementById('exportFilterDp').value;
    const activityFilter = document.getElementById('exportFilterActivity').value;
    const tagFilter = document.getElementById('exportFilterTag').value.trim();

    exportFilteredDevices = exportDevices.filter(d => {
        // Filtre Device Profile
        if (dpFilter && d.deviceProfileId !== dpFilter) return false;

        // Filtre activite
        if (activityFilter) {
            const now = new Date();
            if (activityFilter === 'active' && (!d.lastSeenAt || (now - new Date(d.lastSeenAt)) > 24*60*60*1000)) return false;
            if (activityFilter === 'inactive' && (!d.lastSeenAt || (now - new Date(d.lastSeenAt)) <= 24*60*60*1000)) return false;
            if (activityFilter === 'never' && d.lastSeenAt) return false;
        }

        // Filtre tag
        if (tagFilter && tagFilter.includes('=')) {
            const [key, val] = tagFilter.split('=').map(s => s.trim());
            if (!d.tags || !d.tags[key] || (val && d.tags[key] !== val)) return false;
        }

        return true;
    });

    renderExportPreview(); // Modifier pour utiliser exportFilteredDevices
    document.getElementById('exportDeviceCount').textContent =
        `${exportFilteredDevices.length} / ${exportDevices.length}`;
}
```

**Modifier `loadDevicesForExport()` :** apres le chargement, remplir le select DP avec les profils trouves et initialiser `exportFilteredDevices = [...exportDevices]`.

**Modifier `renderExportPreview()` et `downloadExport()` :** utiliser `exportFilteredDevices` au lieu de `exportDevices`.

### Estimation
~80 lignes (HTML + JS)

---

## Phase 8 : Copier-coller rapide

### Objectif
Boutons "copier" a cote des DevEUI et AppKey dans l'interface.

### Fonction utilitaire
```js
function copyToClipboard(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const original = btn.textContent;
        btn.textContent = '✓';
        btn.style.color = 'var(--success)';
        setTimeout(() => {
            btn.textContent = original;
            btn.style.color = '';
        }, 1500);
    });
}
```

### CSS
```css
.btn-copy {
    background: none;
    border: 1px solid var(--border);
    color: var(--text-dim);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    transition: all 0.2s;
    margin-left: 0.3rem;
}

.btn-copy:hover {
    border-color: var(--accent);
    color: var(--accent);
}
```

### Ou ajouter les boutons
1. **Log d'import** : dans la fonction `log()`, quand le message contient un DevEUI, ajouter un bouton copie
2. **Liste de suppression** : dans `renderDeleteList()`, a cote de la colonne DevEUI
3. **Liste d'export** : dans `renderExportPreview()`, a cote de la colonne DevEUI
4. **Resultats de recherche** : dans la phase 5 (si implementee)

**Exemple pour la colonne DevEUI dans les tableaux :**
```js
`<td>
    <span style="font-family: 'JetBrains Mono', monospace;">${d.devEui}</span>
    <button class="btn-copy" onclick="copyToClipboard('${d.devEui}', this)">copier</button>
</td>`
```

### Estimation
~30 lignes (CSS + JS), puis modification de 3-4 fonctions de rendu existantes

---

## Ordre d'implementation recommande

| Ordre | Phase | Fonctionnalite | Complexite | Dependances |
|-------|-------|---------------|------------|-------------|
| 1 | 8 | Copier-coller rapide | Faible | - |
| 2 | 6 | Compteur dans le hub | Faible | - |
| 3 | 4 | Validation pre-import | Moyenne | - |
| 4 | 1 | Annuler le dernier import | Moyenne | - |
| 5 | 7 | Export filtre | Moyenne | - |
| 6 | 3 | Changement de DP en masse | Moyenne | Pattern delete existant |
| 7 | 5 | Recherche cross-app | Moyenne | - |
| 8 | 2 | Migration entre apps | Haute | Pattern delete + export |

**Total estime : ~700 lignes ajoutees**

### Remarques
- Les phases 2 (migration) et 3 (changement DP) ajoutent de nouvelles cartes au hub. La grille passera de 5 a 7 cartes. Sur grand ecran ca tient en 3 colonnes (3+3+1), sur tablette 2 colonnes (2+2+2+1).
- La phase 5 (recherche) ajoute aussi une carte, donc 8 cartes au total. Envisager un regroupement visuel ou une separation "Outils principaux" / "Utilitaires".
- Toutes les phases sont independantes et peuvent etre implementees dans n'importe quel ordre.

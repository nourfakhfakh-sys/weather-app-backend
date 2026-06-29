# Weather App API — Backend Technical Assessment

**Candidat:** Nour ben Brahim
**Poste:** AI Engineer Intern — Backend (Tech Assessment #2)

## À propos de PM Accelerator

PM Accelerator est un organisme américain de développement professionnel pour
Product Managers, fondé par Dr. Nancy Li. Le programme accompagne des candidats
de tous niveaux pour décrocher des postes de Product Manager et d'AI Product
Manager, à travers du mentorat individuel, des bootcamps pratiques sur de vrais
produits, et un réseau d'anciens élèves actif.
🔗 https://www.linkedin.com/school/pmaccelerator/

## Ce que fait ce projet

Une API REST (FastAPI) permettant de :
1. **CREATE** — Soumettre un lieu (ville, code postal, landmark...) + une plage
   de dates → l'API valide le lieu et les dates, va chercher les températures
   journalières réelles (historiques ou prévisions) via l'API **Open-Meteo**
   (gratuite, sans clé), et stocke tout en base SQLite.
2. **READ** — Lister tous les enregistrements ou en récupérer un par id.
3. **UPDATE** — Modifier la plage de dates d'un enregistrement (les données
   météo sont automatiquement re-récupérées).
4. **DELETE** — Supprimer un enregistrement.
5. **EXPORT** — Exporter toute la base en `JSON`, `CSV`, `XML`, `Markdown` ou `PDF`.
6. **Bonus (API supplémentaire)** — Lien Google Maps + lien de recherche YouTube
   pour chaque lieu enregistré.

## Pourquoi Open-Meteo ?

Pas de clé API à gérer (pas de risque de blocage avant le deadline), gratuit,
fiable, et fournit à la fois géocodage + historique + prévisions.

## Stack technique

- **FastAPI** — API REST + documentation interactive auto-générée
- **SQLite** — persistance (`weather.db`, créée automatiquement)
- **httpx** — appels HTTP vers Open-Meteo
- **ReportLab** — génération de PDF

## Installation & lancement

```bash
# 1. Cloner le repo et se placer dans le dossier
cd weather-backend

# 2. Créer un environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer le serveur
uvicorn app.main:app --reload
```

L'API est disponible sur **http://127.0.0.1:8000**
Documentation interactive (Swagger) : **http://127.0.0.1:8000/docs**

## Exemples d'utilisation

### Créer un enregistrement
```bash
curl -X POST http://127.0.0.1:8000/weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Tunis", "start_date": "2026-07-01", "end_date": "2026-07-05"}'
```

### Lister tous les enregistrements
```bash
curl http://127.0.0.1:8000/weather
```

### Modifier un enregistrement
```bash
curl -X PUT http://127.0.0.1:8000/weather/1 \
  -H "Content-Type: application/json" \
  -d '{"end_date": "2026-07-10"}'
```

### Supprimer un enregistrement
```bash
curl -X DELETE http://127.0.0.1:8000/weather/1
```

### Exporter les données
```bash
curl -O http://127.0.0.1:8000/export/csv
curl -O http://127.0.0.1:8000/export/pdf
curl -O http://127.0.0.1:8000/export/json
curl -O http://127.0.0.1:8000/export/xml
curl -O http://127.0.0.1:8000/export/markdown
```

### Bonus — Maps et YouTube
```bash
curl http://127.0.0.1:8000/map/1
curl http://127.0.0.1:8000/youtube/1
```

## Validations implémentées

- Format de date (`YYYY-MM-DD`) et cohérence (`start_date <= end_date`)
- Plage future limitée à 16 jours (limite de l'API de prévisions Open-Meteo)
- Lieu invalide → `404 Not Found` avec message clair
- Lieu ambigu → "fuzzy match" automatique (premier résultat retourné par l'API
  de géocodage, qui classe par pertinence)

## Structure du projet

```
weather-backend/
├── app/
│   ├── main.py          # Routes FastAPI (CRUD + export + bonus)
│   ├── database.py      # Connexion + schéma SQLite
│   ├── weather_api.py   # Géocodage + récupération météo (Open-Meteo)
│   ├── models.py        # Schémas Pydantic
│   └── export.py        # Export JSON/CSV/XML/Markdown/PDF
├── requirements.txt
└── README.md
```

## Limitations connues / pistes d'amélioration

- Pas d'authentification utilisateur (non requis par l'assessment — pas de
  row-level security demandée).
- L'intégration YouTube renvoie un lien de recherche direct plutôt qu'un appel
  structuré à l'API YouTube Data v3 (qui nécessite une clé API) — facilement
  branchable en ajoutant `YOUTUBE_API_KEY` en variable d'environnement.

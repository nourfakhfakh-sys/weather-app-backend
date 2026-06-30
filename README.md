# Weather App API — Backend Technical Assessment

**Candidate:** Nour Fakhfakh
**Role:** AI Engineer Intern / Enineering Student 

## About PM Accelerator

Product Manager Accelerator is a US-based professional development company
founded by Dr. Nancy Li. The program helps aspiring and experienced Product
Managers land top-tier roles through one-on-one mentorship, hands-on bootcamps
where students build real products alongside engineers and data scientists,
and an active alumni network.
🔗 https://www.linkedin.com/school/pmaccelerator/

## What this project does

A REST API (FastAPI) that lets you:
1. **CREATE** — Submit a location (city, postal code, landmark...) and a date
   range → the API validates the location and dates, fetches real daily
   temperatures (historical or forecast) via the **Open-Meteo** API (free, no
   key required), and stores everything in a SQLite database.
2. **READ** — List all records or retrieve one by id.
3. **UPDATE** — Modify a record's date range (weather data is automatically
   re-fetched).
4. **DELETE** — Remove a record.
5. **EXPORT** — Export the entire database to `JSON`, `CSV`, `XML`, `Markdown`,
   or `PDF`.
6. **Bonus (additional API integration)** — Google Maps link and YouTube
   search link for each saved location.

## Why Open-Meteo?

No API key to manage (no risk of being blocked before the deadline), free,
reliable, and covers geocoding + historical data + forecasts in one provider.

## Tech stack

- **FastAPI** — REST API with auto-generated interactive docs
- **SQLite** — persistence (`weather.db`, created automatically)
- **httpx** — HTTP calls to Open-Meteo
- **ReportLab** — PDF export generation

## Installation & usage

```bash
# 1. Clone the repo and move into it
cd weather-backend

# 2. (Recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn app.main:app --reload
```

The API is available at **http://127.0.0.1:8000**
Interactive documentation (Swagger): **http://127.0.0.1:8000/docs**

## Usage examples

### Create a record
```bash
curl -X POST http://127.0.0.1:8000/weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Tunis", "start_date": "2026-07-01", "end_date": "2026-07-05"}'
```

### List all records
```bash
curl http://127.0.0.1:8000/weather
```

### Update a record
```bash
curl -X PUT http://127.0.0.1:8000/weather/1 \
  -H "Content-Type: application/json" \
  -d '{"end_date": "2026-07-10"}'
```

### Delete a record
```bash
curl -X DELETE http://127.0.0.1:8000/weather/1
```

### Export data
```bash
curl -O http://127.0.0.1:8000/export/csv
curl -O http://127.0.0.1:8000/export/pdf
curl -O http://127.0.0.1:8000/export/json
curl -O http://127.0.0.1:8000/export/xml
curl -O http://127.0.0.1:8000/export/markdown
```

### Bonus — Maps and YouTube
```bash
curl http://127.0.0.1:8000/map/1
curl http://127.0.0.1:8000/youtube/1
```

## Validations implemented

- Date format (`YYYY-MM-DD`) and logical consistency (`start_date <= end_date`)
- Future date range limited to 16 days (Open-Meteo forecast API limit)
- Invalid location → `404 Not Found` with a clear message
- Ambiguous location → automatic "fuzzy match" (first result returned by the
  geocoding API, which ranks by relevance)

## Project structure

```
weather-backend/
├── app/
│   ├── main.py          # FastAPI routes (CRUD + export + bonus)
│   ├── database.py      # SQLite connection + schema
│   ├── weather_api.py   # Geocoding + weather retrieval (Open-Meteo)
│   ├── models.py        # Pydantic schemas
│   └── export.py        # JSON/CSV/XML/Markdown/PDF export
├── requirements.txt
└── README.md
```

## Known limitations / improvement ideas

- No user authentication (not required by the assessment — no row-level
  security was requested).
- The YouTube integration returns a direct search link rather than a
  structured call to the YouTube Data API v3 (which requires an API key) —
  easy to plug in by adding a `YOUTUBE_API_KEY` environment variable.

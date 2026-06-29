
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import json

from app.database import init_db, get_connection
from app.models import WeatherCreateRequest, WeatherUpdateRequest
from app.weather_api import geocode_location, validate_date_range, fetch_temperatures
from app.export import EXPORTERS

app = FastAPI(
    title="Weather App API",
    description=(
        "API backend pour la Tech Assessment AI Engineer Intern (PM Accelerator). "
        "CRUD complet sur des requêtes météo géolocalisées + export multi-format."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


def _row_to_dict(row) -> dict:
    d = dict(row)
    d["temperature_data"] = json.loads(d["temperature_data"])
    return d


@app.get("/")
def root():
    return {
        "message": "Weather App API is running.",
        "author": "Nour ben Brahim",
        "about_pm_accelerator": (
            "PM Accelerator forme et accompagne les futurs Product Managers et AI PMs "
            "via du mentorat et des projets concrets en équipe. "
            "https://www.linkedin.com/school/pmaccelerator/"
        ),
        "docs": "/docs",
    }


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@app.post("/weather", status_code=201)
def create_weather_record(payload: WeatherCreateRequest):
    validate_date_range(payload.start_date, payload.end_date)
    geo = geocode_location(payload.location)
    temps = fetch_temperatures(geo["latitude"], geo["longitude"], payload.start_date, payload.end_date)

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO weather_records
                (location_query, resolved_name, country, latitude, longitude,
                 start_date, end_date, temperature_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.location,
                geo["resolved_name"],
                geo["country"],
                geo["latitude"],
                geo["longitude"],
                payload.start_date,
                payload.end_date,
                json.dumps(temps),
            ),
        )
        conn.commit()
        new_id = cur.lastrowid
        row = conn.execute("SELECT * FROM weather_records WHERE id = ?", (new_id,)).fetchone()

    return _row_to_dict(row)


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------
@app.get("/weather")
def list_weather_records():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM weather_records ORDER BY id DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


@app.get("/weather/{record_id}")
def get_weather_record(record_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM weather_records WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Enregistrement introuvable.")
    return _row_to_dict(row)


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
@app.put("/weather/{record_id}")
def update_weather_record(record_id: int, payload: WeatherUpdateRequest):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM weather_records WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Enregistrement introuvable.")
        record = dict(row)

        new_start = payload.start_date or record["start_date"]
        new_end = payload.end_date or record["end_date"]
        validate_date_range(new_start, new_end)

        # Si la plage de dates change, on re-fetch la météo pour rester cohérent
        temps = fetch_temperatures(record["latitude"], record["longitude"], new_start, new_end)

        conn.execute(
            """
            UPDATE weather_records
            SET start_date = ?, end_date = ?, temperature_data = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_start, new_end, json.dumps(temps), record_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM weather_records WHERE id = ?", (record_id,)).fetchone()

    return _row_to_dict(updated)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
@app.delete("/weather/{record_id}", status_code=204)
def delete_weather_record(record_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM weather_records WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Enregistrement introuvable.")
        conn.execute("DELETE FROM weather_records WHERE id = ?", (record_id,))
        conn.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# EXPORT (2.3)
# ---------------------------------------------------------------------------
@app.get("/export/{fmt}")
def export_data(fmt: str):
    fmt = fmt.lower()
    if fmt not in EXPORTERS:
        raise HTTPException(status_code=400, detail=f"Format non supporté. Choisir parmi: {list(EXPORTERS)}")

    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM weather_records ORDER BY id").fetchall()
    records = [_row_to_dict(r) for r in rows]

    exporter_fn, media_type, filename = EXPORTERS[fmt]
    content = exporter_fn(records)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# BONUS — Intégration API supplémentaire (2.2): Google Maps + YouTube
# ---------------------------------------------------------------------------
@app.get("/map/{record_id}")
def get_map_link(record_id: int):
    """Renvoie un lien Google Maps pointant sur le lieu (pas de clé API requise)."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM weather_records WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Enregistrement introuvable.")
    lat, lon = row["latitude"], row["longitude"]
    return {
        "location": row["resolved_name"],
        "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
        "embed_url": f"https://maps.google.com/maps?q={lat},{lon}&z=10&output=embed",
    }


@app.get("/youtube/{record_id}")
def get_youtube_search_link(record_id: int):
    """
    Renvoie un lien de recherche YouTube pour le lieu.
    (Recherche directe sans clé API ; pour des résultats structurés JSON,
    brancher la clé YOUTUBE_API_KEY dans une variable d'environnement et
    appeler https://www.googleapis.com/youtube/v3/search.)
    """
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM weather_records WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Enregistrement introuvable.")
    query = f"{row['resolved_name']} {row['country']} travel guide".replace(" ", "+")
    return {"youtube_search_url": f"https://www.youtube.com/results?search_query={query}"}

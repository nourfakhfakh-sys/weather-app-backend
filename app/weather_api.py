
import httpx
from datetime import date, datetime
from fastapi import HTTPException

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def geocode_location(location_query: str) -> dict:
    """
    Résout un nom de lieu (ville, landmark, etc.) en coordonnées.
    Fait un "fuzzy match" simple en prenant le premier résultat retourné par l'API.
    Lève une HTTPException 404 si rien n'est trouvé -> validation du lieu.
    """
    try:
        resp = httpx.get(
            GEOCODING_URL,
            params={"name": location_query, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Erreur API de géocodage: {exc}")

    results = data.get("results")
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Lieu introuvable: '{location_query}'. Essayez un nom de ville plus précis.",
        )

    best = results[0]
    return {
        "resolved_name": best.get("name"),
        "country": best.get("country"),
        "latitude": best.get("latitude"),
        "longitude": best.get("longitude"),
    }


def validate_date_range(start_date: str, end_date: str) -> None:
    """Valide le format et la cohérence logique de la plage de dates."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Les dates doivent être au format YYYY-MM-DD.")

    if start > end:
        raise HTTPException(status_code=400, detail="start_date doit être antérieure ou égale à end_date.")

    # Open-Meteo forecast API ne couvre que ~16 jours dans le futur
    delta_future = (end - date.today()).days
    if delta_future > 16:
        raise HTTPException(
            status_code=400,
            detail="end_date trop loin dans le futur (max 16 jours de prévision supportés).",
        )


def fetch_temperatures(latitude: float, longitude: float, start_date: str, end_date: str) -> list[dict]:
    """
    Récupère les températures journalières (min/max) pour une plage de dates.
    Bascule automatiquement entre l'API historique (passé) et l'API de prévisions (futur).
    """
    today = date.today()
    start = datetime.strptime(start_date, "%Y-%m-%d").date()

    url = ARCHIVE_URL if start < today else FORECAST_URL

    try:
        resp = httpx.get(
            url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Erreur API météo: {exc}")

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])

    return [
        {
            "date": dates[i],
            "temp_max_c": tmax[i] if i < len(tmax) else None,
            "temp_min_c": tmin[i] if i < len(tmin) else None,
            "precipitation_mm": precip[i] if i < len(precip) else None,
        }
        for i in range(len(dates))
    ]

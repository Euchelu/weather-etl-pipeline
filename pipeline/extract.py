import requests
import logging
from typing import Any

logger = logging.getLogger(__name__)

API_URL = "https://api.open-meteo.com/v1/forecast"

CITIES = {
    "Madrid":   {"latitude": 40.4168, "longitude": -3.7038},
    "Sevilla":  {"latitude": 37.3886, "longitude": -5.9823},
    "Barcelona":{"latitude": 41.3851, "longitude": 2.1734},
    "Valencia": {"latitude": 39.4699, "longitude": -0.3763},
}

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "precipitation",
    "weather_code",
]


def fetch_weather(city: str, days: int = 1) -> dict[str, Any]:
    """
    Llama a la API de Open-Meteo y devuelve los datos crudos de una ciudad.
    Lanza ValueError si la ciudad no está soportada.
    Lanza requests.HTTPError si la API falla.
    """
    if city not in CITIES:
        raise ValueError(f"Ciudad '{city}' no soportada. Opciones: {list(CITIES)}")

    coords = CITIES[city]
    params = {
        **coords,
        "hourly": ",".join(HOURLY_VARIABLES),
        "forecast_days": days,
        "timezone": "Europe/Madrid",
    }

    logger.info(f"[EXTRACT] Fetching weather for {city}...")
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json().copy()  # evita mutar el objeto si el caller reutiliza la respuesta
    data["city"] = city
    logger.info(f"[EXTRACT] {len(data['hourly']['time'])} records fetched for {city}")
    return data


def fetch_all_cities(days: int = 1) -> list[dict[str, Any]]:
    """Extrae datos de todas las ciudades configuradas."""
    results = []
    for city in CITIES:
        try:
            results.append(fetch_weather(city, days))
        except Exception as e:
            logger.error(f"[EXTRACT] Failed for {city}: {e}")
    return results

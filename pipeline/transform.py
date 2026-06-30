import pandas as pd
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Mapping de WMO weather codes a descripciones legibles
WEATHER_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail",
}


def _classify_temperature(temp: float) -> str:
    """Clasifica la temperatura en una categoría descriptiva."""
    if temp < 0:
        return "freezing"
    elif temp < 10:
        return "cold"
    elif temp < 18:
        return "cool"
    elif temp < 25:
        return "comfortable"
    elif temp < 32:
        return "warm"
    return "hot"


def transform(raw_data: dict[str, Any]) -> pd.DataFrame:
    """
    Transforma los datos crudos de la API en un DataFrame limpio y enriquecido.

    Pasos:
    1. Aplana la estructura hourly en columnas
    2. Renombra columnas a nombres claros
    3. Convierte tipos (datetime, float)
    4. Elimina filas con nulos en columnas críticas
    5. Añade columnas calculadas (temp_category, weather_description)
    6. Añade columna city
    """
    city = raw_data["city"]
    hourly = raw_data["hourly"]

    df = pd.DataFrame({
        "timestamp":   hourly["time"],
        "temperature": hourly["temperature_2m"],
        "humidity":    hourly["relative_humidity_2m"],
        "wind_speed":  hourly["wind_speed_10m"],
        "precipitation": hourly["precipitation"],
        "weather_code":  hourly["weather_code"],
    })

    # Tipos correctos
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["temperature"] = df["temperature"].astype(float)
    df["humidity"] = df["humidity"].astype(float)
    df["wind_speed"] = df["wind_speed"].astype(float)
    df["precipitation"] = df["precipitation"].astype(float)
    df["weather_code"] = df["weather_code"].astype(int)

    # Eliminar filas sin temperatura (dato crítico)
    before = len(df)
    df = df.dropna(subset=["temperature"])
    dropped = before - len(df)
    if dropped:
        logger.warning(f"[TRANSFORM] Dropped {dropped} rows with null temperature for {city}")

    # Columnas enriquecidas
    df["temp_category"] = df["temperature"].apply(_classify_temperature)
    df["weather_description"] = df["weather_code"].map(WEATHER_DESCRIPTIONS).fillna("Unknown")
    df["city"] = city

    logger.info(f"[TRANSFORM] {len(df)} records transformed for {city}")
    return df


def transform_all(raw_list: list[dict[str, Any]]) -> pd.DataFrame:
    """Transforma y combina datos de múltiples ciudades en un único DataFrame."""
    frames = [transform(raw) for raw in raw_list]
    combined = pd.concat(frames, ignore_index=True)
    logger.info(f"[TRANSFORM] Total records after merge: {len(combined)}")
    return combined

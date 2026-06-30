import logging
import sys
from pipeline.extract import fetch_all_cities, fetch_weather, CITIES
from pipeline.transform import transform_all, transform
from pipeline.load import load, get_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_pipeline(cities: list[str] | None = None, days: int = 1) -> dict:
    """
    Ejecuta el pipeline ETL completo: Extract → Transform → Load.

    Args:
        cities: lista de ciudades a procesar. Si es None, procesa todas.
        days: número de días de pronóstico a extraer (1-7).

    Returns:
        Diccionario con estadísticas de la ejecución.
    """
    logger.info("=" * 50)
    logger.info("STARTING ETL PIPELINE")
    logger.info("=" * 50)

    # ── EXTRACT ──────────────────────────────────────────
    if cities:
        raw_data = []
        for city in cities:
            try:
                raw_data.append(fetch_weather(city, days))
            except Exception as e:
                logger.error(f"[EXTRACT] Skipping {city}: {e}")
    else:
        raw_data = fetch_all_cities(days)

    if not raw_data:
        logger.error("No data extracted. Aborting pipeline.")
        return {"status": "failed", "extracted": 0, "inserted": 0}

    extracted_cities = [d["city"] for d in raw_data]
    logger.info(f"[EXTRACT] Done — cities: {extracted_cities}")

    # ── TRANSFORM ─────────────────────────────────────────
    df = transform_all(raw_data)
    logger.info(f"[TRANSFORM] Done — {len(df)} records ready to load")

    # ── LOAD ──────────────────────────────────────────────
    engine = get_engine()
    inserted = load(df, engine)
    logger.info(f"[LOAD] Done — {inserted} rows inserted into weather_hourly")

    logger.info("=" * 50)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 50)

    return {
        "status": "success",
        "extracted": len(raw_data),
        "transformed": len(df),
        "inserted": inserted,
        "cities": extracted_cities,
    }


if __name__ == "__main__":
    result = run_pipeline()
    print(f"\nResult: {result}")

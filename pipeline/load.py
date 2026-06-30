import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./weather.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS weather_hourly (
    id              SERIAL PRIMARY KEY,
    city            VARCHAR(100) NOT NULL,
    timestamp       TIMESTAMP NOT NULL,
    temperature     FLOAT,
    humidity        FLOAT,
    wind_speed      FLOAT,
    precipitation   FLOAT,
    weather_code    INT,
    temp_category       VARCHAR(20),
    weather_description VARCHAR(100),
    loaded_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (city, timestamp)
);
"""

# SQLite uses AUTOINCREMENT syntax differently — keep it compatible
CREATE_TABLE_SQLITE = """
CREATE TABLE IF NOT EXISTS weather_hourly (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    city                TEXT NOT NULL,
    timestamp           TEXT NOT NULL,
    temperature         REAL,
    humidity            REAL,
    wind_speed          REAL,
    precipitation       REAL,
    weather_code        INTEGER,
    temp_category       TEXT,
    weather_description TEXT,
    loaded_at           TEXT DEFAULT (datetime('now')),
    UNIQUE (city, timestamp)
);
"""


def get_engine():
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    return create_engine(DATABASE_URL, connect_args=connect_args)


def ensure_table(engine) -> None:
    """Crea la tabla si no existe."""
    sql = CREATE_TABLE_SQLITE if DATABASE_URL.startswith("sqlite") else CREATE_TABLE_SQL
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()


def load(df: pd.DataFrame, engine=None) -> int:
    """
    Carga el DataFrame en la tabla weather_hourly.
    Inserta fila a fila con INSERT OR IGNORE para saltarse duplicados
    por (city, timestamp) sin lanzar excepciones.
    Devuelve el número de filas efectivamente insertadas.
    """
    if engine is None:
        engine = get_engine()

    ensure_table(engine)

    columns = [
        "city", "timestamp", "temperature", "humidity",
        "wind_speed", "precipitation", "weather_code",
        "temp_category", "weather_description",
    ]
    df_to_load = df[columns].copy()

    insert_sql = text("""
        INSERT OR IGNORE INTO weather_hourly
            (city, timestamp, temperature, humidity, wind_speed,
             precipitation, weather_code, temp_category, weather_description)
        VALUES
            (:city, :timestamp, :temperature, :humidity, :wind_speed,
             :precipitation, :weather_code, :temp_category, :weather_description)
    """)

    rows_before = _count_rows(engine)
    with engine.begin() as conn:
        for row in df_to_load.itertuples(index=False):
            conn.execute(insert_sql, row._asdict())
    rows_after = _count_rows(engine)
    inserted = rows_after - rows_before

    logger.info(f"[LOAD] {inserted} new rows inserted ({len(df_to_load) - inserted} duplicates skipped)")
    return inserted


def _count_rows(engine) -> int:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM weather_hourly"))
        return result.scalar()

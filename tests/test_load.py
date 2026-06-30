import pytest
import pandas as pd
from sqlalchemy import create_engine, text
from pipeline.load import load, ensure_table, _count_rows


@pytest.fixture
def engine():
    """Base de datos SQLite en memoria para cada test."""
    e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    yield e
    e.dispose()


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "city":                ["Madrid", "Sevilla"],
        "timestamp":           ["2024-01-01 00:00:00", "2024-01-01 00:00:00"],
        "temperature":         [10.5, 20.0],
        "humidity":            [70.0, 55.0],
        "wind_speed":          [15.0, 8.0],
        "precipitation":       [0.0, 0.0],
        "weather_code":        [1, 0],
        "temp_category":       ["cold", "comfortable"],
        "weather_description": ["Mainly clear", "Clear sky"],
    })


def test_ensure_table_creates_table(engine):
    import os
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    ensure_table(engine)
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='weather_hourly'"
        ))
        assert result.fetchone() is not None


def test_load_inserts_rows(engine, sample_df):
    inserted = load(sample_df, engine)
    assert inserted == 2


def test_load_returns_correct_count(engine, sample_df):
    load(sample_df, engine)
    assert _count_rows(engine) == 2


def test_load_skips_duplicates(engine, sample_df):
    load(sample_df, engine)
    inserted_second = load(sample_df, engine)
    # Las mismas filas (city + timestamp) no deben duplicarse
    assert _count_rows(engine) == 2
    assert inserted_second == 0


def test_load_partial_new_rows(engine, sample_df):
    load(sample_df, engine)

    new_row = pd.DataFrame({
        "city":                ["Barcelona"],
        "timestamp":           ["2024-01-01 00:00:00"],
        "temperature":         [15.0],
        "humidity":            [65.0],
        "wind_speed":          [10.0],
        "precipitation":       [0.0],
        "weather_code":        [2],
        "temp_category":       ["cool"],
        "weather_description": ["Partly cloudy"],
    })
    combined = pd.concat([sample_df, new_row], ignore_index=True)
    inserted = load(combined, engine)

    assert inserted == 1
    assert _count_rows(engine) == 3

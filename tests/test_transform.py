import pytest
import pandas as pd
from pipeline.transform import transform, transform_all, _classify_temperature


RAW_MADRID = {
    "city": "Madrid",
    "hourly": {
        "time":                  ["2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00"],
        "temperature_2m":        [5.0, None, 22.0],
        "relative_humidity_2m":  [80, 82, 60],
        "wind_speed_10m":        [10.0, 12.0, 8.0],
        "precipitation":         [0.0, 0.1, 0.0],
        "weather_code":          [1, 61, 0],
    }
}

RAW_SEVILLA = {
    "city": "Sevilla",
    "hourly": {
        "time":                  ["2024-01-01T00:00", "2024-01-01T01:00"],
        "temperature_2m":        [18.0, 19.0],
        "relative_humidity_2m":  [55, 57],
        "wind_speed_10m":        [5.0, 6.0],
        "precipitation":         [0.0, 0.0],
        "weather_code":          [0, 0],
    }
}


# ── _classify_temperature ─────────────────────────────────────────────────────

@pytest.mark.parametrize("temp,expected", [
    (-5.0, "freezing"),
    (5.0,  "cold"),
    (14.0, "cool"),
    (20.0, "comfortable"),
    (28.0, "warm"),
    (35.0, "hot"),
])
def test_classify_temperature(temp, expected):
    assert _classify_temperature(temp) == expected


# ── transform ─────────────────────────────────────────────────────────────────

def test_transform_returns_dataframe():
    df = transform(RAW_MADRID)
    assert isinstance(df, pd.DataFrame)


def test_transform_drops_null_temperature():
    df = transform(RAW_MADRID)
    # RAW_MADRID tiene 3 filas pero 1 con None en temperatura
    assert len(df) == 2
    assert df["temperature"].isnull().sum() == 0


def test_transform_has_required_columns():
    df = transform(RAW_MADRID)
    required = {"city", "timestamp", "temperature", "humidity",
                "wind_speed", "precipitation", "weather_code",
                "temp_category", "weather_description"}
    assert required.issubset(set(df.columns))


def test_transform_city_column():
    df = transform(RAW_MADRID)
    assert (df["city"] == "Madrid").all()


def test_transform_temp_category():
    df = transform(RAW_MADRID)
    # 5.0 → cold, 22.0 → comfortable
    categories = df["temp_category"].tolist()
    assert "cold" in categories
    assert "comfortable" in categories


def test_transform_weather_description():
    df = transform(RAW_MADRID)
    # weather_code 0 → "Clear sky", 1 → "Mainly clear", 61 → "Slight rain"
    descriptions = df["weather_description"].tolist()
    assert "Clear sky" in descriptions or "Mainly clear" in descriptions


def test_transform_timestamp_is_datetime():
    df = transform(RAW_MADRID)
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])


# ── transform_all ─────────────────────────────────────────────────────────────

def test_transform_all_combines_cities():
    df = transform_all([RAW_MADRID, RAW_SEVILLA])
    cities = df["city"].unique().tolist()
    assert "Madrid" in cities
    assert "Sevilla" in cities


def test_transform_all_row_count():
    df = transform_all([RAW_MADRID, RAW_SEVILLA])
    # Madrid: 2 filas válidas + Sevilla: 2 filas = 4
    assert len(df) == 4

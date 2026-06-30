import pytest
from unittest.mock import patch, MagicMock
from pipeline.extract import fetch_weather, fetch_all_cities, CITIES


MOCK_API_RESPONSE = {
    "hourly": {
        "time":                  ["2024-01-01T00:00", "2024-01-01T01:00"],
        "temperature_2m":        [10.5, 11.0],
        "relative_humidity_2m":  [70, 72],
        "wind_speed_10m":        [15.0, 14.5],
        "precipitation":         [0.0, 0.0],
        "weather_code":          [1, 1],
    }
}


def test_fetch_weather_valid_city():
    with patch("pipeline.extract.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_API_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_weather("Madrid")

        assert result["city"] == "Madrid"
        assert "hourly" in result
        assert len(result["hourly"]["time"]) == 2
        mock_get.assert_called_once()


def test_fetch_weather_invalid_city():
    with pytest.raises(ValueError, match="no soportada"):
        fetch_weather("Atlantis")


def test_fetch_weather_api_error():
    with patch("pipeline.extract.requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection error")
        with pytest.raises(Exception):
            fetch_weather("Madrid")


def test_fetch_all_cities_returns_all():
    with patch("pipeline.extract.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_API_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        results = fetch_all_cities()

        assert len(results) == len(CITIES)
        cities_returned = [r["city"] for r in results]
        for city in CITIES:
            assert city in cities_returned


def test_fetch_all_cities_skips_failed():
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("API down")
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_API_RESPONSE
        mock_response.raise_for_status = MagicMock()
        return mock_response

    with patch("pipeline.extract.requests.get", side_effect=side_effect):
        results = fetch_all_cities()
        # Una ciudad falló pero el resto se procesaron
        assert len(results) == len(CITIES) - 1

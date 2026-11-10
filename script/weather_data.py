"""Load and query the local weather forecast database."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class WeatherDataRepository:
    """Provides access to weather forecasts stored in the project database."""

    def __init__(self) -> None:
        database_path = (
            Path(__file__).resolve().parent.parent
            / "database"
            / "malaysia_weather.json"
        )
        with database_path.open("r", encoding="utf-8") as file:
            self.data: dict[str, dict[str, Any]] = json.load(file)

    @property
    def states(self) -> list[str]:
        return list(self.data)

    def get_place(self, state: str) -> dict[str, Any]:
        return self.data[state]

    def get_hourly_forecast(self, state: str) -> list[dict[str, Any]]:
        return self.data[state]["hours"]

    def get_city_data(
        self, state: str, hour: int | None = None
    ) -> dict[str, Any] | None:
        place = self.get_place(state)
        forecast_hour = datetime.now().hour if hour is None else hour
        forecast_hour = max(6, min(20, forecast_hour))

        for entry in self.get_hourly_forecast(state):
            if entry["hour"] == forecast_hour:
                return {
                    "name": place["city"],
                    "temperature": entry["temp_c"],
                    "humidity": entry["humidity_pct"],
                    "uv_index": entry["uv_index"],
                    "rain_chance": entry["rain_chance_pct"],
                }
        return None

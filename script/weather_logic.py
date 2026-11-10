"""Weather-planning, comparison, activity, and hydration business rules."""

from typing import Any

from weather_data import WeatherDataRepository


class WeatherPlannerLogic:
    """Calculates recommendations and summaries from weather forecasts."""

    def __init__(self, weather_data: WeatherDataRepository) -> None:
        self.weather_data = weather_data

    def calculate_activity_score(self, entry: dict[str, Any]) -> int:
        score = 100
        temperature = entry["temp_c"]

        if temperature < 12:
            score -= (12 - temperature) * 3
        elif temperature > 26:
            score -= (temperature - 26) * 3.5

        score -= entry["rain_chance_pct"] * 0.4
        score -= max(0, entry["uv_index"] - 6) * 2
        return max(0, min(100, int(score)))

    def score_hours(self, state: str) -> list[tuple[dict[str, Any], int]]:
        return [
            (entry, self.calculate_activity_score(entry))
            for entry in self.weather_data.get_hourly_forecast(state)
        ]

    def create_plan(self, state: str) -> str:
        place = self.weather_data.get_place(state)
        scored_hours = sorted(
            self.score_hours(state), key=lambda item: item[1], reverse=True
        )
        if not scored_hours:
            return f"No weather forecast found for {place['city']}."

        best_entry, best_score = scored_hours[0]
        return (
            f"{place['city']} today's plan\n"
            f"Best time for outdoor activities: {best_entry['hour']:02d}:00 "
            f"(Score: {best_score}/100)"
        )

    def get_activity_advice(
        self, weather: dict[str, Any]
    ) -> tuple[str, list[str]]:
        if weather["rain_chance"] >= 60:
            return "It will likely rain. Stay indoors.", [
                "Visit a mall or a museum",
                "Workout at the gym",
                "Play board games or watch a movie",
            ]
        if weather["uv_index"] >= 8:
            return "The sun is very strong. Avoid long time outside.", [
                "Go swimming",
                "Play indoor sports like badminton",
                "Go outside again in the evening",
            ]
        if weather["temperature"] >= 33:
            return "It is quite hot. Keep your activities light.", [
                "Take a short walk in a shaded area",
                "Have a picnic under the trees",
                "Go swimming",
            ]
        return "The weather is great for outdoor activities.", [
            "Go jogging or cycling",
            "Play football or badminton at the park",
            "Have a picnic",
        ]

    def calculate_comfort_score(self, weather: dict[str, Any]) -> int:
        score = 100
        temperature = weather["temperature"]

        if temperature < 12:
            score -= (12 - temperature) * 3
        elif temperature > 26:
            score -= (temperature - 26) * 3.5

        score -= weather["rain_chance"] * 0.4
        return max(0, min(100, int(score)))

    def compare_cities(
        self, city_a: dict[str, Any], city_b: dict[str, Any]
    ) -> tuple[int, int, list[str], str]:
        temperature_difference = round(
            city_a["temperature"] - city_b["temperature"], 1
        )
        score_a = self.calculate_comfort_score(city_a)
        score_b = self.calculate_comfort_score(city_b)
        verdicts = []

        if abs(temperature_difference) < 1.0:
            verdicts.append(
                f"Both cities share similar temperatures "
                f"(~{city_a['temperature']}°C)."
            )
        elif temperature_difference > 0:
            verdicts.append(
                f"{city_a['name']} is {temperature_difference}°C warmer "
                f"than {city_b['name']}."
            )
        else:
            verdicts.append(
                f"{city_b['name']} is {abs(temperature_difference)}°C warmer "
                f"than {city_a['name']}."
            )

        if city_a["rain_chance"] != city_b["rain_chance"]:
            drier = (
                city_a["name"]
                if city_a["rain_chance"] < city_b["rain_chance"]
                else city_b["name"]
            )
            verdicts.append(f"{drier} has a lower chance of precipitation.")

        recommended_city, recommended_score = (
            (city_a, score_a) if score_a >= score_b else (city_b, score_b)
        )
        recommendation = (
            f"{recommended_city['name']} is recommended for outdoor activities "
            f"today (Score: {recommended_score}/100)."
        )
        return score_a, score_b, verdicts, recommendation

    def calculate_feels_like(self, temperature: float, humidity: float) -> float:
        temperature_f = temperature * 9 / 5 + 32
        if temperature_f < 80 or humidity < 40:
            return temperature

        heat_index_f = (
            -42.379
            + 2.04901523 * temperature_f
            + 10.14333127 * humidity
            - 0.22475541 * temperature_f * humidity
            - 0.00683783 * temperature_f**2
            - 0.05481717 * humidity**2
            + 0.00122874 * temperature_f**2 * humidity
            + 0.00085282 * temperature_f * humidity**2
            - 0.00000199 * temperature_f**2 * humidity**2
        )
        return round((heat_index_f - 32) * 5 / 9, 1)

    def calculate_hydration(
        self, temperature: float, humidity: float, uv_index: float
    ) -> dict[str, Any]:
        feels_like = self.calculate_feels_like(temperature, humidity)
        water_ml = 250

        if feels_like >= 41:
            level = "Danger"
            water_ml += 500
            advice = (
                "Avoid outdoor activity. Drink water often and rest in the shade "
                "or indoors."
            )
        elif feels_like >= 32:
            level = "High"
            water_ml += 350
            advice = "Drink water every 15 to 20 minutes and take regular shade breaks."
        elif feels_like >= 27:
            level = "Moderate"
            water_ml += 150
            advice = "Drink water regularly and do not wait until you feel thirsty."
        else:
            level = "Low"
            advice = "Comfortable conditions. Normal water intake is fine."

        if uv_index >= 8:
            water_ml += 100

        return {
            "feels_like": feels_like,
            "level": level,
            "water_ml": water_ml,
            "advice": advice,
        }

    def create_hydration_summary(self, state: str) -> tuple[str, str] | None:
        current = self.weather_data.get_city_data(state)
        if current is None:
            return None

        result = self.calculate_hydration(
            current["temperature"], current["humidity"], current["uv_index"]
        )
        summary = (
            f"{current['name']} hydration safety (now)\n"
            f"Temperature: {current['temperature']}°C "
            f"(feels like {result['feels_like']}°C)\n"
            f"Humidity: {current['humidity']}%   UV index: {current['uv_index']}\n"
            f"Risk level: {result['level']}\n"
            f"Suggested water: about {result['water_ml']} ml per hour\n"
            f"{result['advice']}"
        )
        return summary, result["level"]

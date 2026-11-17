# BUSINESS LOGIC LAYER
# This file holds calculations, decisions, and color utilities.

class TodaysPlanner:

    def __init__(self, weather_data):
        self.weather_data = weather_data

    def calculate_score(self, entry):
        score = 100
        temperature = entry["temp_c"]

        if temperature < 12:
            score -= (12 - temperature) * 3
        elif temperature > 26:
            score -= (temperature - 26) * 3.5

        score -= entry["rain_chance_pct"] * 0.4
        score -= max(0, entry["uv_index"] - 6) * 2
        return max(0, min(100, int(score)))

    def score_hours(self, state):
        results = []
        for entry in self.weather_data.get_hours(state):
            score = self.calculate_score(entry)
            results.append({"entry": entry, "score": score})
        return results

    def create_plan(self, state):
        city = self.weather_data.get_city_name(state)
        scored_hours = self.score_hours(state)

        best = scored_hours[0]
        for item in scored_hours:
            if item["score"] > best["score"]:
                best = item

        best_hour = best["entry"]["hour"]
        best_score = best["score"]

        return (
            f"📍 {city} Today's Plan\n"
            f"🌟 Best Outdoor Window: {best_hour:02d}:00 "
            f"(Score: {best_score}/100)"
        )


class ActivityAdvisor:

    def __init__(self, weather_data):
        self.weather_data = weather_data

    def get_advice(self, weather):
        if weather["rain_chance"] >= 60:
            verdict = "🌧️ Rain expected. Recommended indoor pursuits:"
            activities = [
                "Visit a local mall or museum",
                "Workout at the indoor gym",
                "Enjoy board games or a movie marathon",
            ]
        elif weather["uv_index"] >= 8:
            verdict = "☀️ Extremely high UV index. Limit direct sun exposure:"
            activities = [
                "Indoor swimming session",
                "Play indoor badminton or squash",
                "Step outdoors during evening hours",
            ]
        elif weather["temperature"] >= 33:
            verdict = "🌡️ High temperature alert. Keep exertion light:"
            activities = [
                "Take a shaded park stroll",
                "Relax at a shaded garden picnic",
                "Indoor water sports / swimming",
            ]
        else:
            verdict = "✨ Pristine weather conditions for outdoor activities:"
            activities = [
                "Go for a refreshing jog or cycling",
                "Play football or badminton at the park",
                "Enjoy an outdoor picnic",
            ]

        return verdict, activities

    def create_advice_text(self, state):
        weather = self.weather_data.get_city_data(state)
        if weather is None:
            return None

        verdict, activities = self.get_advice(weather)
        text = (
            f"🏙️ {weather['name']} Weather Report\n"
            f"• Temperature: {weather['temperature']}°C\n"
            f"• Humidity: {weather['humidity']}%\n"
            f"• UV Index: {weather['uv_index']} | Rain Risk: {weather['rain_chance']}%\n\n"
            f"{verdict}\n"
        )
        for act in activities:
            text += f"  - {act}\n"
        return text


class HydrationCalculator:

    def __init__(self, weather_data):
        self.weather_data = weather_data

    def calculate_feels_like(self, temperature, humidity):
        temp_f = temperature * 9 / 5 + 32
        if temp_f < 80 or humidity < 40:
            return temperature

        heat_index_f = (
            -42.379 + 2.04901523 * temp_f + 10.14333127 * humidity
            - 0.22475541 * temp_f * humidity - 0.00683783 * temp_f ** 2
            - 0.05481717 * humidity ** 2 + 0.00122874 * temp_f ** 2 * humidity
            + 0.00085282 * temp_f * humidity ** 2 - 0.00000199 * temp_f ** 2 * humidity ** 2
        )
        return round((heat_index_f - 32) * 5 / 9, 1)

    def calculate_hydration(self, temperature, humidity, uv_index):
        feels_like = self.calculate_feels_like(temperature, humidity)
        water_ml = 250

        if feels_like >= 41:
            level, water_ml, advice = "Danger", water_ml + 500, "Avoid outdoors. Drink water constantly and stay shaded."
        elif feels_like >= 32:
            level, water_ml, advice = "High", water_ml + 350, "Hydrate every 15–20 minutes with regular shade breaks."
        elif feels_like >= 27:
            level, water_ml, advice = "Moderate", water_ml + 150, "Drink fluids regularly before feeling thirsty."
        else:
            level, water_ml, advice = "Low", water_ml, "Comfortable environment. Maintain normal fluid intake."

        if uv_index >= 8:
            water_ml += 100

        return {"feels_like": feels_like, "level": level, "water_ml": water_ml, "advice": advice}

    def create_summary(self, state):
        current = self.weather_data.get_city_data(state)
        if current is None:
            return "No weather data available.", "Low"

        res = self.calculate_hydration(current["temperature"], current["humidity"], current["uv_index"])
        summary = (
            f"💧 {current['name']} Hydration Profile\n"
            f"• Temp: {current['temperature']}°C (Feels like {res['feels_like']}°C)\n"
            f"• Humidity: {current['humidity']}% | UV: {current['uv_index']}\n"
            f"• Risk Level: {res['level']} | Target: ~{res['water_ml']} ml/h\n\n"
            f"💡 {res['advice']}"
        )
        return summary, res["level"]

    def get_hourly_results(self, state):
        results = []
        for entry in self.weather_data.get_hours(state):
            res = self.calculate_hydration(entry["temp_c"], entry["humidity_pct"], entry["uv_index"])
            results.append({
                "hour": entry["hour"],
                "temperature": entry["temp_c"],
                "feels_like": res["feels_like"],
                "level": res["level"],
                "water_ml": res["water_ml"],
            })
        return results


class CityCompare:

    def __init__(self, weather_data):
        self.weather_data = weather_data

    def calculate_comfort_score(self, data):
        score = 100
        temp = data["temperature"]
        if temp < 12:
            score -= (12 - temp) * 3
        elif temp > 26:
            score -= (temp - 26) * 3.5
        score -= data["rain_chance"] * 0.4
        return max(0, min(100, int(score)))

    def compare_cities(self, city_a, city_b):
        temp_diff = round(city_a["temperature"] - city_b["temperature"], 1)
        score_a = self.calculate_comfort_score(city_a)
        score_b = self.calculate_comfort_score(city_b)
        verdicts = []

        if abs(temp_diff) < 1.0:
            verdicts.append(f"Both cities share comparable warmth (~{city_a['temperature']}°C).")
        elif temp_diff > 0:
            verdicts.append(f"{city_a['name']} is warmer by {temp_diff}°C.")
        else:
            verdicts.append(f"{city_b['name']} is warmer by {abs(temp_diff)}°C.")

        if city_a["rain_chance"] != city_b["rain_chance"]:
            drier = city_a["name"] if city_a["rain_chance"] < city_b["rain_chance"] else city_b["name"]
            verdicts.append(f"{drier} experiences a lower rain probability.")

        rec = f"{city_a['name']} wins outdoor recommendation ({score_a}/100)." if score_a >= score_b else f"{city_b['name']} wins outdoor recommendation ({score_b}/100)."
        return score_a, score_b, verdicts, rec

    def create_comparison_text(self, state_a, state_b):
        city_a = self.weather_data.get_city_data(state_a)
        city_b = self.weather_data.get_city_data(state_b)
        score_a, score_b, verdicts, rec = self.compare_cities(city_a, city_b)

        return (
            f"⚖️ Regional City Comparison\n\n"
            f"🏙️ {city_a['name']}: {city_a['temperature']}°C | Humid {city_a['humidity']}% | Score {score_a}/100\n"
            f"🏙️ {city_b['name']}: {city_b['temperature']}°C | Humid {city_b['humidity']}% | Score {score_b}/100\n\n"
            + "\n".join([f"• {v}" for v in verdicts])
            + f"\n\n🏆 {rec}"
        )


def get_score_color(score):
    if score >= 70:
        return "#2ecc71"
    if score >= 40:
        return "#f1c40f"
    return "#e74c3c"


def get_level_color(level):
    if level == "Low":
        return "#2ecc71"
    if level == "Moderate":
        return "#f1c40f"
    if level == "High":
        return "#e67e22"
    return "#e74c3c"
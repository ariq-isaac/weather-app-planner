# BUSINESS LOGIC LAYER
# This file holds all the calculations and decisions.

class TodaysPlanner:

    def __init__(self, weather_data):
        self.weather_data = weather_data

    # Calculates how suitable an hour is for outdoor activities.
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

    # Gives every hour of a state a score.
    # Returns a list of dictionaries: {"entry": ..., "score": ...}
    def score_hours(self, state):
        results = []

        for entry in self.weather_data.get_hours(state):
            score = self.calculate_score(entry)
            results.append({"entry": entry, "score": score})

        return results

    # Builds a plan from the best forecast hour.
    def create_plan(self, state):
        city = self.weather_data.get_city_name(state)
        scored_hours = self.score_hours(state)

        # Find the hour with the highest score (the first one wins a tie)
        best = scored_hours[0]
        for item in scored_hours:
            if item["score"] > best["score"]:
                best = item

        best_hour = best["entry"]["hour"]
        best_score = best["score"]

        plan = (
            f"{city} today's plan\n"
            f"Best time for outdoor activities: {best_hour:02d}:00 "
            f"(Score: {best_score}/100)"
        )

        return plan


# ==========================================
# ACTIVITY ADVISOR LOGIC
# ==========================================
class ActivityAdvisor:

    def __init__(self, weather_data):
        self.weather_data = weather_data

    # Decides which activities suit the weather
    def get_advice(self, weather):
        if weather["rain_chance"] >= 60:
            verdict = "It will likely rain. Stay indoors."
            activities = [
                "Visit a mall or a museum",
                "Workout at the gym",
                "Play board games or watch a movie",
            ]
        elif weather["uv_index"] >= 8:
            verdict = "The sun is very strong. Avoid long time outside."
            activities = [
                "Go swimming",
                "Play indoor sports like badminton",
                "Go outside again in the evening",
            ]
        elif weather["temperature"] >= 33:
            verdict = "It is quite hot. Keep your activities light."
            activities = [
                "Take a short walk in a shaded area",
                "Have a picnic under the trees",
                "Go swimming",
            ]
        else:
            verdict = "The weather is great for outdoor activities."
            activities = [
                "Go jogging or cycling",
                "Play football or badminton at the park",
                "Have a picnic",
            ]

        return verdict, activities

    # Builds the full advice text for one state.
    # Returns None if no weather was found for this hour.
    def create_advice_text(self, state):
        weather = self.weather_data.get_city_data(state)

        if weather is None:
            return None

        verdict, activities = self.get_advice(weather)

        text = f"{weather['name']} right now\n"
        text += f"Temperature: {weather['temperature']}°C\n"
        text += f"Humidity: {weather['humidity']}%\n"
        text += f"UV index: {weather['uv_index']}\n"
        text += f"Rain chance: {weather['rain_chance']}%\n\n"
        text += verdict + "\n\nSuggested activities:\n"
        for activity in activities:
            text += "• " + activity + "\n"

        return text


# ==========================================
# HYDRATION & SAFETY LOGIC
# ==========================================
class HydrationCalculator:

    def __init__(self, weather_data):
        self.weather_data = weather_data

    # Calculates the "feels like" temperature (heat index) in Celsius.
    def calculate_feels_like(self, temperature, humidity):
        temp_f = temperature * 9 / 5 + 32

        if temp_f < 80 or humidity < 40:
            return temperature

        heat_index_f = (
            -42.379
            + 2.04901523 * temp_f
            + 10.14333127 * humidity
            - 0.22475541 * temp_f * humidity
            - 0.00683783 * temp_f ** 2
            - 0.05481717 * humidity ** 2
            + 0.00122874 * temp_f ** 2 * humidity
            + 0.00085282 * temp_f * humidity ** 2
            - 0.00000199 * temp_f ** 2 * humidity ** 2
        )

        return round((heat_index_f - 32) * 5 / 9, 1)

    # Works out the hydration risk level and advice from the weather.
    def calculate_hydration(self, temperature, humidity, uv_index):
        feels_like = self.calculate_feels_like(temperature, humidity)
        water_ml = 250

        if feels_like >= 41:
            level = "Danger"
            water_ml += 500
            advice = "Avoid outdoor activity. Drink water often and rest in the shade or indoors."
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

    # Builds the summary text for the current hour.
    # Returns the text and the risk level.
    def create_summary(self, state):
        current = self.weather_data.get_city_data(state)
        if current is None:
            return "No weather data found for the current hour.", "Low"

        result = self.calculate_hydration(
            current["temperature"],
            current["humidity"],
            current["uv_index"]
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

    # Works out the hydration result for every hour of a state.
    # Returns a list of dictionaries, one for each hour.
    def get_hourly_results(self, state):
        results = []

        for entry in self.weather_data.get_hours(state):
            result = self.calculate_hydration(
                entry["temp_c"],
                entry["humidity_pct"],
                entry["uv_index"]
            )

            results.append({
                "hour": entry["hour"],
                "temperature": entry["temp_c"],
                "feels_like": result["feels_like"],
                "level": result["level"],
                "water_ml": result["water_ml"],
            })

        return results


# ==========================================
# CITY COMPARE LOGIC
# ==========================================
class CityCompare:

    def __init__(self, weather_data):
        self.weather_data = weather_data

    # Comfort score (the json has no wind data)
    def calculate_comfort_score(self, data):
        score = 100
        temp = data["temperature"]

        if temp < 12:
            score -= (12 - temp) * 3
        elif temp > 26:
            score -= (temp - 26) * 3.5

        score -= data["rain_chance"] * 0.4

        return max(0, min(100, int(score)))

    # Compares the two places
    def compare_cities(self, city_a, city_b):
        temp_diff = round(city_a["temperature"] - city_b["temperature"], 1)
        score_a = self.calculate_comfort_score(city_a)
        score_b = self.calculate_comfort_score(city_b)

        verdicts = []

        if abs(temp_diff) < 1.0:
            verdicts.append(f"Both cities share similar temperatures (~{city_a['temperature']}°C).")
        elif temp_diff > 0:
            verdicts.append(f"{city_a['name']} is {temp_diff}°C warmer than {city_b['name']}.")
        else:
            verdicts.append(f"{city_b['name']} is {abs(temp_diff)}°C warmer than {city_a['name']}.")

        if city_a["rain_chance"] != city_b["rain_chance"]:
            if city_a["rain_chance"] < city_b["rain_chance"]:
                drier = city_a["name"]
            else:
                drier = city_b["name"]
            verdicts.append(f"{drier} has a lower chance of precipitation.")

        if score_a >= score_b:
            recommendation = f"{city_a['name']} is recommended for outdoor activities today (Score: {score_a}/100)."
        else:
            recommendation = f"{city_b['name']} is recommended for outdoor activities today (Score: {score_b}/100)."

        return score_a, score_b, verdicts, recommendation

    # Builds the full comparison text for two states
    def create_comparison_text(self, state_a, state_b):
        city_a = self.weather_data.get_city_data(state_a)
        city_b = self.weather_data.get_city_data(state_b)

        score_a, score_b, verdicts, recommendation = self.compare_cities(city_a, city_b)

        text = (
            f"{city_a['name']}: {city_a['temperature']}°C, Humidity {city_a['humidity']}%\n"
            f"UV {city_a['uv_index']}, Rain {city_a['rain_chance']}%, Score {score_a}/100\n\n"
            f"{city_b['name']}: {city_b['temperature']}°C, Humidity {city_b['humidity']}%\n"
            f"UV {city_b['uv_index']}, Rain {city_b['rain_chance']}%, Score {score_b}/100\n\n"
            + "\n".join(verdicts)
            + "\n\n" + recommendation
        )

        return text

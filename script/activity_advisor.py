import json
import threading
import urllib.parse
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

APP_TITLE = "Weather Planner & Activity Advisor"
DATABASE_FILE = "weather_database.json"

def load_weather_database():
    """Load saved weather records from a local JSON file."""
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as file:
            records = json.load(file)
            return records if isinstance(records, list) else []
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError):
        return []

def save_weather_record(record):
    """Append a weather record to the JSON database."""
    records = load_weather_database()
    records.append(record)
    with open(DATABASE_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
 }

def weather_name(code):
    return WEATHER_CODES.get(code, "Unknown weather")

def recommend_activity(temp, code, rain_probability):
    # Thunderstorm / severe weather
    if code in (95, 96, 99):
        return (
            "Stay indoors",
            "Avoid outdoor sports, cycling, and open areas. Wait until the storm has passed."
        )

    # Rain, drizzle, snow, or high chance of rain
    if code >= 51 or rain_probability >= 60:
        return (
            "Indoor activities",
            "Try gaming, reading, a movie, indoor exercise, or a hobby. Bring an umbrella if you must go out."
        )

    if temp >= 35:
        return (
            "Cool indoor activities",
            "It is very hot. Choose indoor exercise or relaxing activities, drink water, and avoid strenuous activity in peak heat."
        )
    elif temp >= 30:
        return (
            "Light outdoor activities",
            "Try a short walk or casual activity in shade. Hydrate and avoid the hottest part of the day."
        )
    elif temp >= 20:
        return (
            "Outdoor activities",
            "Good conditions for walking, cycling, badminton, or a picnic. Check the sky before leaving."
        )
    else:
        return (
            "Comfortable outdoor or indoor activities",
            "Try a walk, sightseeing, or a cozy indoor activity. Bring a light jacket if needed."
        )

def clothing_advice(temp, code):
    if code >= 51:
        return "Raincoat or umbrella; shoes with good grip."
    if temp >= 30:
        return "Light, breathable clothing; consider a hat and sunscreen."
    if temp < 20:
        return "Bring a light jacket or warm layer."
    return "Comfortable everyday clothing."

class WeatherPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("720x620")
        self.root.minsize(620, 540)
        self.root.configure(bg="#eef4f8")

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#eef4f8")
        style.configure("TLabel", background="#eef4f8", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"), foreground="#12304a")
        style.configure("Sub.TLabel", font=("Segoe UI", 10), foreground="#496579")
        style.configure("Card.TFrame", background="white")
        style.configure("CardTitle.TLabel", background="white", font=("Segoe UI", 11, "bold"))
        style.configure("CardText.TLabel", background="white", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)

        self.city_var = tk.StringVar(value="Kuching")
        self.status_var = tk.StringVar(value="Enter a city and click Get Weather.")
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="🌦 Weather Planner", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            main,
            text="Live weather and activity suggestions for your day",
            style="Sub.TLabel"
        ).pack(anchor="w", pady=(2, 16))

        search = ttk.Frame(main)
        search.pack(fill="x", pady=(0, 14))
        ttk.Label(search, text="City:").pack(side="left")
        city_entry = ttk.Entry(search, textvariable=self.city_var, font=("Segoe UI", 11), width=30)
        city_entry.pack(side="left", padx=8, ipady=5)
        city_entry.bind("<Return>", lambda event: self.get_weather())
        self.fetch_button = ttk.Button(search, text="Get Weather", command=self.get_weather)
        self.fetch_button.pack(side="left")

        self.status_label = ttk.Label(main, textvariable=self.status_var, style="Sub.TLabel")
        self.status_label.pack(anchor="w", pady=(0, 10))

        self.weather_card = self.make_card(main, "Current Weather")
        self.weather_card.pack(fill="x", pady=(0, 10))
        self.weather_info = ttk.Label(
            self.weather_card,
            text="Your weather details will appear here.",
            style="CardText.TLabel",
            justify="left"
        )
        self.weather_info.pack(anchor="w", padx=14, pady=(0, 14))

        self.activity_card = self.make_card(main, "Activity Advisor")
        self.activity_card.pack(fill="x", pady=(0, 10))
        self.activity_info = ttk.Label(
            self.activity_card,
            text="Activity recommendations will appear here.",
            style="CardText.TLabel",
            justify="left",
            wraplength=640
        )
        self.activity_info.pack(anchor="w", padx=14, pady=(0, 14))

        self.clothing_card = self.make_card(main, "What to Wear")
        self.clothing_card.pack(fill="x")
        self.clothing_info = ttk.Label(
            self.clothing_card,
            text="Clothing advice will appear here.",
            style="CardText.TLabel",
            justify="left",
            wraplength=640
        )
        self.clothing_info.pack(anchor="w", padx=14, pady=(0, 14))

        self.history_card = self.make_card(main, "Saved Weather History")
        self.history_card.pack(fill="x", pady=(10, 0))
        self.history_info = ttk.Label(
            self.history_card,
            text=self.history_text(),
            style="CardText.TLabel",
            justify="left",
            wraplength=640
        )
        self.history_info.pack(anchor="w", padx=14, pady=(0, 14))

        ttk.Label(
            main,
            text="Weather data: Open-Meteo • Requires an internet connection",
            style="Sub.TLabel"
        ).pack(anchor="center", pady=(14, 0))

    def make_card(self, parent, title):
        card = ttk.Frame(parent, style="Card.TFrame", padding=(14, 12))
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        return card

    def history_text(self):
        records = load_weather_database()
        if not records:
            return "No saved weather records yet. Fetch weather to save your first record."
        recent = records[-5:][::-1]
        lines = []
        for record in recent:
            lines.append(
                f"{record.get('saved_at', 'Unknown time')} | "
                f"{record.get('city', 'Unknown city')} | "
                f"{record.get('temperature', '—')}°C | "
                f"{record.get('condition', 'Unknown')}"
            )
        return "\\n".join(lines)

    def refresh_history(self):
        self.history_info.config(text=self.history_text())

    def get_weather(self):
        city = self.city_var.get().strip()
        if not city:
            messagebox.showwarning("City required", "Please enter a city name.")
            return

        self.fetch_button.config(state="disabled")
        self.status_var.set("Finding city and checking live weather...")
        threading.Thread(target=self.fetch_weather_thread, args=(city,), daemon=True).start()

    def fetch_weather_thread(self, city):
        try:
            # Geocode city name using Open-Meteo
            query = urllib.parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"})
            geo_url = "https://geocoding-api.open-meteo.com/v1/search?" + query
            geo_data = self.request_json(geo_url)

            results = geo_data.get("results") or []
            if not results:
                raise ValueError(f"Could not find '{city}'. Try a different city name.")

            place = results[0]
            lat = place["latitude"]
            lon = place["longitude"]
            place_name = place.get("name", city)
            country = place.get("country", "")
            admin = place.get("admin1", "")
            location_parts = [place_name]
            if admin and admin != place_name:
                location_parts.append(admin)
            if country:
                location_parts.append(country)
            location_text = ", ".join(location_parts)

            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
                "hourly": "precipitation_probability",
                "forecast_days": 1,
                "timezone": "auto"
            }
            weather_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
            weather_data = self.request_json(weather_url)

            current = weather_data.get("current", {})
            code = int(current.get("weather_code", 0))
            temp = float(current.get("temperature_2m", 0))
            feels = current.get("apparent_temperature", temp)
            humidity = current.get("relative_humidity_2m", "—")
            precipitation = current.get("precipitation", 0)
            wind = current.get("wind_speed_10m", "—")

            hourly = weather_data.get("hourly", {})
            probs = hourly.get("precipitation_probability", [])
            rain_prob = max(probs[:3]) if probs else 0

            result = {
                "location": location_text,
                "temp": temp,
                "feels": feels,
                "humidity": humidity,
                "precipitation": precipitation,
                "wind": wind,
                "code": code,
                "rain_prob": rain_prob,
                "time": current.get("time", "")
            }
            self.root.after(0, self.show_weather, result)
        except Exception as exc:
            self.root.after(0, self.show_error, str(exc))

    @staticmethod
    def request_json(url):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "WeatherPlannerActivityAdvisor/1.0"}
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    def show_weather(self, data):
        self.fetch_button.config(state="normal")
        self.status_var.set("Weather updated successfully.")

        try:
            time_text = datetime.fromisoformat(data["time"]).strftime("%I:%M %p")
        except Exception:
            time_text = data["time"]

        self.weather_info.config(
            text=(
                f"📍 {data['location']}\n"
                f"🌡 Temperature: {data['temp']:.1f}°C (feels like {float(data['feels']):.1f}°C)\n"
                f"☁ Conditions: {weather_name(data['code'])}\n"
                f"💧 Humidity: {data['humidity']}%\n"
                f"🌧 Precipitation: {data['precipitation']} mm\n"
                f"☔ Rain chance (next few hours): {data['rain_prob']}%\n"
                f"💨 Wind: {data['wind']} km/h\n"
                f"🕒 Updated: {time_text}"
            )
        )

        activity, advice = recommend_activity(data["temp"], data["code"], data["rain_prob"])
        self.activity_info.config(text=f"Recommended: {activity}\n{advice}")
        self.clothing_info.config(text=clothing_advice(data["temp"], data["code"]))

        record = {
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "city": data["location"],
            "temperature": round(data["temp"], 1),
            "condition": weather_name(data["code"]),
            "humidity": data["humidity"],
            "rain_probability": data["rain_prob"],
            "wind_kmh": data["wind"],
            "recommended_activity": activity
        }
        try:
            save_weather_record(record)
            self.refresh_history()
        except OSError as exc:
            messagebox.showwarning(
                "Database save failed",
                f"Weather was displayed, but could not be saved to {DATABASE_FILE}.\\n{exc}"
            )

    def show_error(self, message):
        self.fetch_button.config(state="normal")
        self.status_var.set("Could not retrieve weather.")
        messagebox.showerror(
            "Weather lookup failed",
            message + "\n\nCheck your internet connection and try again."
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherPlannerApp(root)
    root.mainloop()

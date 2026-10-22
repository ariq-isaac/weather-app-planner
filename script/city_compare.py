import os
import sys
import time
import random
import json
import logging
from logging.handlers import RotatingFileHandler
import threading
import urllib.request
import urllib.parse
import urllib.error

# Graceful Tkinter import
try:
    import tkinter as tk
    from tkinter import messagebox
    HAS_TKINTER = True
except (ImportError, ModuleNotFoundError):
    tk = None
    messagebox = None
    HAS_TKINTER = False



# 1. ERROR LOGGING SETUP
LOG_FILE = "weather_planner.log"

def setup_logger(name="city_compare"):
    """Configures structured file and console logging."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Rotating file handler (5 MB max, up to 3 backups)
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            sys.stderr.write(f"Warning: Could not setup log file: {e}\n")

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

logger = setup_logger("city_compare")


# 2. RATE LIMITING & CACHING
class RateLimitExceededException(Exception):
    """Raised when request rate exceeds allowed threshold and retries fail."""
    pass

class CityNotFoundError(Exception):
    """Raised when a city cannot be located."""
    pass

class RateLimiter:
    """Token-Bucket rate limiter with sliding window tracking."""
    def __init__(self, max_requests_per_minute=20, burst_limit=5):
        self.capacity = burst_limit
        self.tokens = burst_limit
        self.fill_rate = max_requests_per_minute / 60.0  # tokens per second
        self.last_update = time.time()
        self.lock = threading.Lock()
        self.request_timestamps = []
        logger.info("RateLimiter initialized (max_req/min=%d, burst=%d)", max_requests_per_minute, burst_limit)

    def _add_tokens(self):
        now = time.time()
        delta = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + delta * self.fill_rate)
        self.last_update = now

    def acquire(self, timeout=6.0):
        deadline = time.time() + timeout
        with self.lock:
            while True:
                self._add_tokens()
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    now = time.time()
                    self.request_timestamps.append(now)
                    self.request_timestamps = [t for t in self.request_timestamps if now - t <= 60]
                    logger.debug("Rate token acquired. Remaining: %.2f", self.tokens)
                    return True
                wait_time = (1.0 - self.tokens) / self.fill_rate
                if time.time() + wait_time > deadline:
                    logger.warning("Rate limit exceeded: Token timeout after %.2fs", timeout)
                    return False
                time.sleep(min(wait_time, 0.4))

GLOBAL_RATE_LIMITER = RateLimiter(max_requests_per_minute=25, burst_limit=5)

# In-Memory Cache for Weather Data
WEATHER_CACHE = {}
CACHE_TTL_SECONDS = 600

def get_cached_weather(city_key):
    norm_key = city_key.strip().lower()
    entry = WEATHER_CACHE.get(norm_key)
    if entry:
        cached_time, data = entry
        age = time.time() - cached_time
        if age < CACHE_TTL_SECONDS:
            logger.info("Cache HIT for '%s' (age: %.1fs)", city_key, age)
            return data
    logger.debug("Cache MISS for '%s'", city_key)
    return None

def set_cached_weather(city_key, data):
    norm_key = city_key.strip().lower()
    WEATHER_CACHE[norm_key] = (time.time(), data)
    logger.debug("Cached weather data for '%s' (TTL: %ds)", city_key, CACHE_TTL_SECONDS)


# 3. WEATHER FETCHING WITH RETRY & BACKOFF
def fetch_weather_with_retry(city_name, max_retries=3):
    """
    Fetches weather data using Open-Meteo API.
    Handles caching, token-bucket throttling, and HTTP 429 backoff.
    """
    logger.info("Initiating weather fetch for: '%s'", city_name)

    # 1. Cache check
    cached = get_cached_weather(city_name)
    if cached:
        return cached

    # 2. Rate limit token check
    if not GLOBAL_RATE_LIMITER.acquire(timeout=5.0):
        err = f"API rate limit exceeded. Please wait a moment before querying '{city_name}'."
        logger.error(err)
        raise RateLimitExceededException(err)

    # 3. Geocode city name to lat/lon
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city_name)}&count=1&language=en&format=json"

    retries = 0
    backoff = 1.0
    lat, lon, canonical_name, country = None, None, city_name, ""

    while retries <= max_retries:
        try:
            req = urllib.request.Request(geo_url, headers={"User-Agent": "WeatherPlannerApp/1.0"})
            with urllib.request.urlopen(req, timeout=6.0) as response:
                if response.getcode() == 200:
                    raw_data = json.loads(response.read().decode("utf-8"))
                    results = raw_data.get("results")
                    if not results:
                        logger.warning("City '%s' not found in geocoding service.", city_name)
                        raise CityNotFoundError(f"City '{city_name}' was not found. Please check spelling.")
                    geo_info = results[0]
                    lat = geo_info["latitude"]
                    lon = geo_info["longitude"]
                    canonical_name = geo_info.get("name", city_name)
                    country = geo_info.get("country", "")
                    logger.info("Geocoded '%s' -> %s, %s (%.4f, %.4f)", city_name, canonical_name, country, lat, lon)
                    break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retries += 1
                sleep_time = backoff + random.uniform(0.1, 0.5)
                logger.warning("HTTP 429 on geocode '%s'. Retrying in %.2fs (%d/%d)", city_name, sleep_time, retries, max_retries)
                time.sleep(sleep_time)
                backoff *= 2
                continue
            logger.error("HTTP error %d geocoding '%s': %s", e.code, city_name, e.reason)
            raise
        except urllib.error.URLError as e:
            retries += 1
            if retries <= max_retries:
                sleep_time = backoff + random.uniform(0.1, 0.5)
                logger.warning("Network URLError for '%s': %s. Retrying...", city_name, e.reason)
                time.sleep(sleep_time)
                backoff *= 2
            else:
                logger.error("Connection failed permanently for geocoding '%s': %s", city_name, e.reason)
                raise

    # 4. Fetch weather forecast
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,"
        f"apparent_temperature,precipitation,weather_code,wind_speed_10m&"
        f"daily=temperature_2m_max,temperature_2m_min,uv_index_max,precipitation_probability_max&timezone=auto"
    )

    retries = 0
    backoff = 1.0

    while retries <= max_retries:
        try:
            req = urllib.request.Request(weather_url, headers={"User-Agent": "WeatherPlannerApp/1.0"})
            with urllib.request.urlopen(req, timeout=6.0) as response:
                if response.getcode() == 200:
                    raw_data = json.loads(response.read().decode("utf-8"))
                    current = raw_data.get("current", {})
                    daily = raw_data.get("daily", {})

                    weather_code = current.get("weather_code", 0)
                    condition_desc = decode_weather_code(weather_code)

                    result = {
                        "name": canonical_name,
                        "country": country,
                        "temperature": round(current.get("temperature_2m", 0.0), 1),
                        "apparent_temperature": round(current.get("apparent_temperature", 0.0), 1),
                        "humidity": current.get("relative_humidity_2m", 0),
                        "wind_speed": round(current.get("wind_speed_10m", 0.0), 1),
                        "condition": condition_desc,
                        "temp_max": round(daily.get("temperature_2m_max", [current.get("temperature_2m", 0.0)])[0], 1),
                        "temp_min": round(daily.get("temperature_2m_min", [current.get("temperature_2m", 0.0)])[0], 1),
                        "uv_index": round(daily.get("uv_index_max", [4.0])[0], 1),
                        "rain_chance": daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0,
                    }

                    set_cached_weather(city_name, result)
                    set_cached_weather(canonical_name, result)
                    logger.info("Weather retrieved for %s: %.1f°C, %s", canonical_name, result["temperature"], condition_desc)
                    return result

        except urllib.error.HTTPError as e:
            if e.code == 429:
                retries += 1
                sleep_time = backoff + random.uniform(0.1, 0.5)
                logger.warning("HTTP 429 for '%s'. Backing off %.2fs (%d/%d)", city_name, sleep_time, retries, max_retries)
                time.sleep(sleep_time)
                backoff *= 2
                continue
            logger.error("HTTP error %d for '%s': %s", e.code, city_name, e.reason)
            raise
        except urllib.error.URLError as e:
            retries += 1
            if retries <= max_retries:
                sleep_time = backoff + random.uniform(0.1, 0.5)
                time.sleep(sleep_time)
                backoff *= 2
            else:
                logger.error("Connection failed for '%s': %s", city_name, e.reason)
                raise

    raise RateLimitExceededException(f"Failed to fetch weather for '{city_name}' after {max_retries} attempts.")

def decode_weather_code(code):
    codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 51: "Light drizzle", 61: "Slight rain", 63: "Moderate rain",
        65: "Heavy rain", 71: "Slight snow", 80: "Rain showers", 95: "Thunderstorm"
    }
    return codes.get(code, "Cloudy")

# ==========================================
# 4. COMPARISON LOGIC
# ==========================================
def compare_cities(city_a, city_b):
    temp_diff = round(city_a["temperature"] - city_b["temperature"], 1)
    humidity_diff = city_a["humidity"] - city_b["humidity"]
    score_a = calculate_comfort_score(city_a)
    score_b = calculate_comfort_score(city_b)

    verdicts = []
    if abs(temp_diff) < 1.0:
        verdicts.append(f"Both cities share similar temperatures (~{city_a['temperature']}°C).")
    elif temp_diff > 0:
        verdicts.append(f"{city_a['name']} is {temp_diff}°C warmer than {city_b['name']}.")
    else:
        verdicts.append(f"{city_b['name']} is {abs(temp_diff)}°C warmer than {city_a['name']}.")

    if city_a["rain_chance"] != city_b["rain_chance"]:
        drier = city_a["name"] if city_a["rain_chance"] < city_b["rain_chance"] else city_b["name"]
        verdicts.append(f"{drier} has a lower chance of precipitation.")

    recommendation = (
        f"{city_a['name']} is recommended for outdoor activities today (Score: {score_a}/100)."
        if score_a >= score_b else
        f"{city_b['name']} is recommended for outdoor activities today (Score: {score_b}/100)."
    )

    logger.info("Comparison complete: %s vs %s", city_a['name'], city_b['name'])
    return {
        "city_a": city_a,
        "city_b": city_b,
        "temp_diff": temp_diff,
        "humidity_diff": humidity_diff,
        "score_a": score_a,
        "score_b": score_b,
        "verdicts": verdicts,
        "recommendation": recommendation
    }

def calculate_comfort_score(data):
    score = 100
    temp = data["temperature"]
    if temp < 12: score -= (12 - temp) * 3
    elif temp > 26: score -= (temp - 26) * 3.5
    score -= data.get("rain_chance", 0) * 0.4
    if data.get("wind_speed", 0) > 25: score -= (data["wind_speed"] - 25) * 1.5
    return max(0, min(100, int(score)))

# ==========================================
# 5. TKINTER GUI WINDOW
# ==========================================
class CityCompareWindow:
    def __init__(self, master=None):
        if not HAS_TKINTER:
            print("Tkinter is not installed on this system.")
            return

        if master is None:
            self.window = tk.Tk()
            self.is_standalone = True
        else:
            self.window = tk.Toplevel(master)
            self.is_standalone = False

        self.window.title("City Compare - Weather Planner App")
        self.window.geometry("640x700")
        self.window.configure(bg="#f8fafc")
        self.build_ui()
        logger.info("CityCompareWindow opened.")

    def build_ui(self):
        # Header banner
        header = tk.Frame(self.window, bg="#1e3a8a", padx=16, pady=12)
        header.pack(fill="x")

        tk.Label(
            header, text="City Weather Comparison",
            font=("Arial", 16, "bold"), bg="#1e3a8a", fg="white"
        ).pack(anchor="w")

        tk.Label(
            header, text="Rate-limit protected • Structured Error Logging • Side-by-side analysis",
            font=("Arial", 9), bg="#1e3a8a", fg="#bfdbfe"
        ).pack(anchor="w")

        # Input Frame
        frame_input = tk.LabelFrame(
            self.window, text="Select Cities to Compare",
            font=("Arial", 10, "bold"), bg="white", padx=14, pady=10
        )
        frame_input.pack(fill="x", padx=16, pady=10)

        # Row 0: Inputs
        tk.Label(frame_input, text="City 1:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_a = tk.Entry(frame_input, font=("Arial", 11), width=16)
        self.entry_a.insert(0, "New York")
        self.entry_a.grid(row=0, column=1, padx=(4, 16), pady=4)

        tk.Label(frame_input, text="City 2:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=2, sticky="w", pady=4)
        self.entry_b = tk.Entry(frame_input, font=("Arial", 11), width=16)
        self.entry_b.insert(0, "London")
        self.entry_b.grid(row=0, column=3, padx=(4, 8), pady=4)

        # Action Buttons
        btn_bar = tk.Frame(frame_input, bg="white")
        btn_bar.grid(row=1, column=0, columnspan=4, sticky="w", pady=(10, 4))

        self.btn_compare = tk.Button(
            btn_bar, text="Compare Now", font=("Arial", 11, "bold"),
            bg="#add8e6", padx=12, pady=4, relief="raised", cursor="hand2",
            command=self.start_thread
        )
        self.btn_compare.pack(side="left")

        self.btn_logs = tk.Button(
            btn_bar, text="View Logs", font=("Arial", 10),
            bg="#e2e8f0", padx=10, pady=4, relief="groove",
            command=self.show_logs
        )
        self.btn_logs.pack(side="left", padx=10)

        self.lbl_status = tk.Label(btn_bar, text="", font=("Arial", 9, "italic"), bg="white", fg="#d97706")
        self.lbl_status.pack(side="left", padx=6)

        # Result Cards Frame
        self.results_frame = tk.Frame(self.window, bg="#f8fafc")
        self.results_frame.pack(fill="x", padx=16, pady=6)

        self.card_a = self.create_card(self.results_frame, "City 1")
        self.card_a.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.card_b = self.create_card(self.results_frame, "City 2")
        self.card_b.pack(side="right", fill="both", expand=True, padx=(6, 0))

        # Bottom Analysis Box
        self.analysis_frame = tk.LabelFrame(
            self.window, text="Comparative Breakdown & Recommendation",
            font=("Arial", 10, "bold"), bg="white", padx=12, pady=10
        )
        self.analysis_frame.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        self.analysis_lbl = tk.Label(
            self.analysis_frame,
            text="Click 'Compare Now' to fetch weather metrics with rate-limit safety.",
            font=("Arial", 10), bg="white", fg="#475569", justify="left", wraplength=580
        )
        self.analysis_lbl.pack(anchor="w")

    def create_card(self, parent, title):
        card = tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold"), bg="white", padx=12, pady=10)
        card.temp = tk.Label(card, text="--°C", font=("Arial", 24, "bold"), bg="white", fg="#1e3a8a")
        card.temp.pack(anchor="w")

        card.cond = tk.Label(card, text="Condition: --", font=("Arial", 10), bg="white", fg="#334155")
        card.cond.pack(anchor="w", pady=(2, 6))

        card.stats = tk.Label(
            card, text="Feels like: --\nHumidity: --\nWind: --\nRain chance: --",
            font=("Arial", 9), bg="white", fg="#64748b", justify="left"
        )
        card.stats.pack(anchor="w")

        card.score = tk.Label(card, text="Outdoor Score: --/100", font=("Arial", 9, "bold"), bg="#f1f5f9", padx=6, pady=2)
        card.score.pack(anchor="w", pady=(8, 0))
        return card

    def start_thread(self):
        city_a = self.entry_a.get().strip()
        city_b = self.entry_b.get().strip()
        if not city_a or not city_b:
            messagebox.showwarning("Missing Input", "Please provide names for both cities.")
            return

        self.btn_compare.config(state="disabled")
        self.lbl_status.config(text="Fetching with rate-limit protection...")

        threading.Thread(
            target=self._worker, args=(city_a, city_b), daemon=True
        ).start()

    def _worker(self, city_a, city_b):
        try:
            data_a = fetch_weather_with_retry(city_a)
            data_b = fetch_weather_with_retry(city_b)
            comp = compare_cities(data_a, data_b)
            self.window.after(0, self._render_results, comp)
        except Exception as e:
            logger.exception("Worker error: %s", e)
            self.window.after(0, self._render_error, str(e))

    def _render_results(self, comp):
        self.btn_compare.config(state="normal")
        self.lbl_status.config(text="Success", fg="#16a34a")

        ca, cb = comp["city_a"], comp["city_b"]
        self.card_a.config(text=f"{ca['name']}, {ca['country']}")
        self.card_a.temp.config(text=f"{ca['temperature']}°C")
        self.card_a.cond.config(text=f"Condition: {ca['condition']}")
        self.card_a.stats.config(text=f"Feels like: {ca['apparent_temperature']}°C\nHumidity: {ca['humidity']}%\nWind: {ca['wind_speed']} km/h\nRain chance: {ca['rain_chance']}%")
        self.card_a.score.config(text=f"Outdoor Score: {comp['score_a']}/100")

        self.card_b.config(text=f"{cb['name']}, {cb['country']}")
        self.card_b.temp.config(text=f"{cb['temperature']}°C")
        self.card_b.cond.config(text=f"Condition: {cb['condition']}")
        self.card_b.stats.config(text=f"Feels like: {cb['apparent_temperature']}°C\nHumidity: {cb['humidity']}%\nWind: {cb['wind_speed']} km/h\nRain chance: {cb['rain_chance']}%")
        self.card_b.score.config(text=f"Outdoor Score: {comp['score_b']}/100")

        verdict_text = "\n• ".join(comp["verdicts"])
        self.analysis_lbl.config(
            text=f"• {verdict_text}\n\n★ Recommendation: {comp['recommendation']}"
        )

    def _render_error(self, err_msg):
        self.btn_compare.config(state="normal")
        self.lbl_status.config(text="Error logged", fg="#dc2626")
        messagebox.showerror("Weather Comparison Error", err_msg)

    def show_logs(self):
        log_win = tk.Toplevel(self.window)
        log_win.title("Weather Planner Logs")
        log_win.geometry("580x360")
        text_area = tk.Text(log_win, bg="#0f172a", fg="#f8fafc", font=("Courier", 9))
        text_area.pack(fill="both", expand=True, padx=6, pady=6)
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                text_area.insert("1.0", "".join(f.readlines()[-60:]))
        else:
            text_area.insert("1.0", "Log file is currently empty.")
        text_area.config(state="disabled")

    def run(self):
        if self.is_standalone:
            self.window.mainloop()

def open_city_compare_window(parent=None):
    """Entry point when clicked from homepage.py"""
    logger.info("Opening City Compare window.")
    return CityCompareWindow(parent)

if __name__ == "__main__":
    app = CityCompareWindow()
    app.run()
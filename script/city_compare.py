# THIS IS THE CITY COMPARE PAGE OF THE PROGRAM

import tkinter as tk
import json
import os
from datetime import datetime

class CityComparePage(tk.Frame):

    # Page Initialization
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.load_data()
        self.display_widgets()

    # Loads the weather database (database/malaysia_weather.json)
    def load_data(self):
        folder = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(folder, "..", "database", "malaysia_weather.json")

        with open(path, "r", encoding="utf-8") as file:
            self.data = json.load(file)

        # The state names (Johor, Kedah, ...) are the keys of the json
        self.states = list(self.data.keys())

    # Display Widgets
    def display_widgets(self):

        # Creates frame for back button
        self.back_button_frame = tk.Frame(
            self,
            bg="white"
            )

        # Back button (goes back to the home page)
        self.back_button = tk.Button(
            self.back_button_frame,
            text="Back to home page",
            font=("Arial", 15, "bold"),
            width=15,
            height=2,
            bg="white",
            command=self.go_back
            )
        self.back_button.grid(row=0, column=0, padx=10, pady=10)

        # Packs back button frame
        self.back_button_frame.pack()

        # Title/Header
        self.header = tk.Label(
            self,
            text="City Compare",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="darkblue"
            )
        self.header.pack(pady=(10,10))

        # Creates The frame which the dropdowns and buttons will stay
        self.button_frame = tk.Frame(
            self,
            bg="white"
            )

        # First dropdown
        self.state_a = tk.StringVar(value=self.states[0])
        self.menu_a = tk.OptionMenu(self.button_frame, self.state_a, *self.states)
        self.menu_a.config(font=("Arial", 15, "bold"), width=20, bg="lightblue")
        self.menu_a.grid(row=0, column=0, padx=10, pady=10)

        # Second dropdown
        self.state_b = tk.StringVar(value=self.states[1])
        self.menu_b = tk.OptionMenu(self.button_frame, self.state_b, *self.states)
        self.menu_b.config(font=("Arial", 15, "bold"), width=20, bg="lightblue")
        self.menu_b.grid(row=1, column=0, padx=10, pady=10)

        # Compare button
        self.compare_button = tk.Button(
            self.button_frame,
            text="Compare",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.on_click
            )
        self.compare_button.grid(row=2, column=0, padx=10, pady=10)

        # Packs all buttons
        self.button_frame.pack()

        # Where the result will be shown
        self.result_label = tk.Label(
            self,
            text="Pick two places and press Compare",
            font=("Arial", 12),
            bg="white",
            justify="left"
            )
        self.result_label.pack(pady=10)

    # Gets the weather of one place for the current hour
    def get_city_data(self, state):
        place = self.data[state]

        # The json only has hours 6 to 20, so keep the hour inside that range
        hour = datetime.now().hour
        if hour < 6:
            hour = 6
        if hour > 20:
            hour = 20

        for entry in place["hours"]:
            if entry["hour"] == hour:
                return {
                    "name": place["city"],
                    "temperature": entry["temp_c"],
                    "humidity": entry["humidity_pct"],
                    "uv_index": entry["uv_index"],
                    "rain_chance": entry["rain_chance_pct"],
                }

    # Comfort score (same formula as before, the json has no wind data)
    def calculate_comfort_score(self, data):
        score = 100
        temp = data["temperature"]

        if temp < 12:
            score -= (12 - temp) * 3
        elif temp > 26:
            score -= (temp - 26) * 3.5

        score -= data["rain_chance"] * 0.4

        return max(0, min(100, int(score)))

    # Compares the two places (same logic as before)
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

    # Adds event listener to the buttons
    def on_click(self):
        city_a = self.get_city_data(self.state_a.get())
        city_b = self.get_city_data(self.state_b.get())

        score_a, score_b, verdicts, recommendation = self.compare_cities(city_a, city_b)

        text = (
            f"{city_a['name']}: {city_a['temperature']}°C, Humidity {city_a['humidity']}%\n"
            f"UV {city_a['uv_index']}, Rain {city_a['rain_chance']}%, Score {score_a}/100\n\n"
            f"{city_b['name']}: {city_b['temperature']}°C, Humidity {city_b['humidity']}%\n"
            f"UV {city_b['uv_index']}, Rain {city_b['rain_chance']}%, Score {score_b}/100\n\n"
            + "\n".join(verdicts)
            + "\n\n" + recommendation
        )
        self.result_label.config(text=text)

    # Goes back to the home page
    def go_back(self):
        self.app.show_page("home")
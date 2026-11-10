# Hydration Safety Page

import json
import os
from datetime import datetime

import tkinter as tk


class HydrationSafetyPage(tk.Frame):

    # Page Initialization
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.load_data()
        self.display_widgets()

    # Loads weather database
    def load_data(self):
        folder = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(folder, "..", "database", "malaysia_weather.json")

        with open(path, "r", encoding="utf-8") as file:
            self.data = json.load(file)

        # The state names (Johor, Kedah, ...) are the keys of the JSON
        self.states = list(self.data.keys())

    def display_widgets(self):
        # Back button
        self.back_button = tk.Button(
            self,
            text="Back to home page",
            font=("Arial", 15, "bold"),
            width=15,
            height=2,
            bg="white",
            command=self.go_back
        )
        self.back_button.pack(padx=10, pady=10)

        # Title/Header
        self.header = tk.Label(
            self,
            text="Hydration & Safety",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="darkblue"
        )
        self.header.pack(pady=(10, 10))

        # Frame for the dropdown and button
        self.button_frame = tk.Frame(self, bg="white")

        self.state_label = tk.Label(
            self.button_frame,
            text="Choose your state:",
            font=("Arial", 12),
            bg="white"
        )
        self.state_label.grid(row=0, column=0, padx=10, pady=(0, 5))

        self.selected_state = tk.StringVar(value=self.states[0])
        self.state_menu = tk.OptionMenu(
            self.button_frame,
            self.selected_state,
            *self.states
        )
        self.state_menu.config(
            font=("Arial", 15, "bold"),
            width=20,
            bg="lightblue"
        )
        self.state_menu.grid(row=1, column=0, padx=10, pady=10)

        self.check_button = tk.Button(
            self.button_frame,
            text="Check Hydration Safety",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.on_click
        )
        self.check_button.grid(row=2, column=0, padx=10, pady=10)

        self.button_frame.pack()

        # Overall result for the current hour
        self.result_label = tk.Label(
            self,
            text="Choose a state and press Check Hydration Safety",
            font=("Arial", 12),
            bg="white",
            justify="left",
            wraplength=420
        )
        self.result_label.pack(pady=10)

        # Hourly breakdown
        self.hourly_frame = tk.Frame(self, bg="white")
        self.hourly_frame.pack(fill="x", padx=20)

    # Gets the weather of one place for the current hour
    def get_city_data(self, state):
        place = self.data[state]

        # The JSON only has hours 6 to 20, so keep the hour inside that range.
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
        return None

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

    def get_level_color(self, level):
        if level == "Low":
            return "lightgreen"
        if level == "Moderate":
            return "khaki"
        if level == "High":
            return "orange"
        return "lightcoral"

    # Builds the summary text for the current hour.
    def create_summary(self, state):
        current = self.get_city_data(state)
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

    def display_hourly_risk(self, state):
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        legend = tk.Label(
            self.hourly_frame,
            text="Green: low   Yellow: moderate   Orange: high   Red: danger",
            font=("Arial", 10),
            bg="white"
        )
        legend.pack(pady=(0, 5))

        for entry in self.data[state]["hours"]:
            result = self.calculate_hydration(
                entry["temp_c"],
                entry["humidity_pct"],
                entry["uv_index"]
            )

            row = tk.Label(
                self.hourly_frame,
                text=(
                    f"{entry['hour']:02d}:00   "
                    f"{entry['temp_c']}°C (feels {result['feels_like']}°C)   "
                    f"{result['level']}   "
                    f"{result['water_ml']} ml/h"
                ),
                font=("Arial", 11, "bold"),
                bg=self.get_level_color(result["level"]),
                anchor="w",
                padx=8,
                pady=3
            )
            row.pack(fill="x", pady=1)

    def on_click(self):
        state = self.selected_state.get()
        summary, level = self.create_summary(state)
        self.result_label.config(
            text=summary,
            bg=self.get_level_color(level)
        )
        self.display_hourly_risk(state)

    # Goes back to home page
    def go_back(self):
        self.app.show_page("home")

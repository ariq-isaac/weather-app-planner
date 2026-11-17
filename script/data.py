# DATA LAYER
# This file only loads and looks up the weather data.

import json
import os
from datetime import datetime


class WeatherData:

    def __init__(self):
        self.data = {}
        self.states = []
        self.load_data()

    def load_data(self):
        folder = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(folder, "..", "database", "malaysia_weather.json")

        with open(path, "r", encoding="utf-8") as file:
            self.data = json.load(file)

        self.states = list(self.data.keys())

    def get_states(self):
        return self.states

    def get_city_name(self, state):
        return self.data[state]["city"]

    def get_hours(self, state):
        return self.data[state]["hours"]

    def get_city_data(self, state):
        place = self.data[state]
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
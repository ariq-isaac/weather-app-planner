# DATA LAYER
# This file only loads and look up the weather data.

import json
import os
from datetime import datetime


class WeatherData:

    # Loads the data as soon as the object is created
    def __init__(self):
        self.data = {}
        self.states = []
        self.load_data()

    # Loads the weather database (database/malaysia_weather.json)
    def load_data(self):
        folder = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(folder, "..", "database", "malaysia_weather.json")

        with open(path, "r", encoding="utf-8") as file:
            self.data = json.load(file)

        # The state names (Johor, Kedah, ...) are the keys of the JSON
        self.states = list(self.data.keys())

    # Returns the list of state names
    def get_states(self):
        return self.states

    # Returns the city name of one state
    def get_city_name(self, state):
        return self.data[state]["city"]

    # Returns all the hourly entries of one state
    def get_hours(self, state):
        return self.data[state]["hours"]

    # Gets the weather of one place for the current hour
    def get_city_data(self, state):
        place = self.data[state]

        # The JSON only has hours 6 to 20, so keep the hour inside that range
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

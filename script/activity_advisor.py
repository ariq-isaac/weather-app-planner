# Activity Advisor Page

import tkinter as tk
import json
import os
from datetime import datetime


class ActivityAdvisorPage(tk.Frame):

    # Idk wtf this is but it is needed to make the page work
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

        # The state names that are mentioned in the JSON file
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
            text="Activity Advisor",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="darkblue"
            )
        self.header.pack(pady=(10, 10))

        # Dropdown to choose the state
        self.state_label = tk.Label(
            self,
            text="Choose your state:",
            font=("Arial", 12),
            bg="white"
            )
        self.state_label.pack()

        self.selected_state = tk.StringVar(value=self.states[0])
        self.dropdown = tk.OptionMenu(self, self.selected_state, *self.states)
        self.dropdown.config(font=("Arial", 12), width=15)
        self.dropdown.pack(pady=10)

        # Button that gives the advice
        self.advice_button = tk.Button(
            self,
            text="Get Advice",
            font=("Arial", 15, "bold"),
            width=15,
            height=2,
            bg="lightblue",
            command=self.show_advice
            )
        self.advice_button.pack(pady=10)

        # Label where the result is shown
        self.result_label = tk.Label(
            self,
            text="",
            font=("Arial", 12),
            bg="white",
            justify="left",
            wraplength=420
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

    # Runs when the Get Advice button is clicked
    def show_advice(self):
        weather = self.get_city_data(self.selected_state.get())

        # Stops if no weather was found for this hour
        if weather is None:
            self.result_label.config(text="No weather data found.")
            return

        verdict, activities = self.get_advice(weather)

        text = f"{weather['name']} right now\n"
        text += f"Temperature: {weather['temperature']}°C\n"
        text += f"Humidity: {weather['humidity']}%\n"
        text += f"UV index: {weather['uv_index']}\n"
        text += f"Rain chance: {weather['rain_chance']}%\n\n"
        text += verdict + "\n\nSuggested activities:\n"
        for activity in activities:
            text += "• " + activity + "\n"

        self.result_label.config(text=text)

    # Goes back to home page
    def go_back(self):
        self.app.show_page("home")
# THIS IS THE FIRST / HOMEPAGE OF THE PROGRAM (the entry point)
#
# This file only:
#   1. creates the main window
#   2. loads the weather data once
#   3. creates every page from ui.py
#   4. switches between the pages
#
# File order of the project:
#   data.py      -> loads and looks up the weather data
#   homepage.py  -> this file: starts the app
#   logic.py     -> all calculations and decisions
#   ui.py        -> all the tkinter pages (including the home page)

import tkinter as tk

# Imports the weather data
from data import WeatherData

# Imports the tkinter pages and the shared theme from ui.py
from ui import (
    Theme,
    HomePage,
    TodaysPlanPage,
    ActivityAdvisorPage,
    HydrationSafetyPage,
    CityComparePage,
    register_surface,
)


# ==========================================
# THE APP
# ==========================================
class WeatherApp:

    # App Initialization
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Weather Planner")
        self.window.geometry("920x680")
        self.window.minsize(820, 620)
        self.window.configure(bg=Theme.BG)

        # The weather data is loaded once here and shared with every page
        # Every page reads it through self.app.weather_data
        self.weather_data = WeatherData()

        # The container is the "screen". All pages sit inside it on top of each other
        self.container = tk.Frame(self.window, bg=Theme.BG)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        register_surface(self.container)

        # A dictionary: page name to page
        self.pages = {}
        self.pages["home"] = HomePage(self.container, self)
        self.pages["todays_plan"] = TodaysPlanPage(self.container, self)
        self.pages["activity_advisor"] = ActivityAdvisorPage(self.container, self)
        self.pages["hydration_safety"] = HydrationSafetyPage(self.container, self)
        self.pages["city_compare"] = CityComparePage(self.container, self)

        # Put every page in the same spot of the container
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        # Start on the home page
        self.show_page("home")

    # Brings one page to the front
    def show_page(self, name):
        self.pages[name].tkraise()

    # Runs the program when called
    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = WeatherApp()
    app.run()
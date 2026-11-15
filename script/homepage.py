# THIS IS THE FIRST / HOMEPAGE OF THE PROGRAM
# Run this file to start the program:  python homepage.py

import tkinter as tk

# Imports every tkinter page as well as the weather data
from data import WeatherData
from ui import HomePage
from ui import TodaysPlanPage
from ui import ActivityAdvisorPage
from ui import HydrationSafetyPage
from ui import CityComparePage

class WeatherApp:

    # App Initialization
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Weather Planner App")
        self.window.geometry("500x700")
        self.window.configure(bg="white")

        # The weather data is loaded once here and shared with every page
        self.weather_data = WeatherData()

        # The container is the "screen". All pages sit inside it on top of each other
        self.container = tk.Frame(self.window, bg="white")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # A dictionary: page name -> page
        self.pages = {}
        self.pages["home"] = HomePage(self.container, self)
        self.pages["todays_plan"] = TodaysPlanPage(self.container, self)
        self.pages["city_compare"] = CityComparePage(self.container, self)
        self.pages["activity_advisor"] = ActivityAdvisorPage(self.container, self)
        self.pages["hydration_safety"] = HydrationSafetyPage(self.container, self)

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

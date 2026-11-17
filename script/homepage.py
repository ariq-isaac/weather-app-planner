# THIS IS THE FIRST / HOMEPAGE OF THE PROGRAM
# Run this file to start the program:  python homepage.py

import customtkinter as ctk

from data import WeatherData
from ui import HomePage, TodaysPlanPage, ActivityAdvisorPage, HydrationSafetyPage, CityComparePage

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class WeatherApp:

    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Weather Planner Pro")
        self.window.geometry("520x720")
        self.window.minsize(480, 640)

        self.weather_data = WeatherData()

        self.container = ctk.CTkFrame(self.window, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=15, pady=15)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "home": HomePage(self.container, self),
            "todays_plan": TodaysPlanPage(self.container, self),
            "city_compare": CityComparePage(self.container, self),
            "activity_advisor": ActivityAdvisorPage(self.container, self),
            "hydration_safety": HydrationSafetyPage(self.container, self),
        }

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page("home")

    def show_page(self, name):
        self.pages[name].tkraise()

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = WeatherApp()
    app.run()
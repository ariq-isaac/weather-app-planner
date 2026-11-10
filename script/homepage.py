"""Application entry point and page navigation."""

import tkinter as tk

from ui import (
    ActivityAdvisorPage,
    CityComparePage,
    HomePage,
    HydrationSafetyPage,
    TodaysPlanPage,
)
from weather_data import WeatherDataRepository
from weather_logic import WeatherPlannerLogic


class WeatherApp:
    def __init__(self) -> None:
        self.window = tk.Tk()
        self.window.title("Weather Planner App")
        self.window.geometry("500x700")
        self.window.configure(bg="white")

        self.weather_data = WeatherDataRepository()
        self.logic = WeatherPlannerLogic(self.weather_data)

        self.container = tk.Frame(self.window, bg="white")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        page_types = {
            "home": HomePage,
            "todays_plan": TodaysPlanPage,
            "city_compare": CityComparePage,
            "activity_advisor": ActivityAdvisorPage,
            "hydration_safety": HydrationSafetyPage,
        }
        self.pages = {
            name: page_type(self.container, self)
            for name, page_type in page_types.items()
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page("home")

    def show_page(self, name: str) -> None:
        self.pages[name].tkraise()

    def run(self) -> None:
        self.window.mainloop()


if __name__ == "__main__":
    WeatherApp().run()

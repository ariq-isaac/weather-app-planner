# THIS IS THE FIRST / HOMEPAGE OF THE PROGRAM
# Run this file to start the program:  python homepage.py

import tkinter as tk

# Imports other pages
from city_compare import CityComparePage
from todays_plan import TodaysPlanPage

# ==========================================
# THE HOME PAGE 
# ==========================================
class HomePage(tk.Frame):

    # Page Initialization
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.display_widgets()

    # Display Widgets
    def display_widgets(self):

        # Title/Header
        self.header = tk.Label(
            self,
            text="Welcome to Weather Planner App",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="darkblue"
            )
        self.header.pack(pady=(10,10))

        # Creates The frame which the buttons will stay
        self.button_frame = tk.Frame(
            self,
            bg="white"
            )

        # All the buttons
        self.todays_plan = tk.Button(
            self.button_frame,
            text="Today's Plan",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.open_todays_plan
            )
        self.todays_plan.grid(row=0, column=0, padx=10, pady=10)

        self.activity_advisor = tk.Button(
            self.button_frame,
            text="Activity Advisor",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue"
            )
        self.activity_advisor.grid(row=1, column=0, padx=10, pady=10)

        self.hydration_safety = tk.Button(
            self.button_frame,
            text="Hydration & Safety",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue"
            )
        self.hydration_safety.grid(row=2, column=0, padx=10, pady=10)

        self.city_compare = tk.Button(
            self.button_frame,
            text="City Compare",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.open_city_compare
            )
        self.city_compare.grid(row=3, column=0, padx=10, pady=10)

        self.exit = tk.Button(
            self.button_frame,
            text="Exit",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.app.window.destroy
            )
        self.exit.grid(row=4, column=0, padx=10, pady=10)

        # Packs all buttons
        self.button_frame.pack()

    # Functions that will be used as event listener for buttons
    def open_city_compare(self):
        self.app.show_page("city_compare")
    def open_todays_plan(self):
        self.app.show_page("todays_plan")


# ==========================================
# THE APP 
# ==========================================
class WeatherApp:

    # App Initialization
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Weather Planner App")
        self.window.geometry("500x700")
        self.window.configure(bg="white")

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

        # Put every page in the same spot of the container
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        # Start on the home page
        self.show_page("home")

    # Brings one page to the front (this is the "go to /city_compare" part)
    def show_page(self, name):
        self.pages[name].tkraise()

    # Runs the program when called
    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = WeatherApp()
    app.run()

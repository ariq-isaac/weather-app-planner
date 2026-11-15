# UI LAYER
# This file only builds the user interface
# All the calculations are done by the classes in logic.py.
# All the data is read through the WeatherData class in data.py.

import tkinter as tk

# imports the functions for the logic / calculation
from logic import TodaysPlanner
from logic import ActivityAdvisor
from logic import HydrationCalculator
from logic import CityComparer

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
        self.header.pack(pady=(10, 10))

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
            bg="lightblue",
            command=self.open_activity_advisor
            )
        self.activity_advisor.grid(row=1, column=0, padx=10, pady=10)

        self.hydration_safety = tk.Button(
            self.button_frame,
            text="Hydration & Safety",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.open_hydration_safety
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

    def open_activity_advisor(self):
        self.app.show_page("activity_advisor")

    def open_hydration_safety(self):
        self.app.show_page("hydration_safety")


# ==========================================
# TODAY'S PLAN PAGE
# ==========================================
class TodaysPlanPage(tk.Frame):

    # Page Initialization
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.planner = TodaysPlanner(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

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
            text="Today's Plan",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="darkblue"
            )
        self.header.pack(pady=(10, 10))

        # Creates the frame which the dropdown and button will use.
        self.button_frame = tk.Frame(
            self,
            bg="white"
            )

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

        self.plan_button = tk.Button(
            self.button_frame,
            text="Create Today's Plan",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.on_click
            )
        self.plan_button.grid(row=2, column=0, padx=10, pady=10)

        self.button_frame.pack()

        self.result_label = tk.Label(
            self,
            text="Choose a state and press Create Today's Plan",
            font=("Arial", 12),
            bg="white",
            justify="left",
            wraplength=420
            )
        self.result_label.pack(pady=10)

        self.hourly_frame = tk.Frame(self, bg="white")
        self.hourly_frame.pack(fill="x", padx=20)

    # Chooses the row color from the score
    def get_score_color(self, score):
        if score >= 70:
            return "lightgreen"
        if score >= 40:
            return "khaki"
        return "lightcoral"

    # Shows one colored row for every hour
    def display_hourly_scores(self, state):
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        legend = tk.Label(
            self.hourly_frame,
            text="Green: good   Yellow: moderate   Red: poor",
            font=("Arial", 10),
            bg="white"
            )
        legend.pack(pady=(0, 5))

        for item in self.planner.score_hours(state):
            entry = item["entry"]
            score = item["score"]

            row = tk.Label(
                self.hourly_frame,
                text=(
                    f"{entry['hour']:02d}:00   "
                    f"{entry['temp_c']}°C   "
                    f"Rain {entry['rain_chance_pct']}%   "
                    f"Score {score}/100"
                ),
                font=("Arial", 11, "bold"),
                bg=self.get_score_color(score),
                anchor="w",
                padx=8,
                pady=3
                )
            row.pack(fill="x", pady=1)

    def on_click(self):
        state = self.selected_state.get()
        self.result_label.config(text=self.planner.create_plan(state))
        self.display_hourly_scores(state)

    # Goes back to home page
    def go_back(self):
        self.app.show_page("home")


# ==========================================
# ACTIVITY ADVISOR PAGE
# ==========================================
class ActivityAdvisorPage(tk.Frame):

    # Page Initialization
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.advisor = ActivityAdvisor(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

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

    # Runs when the Get Advice button is clicked
    def show_advice(self):
        text = self.advisor.create_advice_text(self.selected_state.get())

        # Stops if no weather was found for this hour
        if text is None:
            self.result_label.config(text="No weather data found.")
            return

        self.result_label.config(text=text)

    # Goes back to home page
    def go_back(self):
        self.app.show_page("home")


# ==========================================
# HYDRATION & SAFETY PAGE
# ==========================================
class HydrationSafetyPage(tk.Frame):

    # Page Initialization
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.calculator = HydrationCalculator(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

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

    # Chooses the row color from the risk level
    def get_level_color(self, level):
        if level == "Low":
            return "lightgreen"
        if level == "Moderate":
            return "khaki"
        if level == "High":
            return "orange"
        return "lightcoral"

    # Shows one colored row for every hour
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

        for result in self.calculator.get_hourly_results(state):
            row = tk.Label(
                self.hourly_frame,
                text=(
                    f"{result['hour']:02d}:00   "
                    f"{result['temperature']}°C (feels {result['feels_like']}°C)   "
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
        summary, level = self.calculator.create_summary(state)
        self.result_label.config(
            text=summary,
            bg=self.get_level_color(level)
        )
        self.display_hourly_risk(state)

    # Goes back to home page
    def go_back(self):
        self.app.show_page("home")


# ==========================================
# CITY COMPARE PAGE
# ==========================================
class CityComparePage(tk.Frame):

    # Page Initialization
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.comparer = CityComparer(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

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
        self.header.pack(pady=(10, 10))

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

    # Adds event listener to the buttons
    def on_click(self):
        text = self.comparer.create_comparison_text(
            self.state_a.get(),
            self.state_b.get()
        )
        self.result_label.config(text=text)

    # Goes back to the home page
    def go_back(self):
        self.app.show_page("home")

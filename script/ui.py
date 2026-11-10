"""Tkinter pages and widgets for the weather planner application."""

import tkinter as tk
from typing import Any


class WeatherPage(tk.Frame):
    """Shared page behavior for navigation and access to app services."""

    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, bg="white")
        self.app = app
        self.weather_data = app.weather_data
        self.logic = app.logic
        self.states = self.weather_data.states

    def add_back_button(self) -> None:
        tk.Button(
            self,
            text="Back to home page",
            font=("Arial", 15, "bold"),
            width=15,
            height=2,
            bg="white",
            command=self.go_back,
        ).pack(padx=10, pady=10)

    def go_back(self) -> None:
        self.app.show_page("home")


class HomePage(WeatherPage):
    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, app)
        self.display_widgets()

    def display_widgets(self) -> None:
        tk.Label(
            self,
            text="Welcome to Weather Planner App",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="darkblue",
        ).pack(pady=(10, 10))

        self.button_frame = tk.Frame(self, bg="white")
        buttons = (
            ("Today's Plan", "todays_plan"),
            ("Activity Advisor", "activity_advisor"),
            ("Hydration & Safety", "hydration_safety"),
            ("City Compare", "city_compare"),
        )
        for row, (label, page_name) in enumerate(buttons):
            tk.Button(
                self.button_frame,
                text=label,
                font=("Arial", 15, "bold"),
                width=20,
                height=3,
                bg="lightblue",
                command=lambda name=page_name: self.app.show_page(name),
            ).grid(row=row, column=0, padx=10, pady=10)

        tk.Button(
            self.button_frame,
            text="Exit",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.app.window.destroy,
        ).grid(row=len(buttons), column=0, padx=10, pady=10)
        self.button_frame.pack()


class TodaysPlanPage(WeatherPage):
    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, app)
        self.display_widgets()

    def display_widgets(self) -> None:
        self.add_back_button()
        tk.Label(
            self,
            text="Today's Plan",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="darkblue",
        ).pack(pady=(10, 10))

        self.button_frame = tk.Frame(self, bg="white")
        tk.Label(
            self.button_frame,
            text="Choose your state:",
            font=("Arial", 12),
            bg="white",
        ).grid(row=0, column=0, padx=10, pady=(0, 5))

        self.selected_state = tk.StringVar(value=self.states[0])
        self.state_menu = tk.OptionMenu(
            self.button_frame, self.selected_state, *self.states
        )
        self.state_menu.config(
            font=("Arial", 15, "bold"), width=20, bg="lightblue"
        )
        self.state_menu.grid(row=1, column=0, padx=10, pady=10)

        tk.Button(
            self.button_frame,
            text="Create Today's Plan",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.on_click,
        ).grid(row=2, column=0, padx=10, pady=10)
        self.button_frame.pack()

        self.result_label = tk.Label(
            self,
            text="Choose a state and press Create Today's Plan",
            font=("Arial", 12),
            bg="white",
            justify="left",
            wraplength=420,
        )
        self.result_label.pack(pady=10)
        self.hourly_frame = tk.Frame(self, bg="white")
        self.hourly_frame.pack(fill="x", padx=20)

    def display_hourly_scores(self, state: str) -> None:
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        tk.Label(
            self.hourly_frame,
            text="Green: good   Yellow: moderate   Red: poor",
            font=("Arial", 10),
            bg="white",
        ).pack(pady=(0, 5))

        for entry, score in self.logic.score_hours(state):
            color = "lightgreen" if score >= 70 else "khaki" if score >= 40 else "lightcoral"
            tk.Label(
                self.hourly_frame,
                text=(
                    f"{entry['hour']:02d}:00   {entry['temp_c']}°C   "
                    f"Rain {entry['rain_chance_pct']}%   Score {score}/100"
                ),
                font=("Arial", 11, "bold"),
                bg=color,
                anchor="w",
                padx=8,
                pady=3,
            ).pack(fill="x", pady=1)

    def on_click(self) -> None:
        state = self.selected_state.get()
        self.result_label.config(text=self.logic.create_plan(state))
        self.display_hourly_scores(state)


class ActivityAdvisorPage(WeatherPage):
    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, app)
        self.display_widgets()

    def display_widgets(self) -> None:
        self.add_back_button()
        tk.Label(
            self,
            text="Activity Advisor",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="darkblue",
        ).pack(pady=(10, 10))
        tk.Label(
            self, text="Choose your state:", font=("Arial", 12), bg="white"
        ).pack()

        self.selected_state = tk.StringVar(value=self.states[0])
        self.dropdown = tk.OptionMenu(self, self.selected_state, *self.states)
        self.dropdown.config(font=("Arial", 12), width=15)
        self.dropdown.pack(pady=10)

        tk.Button(
            self,
            text="Get Advice",
            font=("Arial", 15, "bold"),
            width=15,
            height=2,
            bg="lightblue",
            command=self.show_advice,
        ).pack(pady=10)
        self.result_label = tk.Label(
            self,
            text="",
            font=("Arial", 12),
            bg="white",
            justify="left",
            wraplength=420,
        )
        self.result_label.pack(pady=10)

    def show_advice(self) -> None:
        state = self.selected_state.get()
        weather = self.weather_data.get_city_data(state)
        if weather is None:
            self.result_label.config(text="No weather data found.")
            return

        verdict, activities = self.logic.get_activity_advice(weather)
        text = (
            f"{weather['name']} right now\n"
            f"Temperature: {weather['temperature']}°C\n"
            f"Humidity: {weather['humidity']}%\n"
            f"UV index: {weather['uv_index']}\n"
            f"Rain chance: {weather['rain_chance']}%\n\n"
            f"{verdict}\n\nSuggested activities:\n"
        )
        text += "".join(f"• {activity}\n" for activity in activities)
        self.result_label.config(text=text)


class CityComparePage(WeatherPage):
    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, app)
        self.display_widgets()

    def display_widgets(self) -> None:
        self.add_back_button()
        tk.Label(
            self,
            text="City Compare",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="darkblue",
        ).pack(pady=(10, 10))

        self.button_frame = tk.Frame(self, bg="white")
        self.state_a = tk.StringVar(value=self.states[0])
        self.menu_a = tk.OptionMenu(
            self.button_frame, self.state_a, *self.states
        )
        self.menu_a.config(font=("Arial", 15, "bold"), width=20, bg="lightblue")
        self.menu_a.grid(row=0, column=0, padx=10, pady=10)

        second_state = self.states[1] if len(self.states) > 1 else self.states[0]
        self.state_b = tk.StringVar(value=second_state)
        self.menu_b = tk.OptionMenu(
            self.button_frame, self.state_b, *self.states
        )
        self.menu_b.config(font=("Arial", 15, "bold"), width=20, bg="lightblue")
        self.menu_b.grid(row=1, column=0, padx=10, pady=10)

        tk.Button(
            self.button_frame,
            text="Compare",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.on_click,
        ).grid(row=2, column=0, padx=10, pady=10)
        self.button_frame.pack()

        self.result_label = tk.Label(
            self,
            text="Pick two places and press Compare",
            font=("Arial", 12),
            bg="white",
            justify="left",
        )
        self.result_label.pack(pady=10)

    def on_click(self) -> None:
        city_a = self.weather_data.get_city_data(self.state_a.get())
        city_b = self.weather_data.get_city_data(self.state_b.get())
        if city_a is None or city_b is None:
            self.result_label.config(text="No weather data found.")
            return

        score_a, score_b, verdicts, recommendation = self.logic.compare_cities(
            city_a, city_b
        )
        text = (
            f"{city_a['name']}: {city_a['temperature']}°C, "
            f"Humidity {city_a['humidity']}%\n"
            f"UV {city_a['uv_index']}, Rain {city_a['rain_chance']}%, "
            f"Score {score_a}/100\n\n"
            f"{city_b['name']}: {city_b['temperature']}°C, "
            f"Humidity {city_b['humidity']}%\n"
            f"UV {city_b['uv_index']}, Rain {city_b['rain_chance']}%, "
            f"Score {score_b}/100\n\n"
            + "\n".join(verdicts)
            + "\n\n"
            + recommendation
        )
        self.result_label.config(text=text)


class HydrationSafetyPage(WeatherPage):
    def __init__(self, parent: tk.Misc, app: Any) -> None:
        super().__init__(parent, app)
        self.display_widgets()

    def display_widgets(self) -> None:
        self.add_back_button()
        tk.Label(
            self,
            text="Hydration & Safety",
            font=("Arial", 20, "bold"),
            bg="white",
            fg="darkblue",
        ).pack(pady=(10, 10))

        self.button_frame = tk.Frame(self, bg="white")
        tk.Label(
            self.button_frame,
            text="Choose your state:",
            font=("Arial", 12),
            bg="white",
        ).grid(row=0, column=0, padx=10, pady=(0, 5))

        self.selected_state = tk.StringVar(value=self.states[0])
        self.state_menu = tk.OptionMenu(
            self.button_frame, self.selected_state, *self.states
        )
        self.state_menu.config(
            font=("Arial", 15, "bold"), width=20, bg="lightblue"
        )
        self.state_menu.grid(row=1, column=0, padx=10, pady=10)

        tk.Button(
            self.button_frame,
            text="Check Hydration Safety",
            font=("Arial", 15, "bold"),
            width=20,
            height=3,
            bg="lightblue",
            command=self.on_click,
        ).grid(row=2, column=0, padx=10, pady=10)
        self.button_frame.pack()

        self.result_label = tk.Label(
            self,
            text="Choose a state and press Check Hydration Safety",
            font=("Arial", 12),
            bg="white",
            justify="left",
            wraplength=420,
        )
        self.result_label.pack(pady=10)
        self.hourly_frame = tk.Frame(self, bg="white")
        self.hourly_frame.pack(fill="x", padx=20)

    @staticmethod
    def get_level_color(level: str) -> str:
        return {
            "Low": "lightgreen",
            "Moderate": "khaki",
            "High": "orange",
            "Danger": "lightcoral",
        }.get(level, "white")

    def display_hourly_risk(self, state: str) -> None:
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        tk.Label(
            self.hourly_frame,
            text="Green: low   Yellow: moderate   Orange: high   Red: danger",
            font=("Arial", 10),
            bg="white",
        ).pack(pady=(0, 5))

        for entry in self.weather_data.get_hourly_forecast(state):
            result = self.logic.calculate_hydration(
                entry["temp_c"], entry["humidity_pct"], entry["uv_index"]
            )
            tk.Label(
                self.hourly_frame,
                text=(
                    f"{entry['hour']:02d}:00   "
                    f"{entry['temp_c']}°C (feels {result['feels_like']}°C)   "
                    f"{result['level']}   {result['water_ml']} ml/h"
                ),
                font=("Arial", 11, "bold"),
                bg=self.get_level_color(result["level"]),
                anchor="w",
                padx=8,
                pady=3,
            ).pack(fill="x", pady=1)

    def on_click(self) -> None:
        summary = self.logic.create_hydration_summary(self.selected_state.get())
        if summary is None:
            self.result_label.config(text="No weather data found for the current hour.")
            return

        text, level = summary
        self.result_label.config(text=text, bg=self.get_level_color(level))
        self.display_hourly_risk(self.selected_state.get())

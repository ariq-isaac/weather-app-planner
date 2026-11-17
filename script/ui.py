# UI LAYER
# CustomTkinter UI designed for 10x better aesthetics and UX.

import customtkinter as ctk
from logic import TodaysPlanner, ActivityAdvisor, HydrationCalculator, CityCompare, get_score_color, get_level_color


class HomePage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.display_widgets()

    def display_widgets(self):
        # Header Card
        header_card = ctk.CTkFrame(self, corner_radius=16, border_width=1, border_color=("#e1e1e1", "#2d2d2d"))
        header_card.pack(fill="x", pady=(10, 20), padx=10)

        ctk.CTkLabel(
            header_card,
            text="🌤️ Weather Planner Pro",
            font=("Segoe UI", 24, "bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            header_card,
            text="Your intelligent daily outdoor & safety companion",
            font=("Segoe UI", 13),
            text_color=("gray50", "gray70")
        ).pack(pady=(0, 20))

        # Menu Button Container Card
        menu_card = ctk.CTkFrame(self, fg_color="transparent")
        menu_card.pack(fill="both", expand=True, padx=10)

        buttons = [
            ("🌤️  Today's Plan", "todays_plan", "#2980b9", "#2471a3"),
            ("🧭  Activity Advisor", "activity_advisor", "#27ae60", "#219653"),
            ("💧  Hydration & Safety", "hydration_safety", "#d35400", "#ba4a00"),
            ("⚖️  City Compare", "city_compare", "#8e44ad", "#7d3c98"),
            ("🚪  Exit Application", None, "#c0392b", "#a93226"),
        ]

        for text, target, color, hover in buttons:
            cmd = (lambda t=target: self.app.show_page(t)) if target else self.app.window.destroy
            btn = ctk.CTkButton(
                menu_card,
                text=text,
                font=("Segoe UI", 15, "bold"),
                height=50,
                corner_radius=12,
                fg_color=color,
                hover_color=hover,
                command=cmd
            )
            btn.pack(fill="x", pady=8)


# ==========================================
# TODAY'S PLAN PAGE
# ==========================================
class TodaysPlanPage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.planner = TodaysPlanner(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

    def display_widgets(self):
        ctk.CTkButton(
            self, text="← Back to Home", font=("Segoe UI", 12, "bold"),
            width=110, height=32, corner_radius=8, fg_color="gray50",
            command=lambda: self.app.show_page("home")
        ).pack(anchor="nw", padx=5, pady=(0, 10))

        ctk.CTkLabel(self, text="Today's Plan", font=("Segoe UI", 20, "bold")).pack(pady=(0, 15))

        ctrl_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("#f0f0f0", "#222222"))
        ctrl_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(ctrl_frame, text="Select State / Region:", font=("Segoe UI", 12)).pack(anchor="w", padx=15, pady=(12, 2))
        
        self.selected_state = ctk.StringVar(value=self.states[0])
        ctk.CTkComboBox(
            ctrl_frame, variable=self.selected_state, values=self.states,
            font=("Segoe UI", 14), height=38, corner_radius=8
        ).pack(fill="x", padx=15, pady=5)

        ctk.CTkButton(
            ctrl_frame, text="Generate Plan", font=("Segoe UI", 14, "bold"),
            height=40, corner_radius=8, command=self.on_click
        ).pack(fill="x", padx=15, pady=(10, 15))

        self.result_label = ctk.CTkLabel(
            self, text="Pick a region and generate your personalized plan.",
            font=("Segoe UI", 13), justify="left", wraplength=440,
            corner_radius=10, fg_color=("#e8f4fd", "#1b2a3a"), padx=15, pady=12
        )
        self.result_label.pack(fill="x", padx=5, pady=10)

        self.hourly_frame = ctk.CTkScrollableFrame(self, corner_radius=12, height=180)
        self.hourly_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def display_hourly_scores(self, state):
        for w in self.hourly_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.hourly_frame, text="🟢 Good (70+)  🟡 Moderate (40-69)  🔴 Poor (<40)",
            font=("Segoe UI", 11), text_color="gray60"
        ).pack(pady=(0, 5))

        for item in self.planner.score_hours(state):
            entry, score = item["entry"], item["score"]
            row = ctk.CTkLabel(
                self.hourly_frame,
                text=f"  {entry['hour']:02d}:00    |    {entry['temp_c']}°C    |    Rain {entry['rain_chance_pct']}%    |    Score: {score}/100",
                font=("Segoe UI", 12, "bold"), fg_color=get_score_color(score),
                corner_radius=8, anchor="w", padx=12, height=34, text_color="#ffffff"
            )
            row.pack(fill="x", pady=3)

    def on_click(self):
        state = self.selected_state.get()
        self.result_label.configure(text=self.planner.create_plan(state))
        self.display_hourly_scores(state)

    def go_back(self):
        self.app.show_page("home")


# ==========================================
# ACTIVITY ADVISOR PAGE
# ==========================================
class ActivityAdvisorPage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.advisor = ActivityAdvisor(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

    def display_widgets(self):
        ctk.CTkButton(
            self, text="← Back to Home", font=("Segoe UI", 12, "bold"),
            width=110, height=32, corner_radius=8, fg_color="gray50",
            command=self.go_back
        ).pack(anchor="nw", padx=5, pady=(0, 10))

        ctk.CTkLabel(self, text="Activity Advisor", font=("Segoe UI", 20, "bold")).pack(pady=(0, 15))

        ctrl_card = ctk.CTkFrame(self, corner_radius=12, fg_color=("#f0f0f0", "#222222"))
        ctrl_card.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(ctrl_card, text="Choose State:", font=("Segoe UI", 12)).pack(anchor="w", padx=15, pady=(12, 2))
        
        self.selected_state = ctk.StringVar(value=self.states[0])
        ctk.CTkComboBox(
            ctrl_card, variable=self.selected_state, values=self.states,
            font=("Segoe UI", 14), height=38, corner_radius=8
        ).pack(fill="x", padx=15, pady=5)

        ctk.CTkButton(
            ctrl_card, text="Get Recommendations", font=("Segoe UI", 14, "bold"),
            height=40, corner_radius=8, command=self.show_advice
        ).pack(fill="x", padx=15, pady=(10, 15))

        self.result_label = ctk.CTkLabel(
            self, text="Select a region to receive curated activity suggestions.",
            font=("Segoe UI", 13), justify="left", wraplength=440,
            corner_radius=10, fg_color=("#eafaf1", "#142d1e"), padx=15, pady=12
        )
        self.result_label.pack(fill="both", expand=True, padx=5, pady=10)

    def show_advice(self):
        text = self.advisor.create_advice_text(self.selected_state.get())
        if text is None:
            self.result_label.configure(text="No weather data found.")
            return
        self.result_label.configure(text=text)

    def go_back(self):
        self.app.show_page("home")


# ==========================================
# HYDRATION & SAFETY PAGE
# ==========================================
class HydrationSafetyPage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.calculator = HydrationCalculator(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

    def display_widgets(self):
        ctk.CTkButton(
            self, text="← Back to Home", font=("Segoe UI", 12, "bold"),
            width=110, height=32, corner_radius=8, fg_color="gray50",
            command=self.go_back
        ).pack(anchor="nw", padx=5, pady=(0, 10))

        ctk.CTkLabel(self, text="Hydration & Safety", font=("Segoe UI", 20, "bold")).pack(pady=(0, 15))

        ctrl_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("#f0f0f0", "#222222"))
        ctrl_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(ctrl_frame, text="Choose State:", font=("Segoe UI", 12)).pack(anchor="w", padx=15, pady=(12, 2))
        
        self.selected_state = ctk.StringVar(value=self.states[0])
        ctk.CTkComboBox(
            ctrl_frame, variable=self.selected_state, values=self.states,
            font=("Segoe UI", 14), height=38, corner_radius=8
        ).pack(fill="x", padx=15, pady=5)

        ctk.CTkButton(
            ctrl_frame, text="Check Hydration Needs", font=("Segoe UI", 14, "bold"),
            height=40, corner_radius=8, command=self.on_click
        ).pack(fill="x", padx=15, pady=(10, 15))

        self.result_label = ctk.CTkLabel(
            self, text="Select a region to analyze heat risk and water requirements.",
            font=("Segoe UI", 13), justify="left", wraplength=440,
            corner_radius=10, fg_color=("#fef9e7", "#332711"), padx=15, pady=12
        )
        self.result_label.pack(fill="x", padx=5, pady=10)

        self.hourly_frame = ctk.CTkScrollableFrame(self, corner_radius=12, height=150)
        self.hourly_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def display_hourly_risk(self, state):
        for w in self.hourly_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.hourly_frame, text="🟢 Low  🟡 Moderate  🟠 High  🔴 Danger",
            font=("Segoe UI", 11), text_color="gray60"
        ).pack(pady=(0, 5))

        for res in self.calculator.get_hourly_results(state):
            row = ctk.CTkLabel(
                self.hourly_frame,
                text=f"  {res['hour']:02d}:00    |    {res['temperature']}°C (feels {res['feels_like']}°C)    |    {res['level']}    |    {res['water_ml']} ml/h",
                font=("Segoe UI", 12, "bold"), fg_color=get_level_color(res["level"]),
                corner_radius=8, anchor="w", padx=12, height=34, text_color="#ffffff"
            )
            row.pack(fill="x", pady=3)

    def on_click(self):
        state = self.selected_state.get()
        summary, level = self.calculator.create_summary(state)
        self.result_label.configure(
            text=summary, fg_color=get_level_color(level), text_color="#ffffff"
        )
        self.display_hourly_risk(state)

    def go_back(self):
        self.app.show_page("home")


# ==========================================
# CITY COMPARE PAGE
# ==========================================
class CityComparePage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.comparer = CityCompare(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

    def display_widgets(self):
        ctk.CTkButton(
            self, text="← Back to Home", font=("Segoe UI", 12, "bold"),
            width=110, height=32, corner_radius=8, fg_color="gray50",
            command=self.go_back
        ).pack(anchor="nw", padx=5, pady=(0, 10))

        ctk.CTkLabel(self, text="City Compare", font=("Segoe UI", 20, "bold")).pack(pady=(0, 15))

        ctrl_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("#f0f0f0", "#222222"))
        ctrl_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(ctrl_frame, text="Select City A:", font=("Segoe UI", 12)).pack(anchor="w", padx=15, pady=(10, 2))
        self.state_a = ctk.StringVar(value=self.states[0])
        ctk.CTkComboBox(ctrl_frame, variable=self.state_a, values=self.states, font=("Segoe UI", 14), height=35).pack(fill="x", padx=15, pady=2)

        ctk.CTkLabel(ctrl_frame, text="Select City B:", font=("Segoe UI", 12)).pack(anchor="w", padx=15, pady=(10, 2))
        self.state_b = ctk.StringVar(value=self.states[1])
        ctk.CTkComboBox(ctrl_frame, variable=self.state_b, values=self.states, font=("Segoe UI", 14), height=35).pack(fill="x", padx=15, pady=2)

        ctk.CTkButton(
            ctrl_frame, text="Compare Cities", font=("Segoe UI", 14, "bold"),
            height=40, corner_radius=8, command=self.on_click
        ).pack(fill="x", padx=15, pady=(15, 15))

        self.result_label = ctk.CTkLabel(
            self, text="Select two cities to compare conditions and outdoor suitability.",
            font=("Segoe UI", 13), justify="left", wraplength=440,
            corner_radius=10, fg_color=("#f4ecf7", "#2a1b38"), padx=15, pady=12
        )
        self.result_label.pack(fill="both", expand=True, padx=5, pady=10)

    def on_click(self):
        text = self.comparer.create_comparison_text(self.state_a.get(), self.state_b.get())
        self.result_label.configure(text=text)

    def go_back(self):
        self.app.show_page("home")
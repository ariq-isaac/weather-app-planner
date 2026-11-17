# UI LAYER
# CustomTkinter UI featuring side-by-side comparison cards and modern dashboard controls.

import customtkinter as ctk
from logic import TodaysPlanner, ActivityAdvisor, HydrationCalculator, CityCompare, get_score_color, get_level_color


class HomePage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.display_widgets()

    def display_widgets(self):
        header_card = ctk.CTkFrame(self, corner_radius=16, border_width=1, border_color=("#e1e1e1", "#2d2d2d"))
        header_card.pack(fill="x", pady=(10, 20), padx=10)

        ctk.CTkLabel(header_card, text="🌤️ Weather Planner", font=("Segoe UI", 26, "bold")).pack(pady=(25, 5))
        ctk.CTkLabel(header_card, text="Your intelligent daily outdoor & safety companion", font=("Segoe UI", 13), text_color=("gray50", "gray70")).pack(pady=(0, 25))

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
            ctk.CTkButton(menu_card, text=text, font=("Segoe UI", 15, "bold"), height=50, corner_radius=12, fg_color=color, hover_color=hover, command=cmd).pack(fill="x", pady=8)


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
        ctk.CTkButton(self, text="← Back to Home", font=("Segoe UI", 12, "bold"), width=120, height=32, corner_radius=8, fg_color="gray50", command=lambda: self.app.show_page("home")).pack(anchor="nw", padx=5, pady=(0, 10))
        ctk.CTkLabel(self, text="Today's Plan", font=("Segoe UI", 22, "bold")).pack(pady=(0, 15))

        ctrl_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("#f0f0f0", "#222222"))
        ctrl_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(ctrl_frame, text="Select State / Region:", font=("Segoe UI", 12)).pack(anchor="w", padx=15, pady=(12, 2))
        self.selected_state = ctk.StringVar(value=self.states[0])
        ctk.CTkComboBox(ctrl_frame, variable=self.selected_state, values=self.states, font=("Segoe UI", 14), height=38, corner_radius=8).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(ctrl_frame, text="Generate Plan", font=("Segoe UI", 14, "bold"), height=40, corner_radius=8, command=self.on_click).pack(fill="x", padx=15, pady=(10, 15))

        self.result_label = ctk.CTkLabel(self, text="Pick a region and generate your personalized plan.", font=("Segoe UI", 13), justify="left", wraplength=800, corner_radius=10, fg_color=("#e8f4fd", "#1b2a3a"), padx=15, pady=12)
        self.result_label.pack(fill="x", padx=5, pady=10)

        self.hourly_frame = ctk.CTkScrollableFrame(self, corner_radius=12, height=220)
        self.hourly_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def display_hourly_scores(self, state):
        for w in self.hourly_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.hourly_frame, text="🟢 Good (70+)  🟡 Moderate (40-69)  🔴 Poor (<40)", font=("Segoe UI", 11), text_color="gray60").pack(pady=(0, 5))
        for item in self.planner.score_hours(state):
            entry, score = item["entry"], item["score"]
            ctk.CTkLabel(self.hourly_frame, text=f"  {entry['hour']:02d}:00    |    {entry['temp_c']}°C    |    Rain {entry['rain_chance_pct']}%    |    Score: {score}/100", font=("Segoe UI", 12, "bold"), fg_color=get_score_color(score), corner_radius=8, anchor="w", padx=12, height=34, text_color="#ffffff").pack(fill="x", pady=3)

    def on_click(self):
        state = self.selected_state.get()
        self.result_label.configure(text=self.planner.create_plan(state))
        self.display_hourly_scores(state)


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
        ctk.CTkButton(self, text="← Back to Home", font=("Segoe UI", 12, "bold"), width=120, height=32, corner_radius=8, fg_color="gray50", command=lambda: self.app.show_page("home")).pack(anchor="nw", padx=5, pady=(0, 10))
        ctk.CTkLabel(self, text="Activity Advisor", font=("Segoe UI", 22, "bold")).pack(pady=(0, 15))

        ctrl_card = ctk.CTkFrame(self, corner_radius=12, fg_color=("#f0f0f0", "#222222"))
        ctrl_card.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(ctrl_card, text="Choose State:", font=("Segoe UI", 12)).pack(anchor="w", padx=15, pady=(12, 2))
        self.selected_state = ctk.StringVar(value=self.states[0])
        ctk.CTkComboBox(ctrl_card, variable=self.selected_state, values=self.states, font=("Segoe UI", 14), height=38, corner_radius=8).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(ctrl_card, text="Get Recommendations", font=("Segoe UI", 14, "bold"), height=40, corner_radius=8, command=self.show_advice).pack(fill="x", padx=15, pady=(10, 15))

        self.result_label = ctk.CTkLabel(self, text="Select a region to receive curated activity suggestions.", font=("Segoe UI", 13), justify="left", wraplength=800, corner_radius=10, fg_color=("#eafaf1", "#142d1e"), padx=15, pady=12)
        self.result_label.pack(fill="both", expand=True, padx=5, pady=10)

    def show_advice(self):
        text = self.advisor.create_advice_text(self.selected_state.get())
        self.result_label.configure(text=text if text else "No weather data found.")


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
        ctk.CTkButton(self, text="← Back to Home", font=("Segoe UI", 12, "bold"), width=120, height=32, corner_radius=8, fg_color="gray50", command=lambda: self.app.show_page("home")).pack(anchor="nw", padx=5, pady=(0, 10))
        ctk.CTkLabel(self, text="Hydration & Safety", font=("Segoe UI", 22, "bold")).pack(pady=(0, 15))

        ctrl_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("#f0f0f0", "#222222"))
        ctrl_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(ctrl_frame, text="Choose State:", font=("Segoe UI", 12)).pack(anchor="w", padx=15, pady=(12, 2))
        self.selected_state = ctk.StringVar(value=self.states[0])
        ctk.CTkComboBox(ctrl_frame, variable=self.selected_state, values=self.states, font=("Segoe UI", 14), height=38, corner_radius=8).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(ctrl_frame, text="Check Hydration Needs", font=("Segoe UI", 14, "bold"), height=40, corner_radius=8, command=self.on_click).pack(fill="x", padx=15, pady=(10, 15))

        self.result_label = ctk.CTkLabel(self, text="Select a region to analyze heat risk and water requirements.", font=("Segoe UI", 13), justify="left", wraplength=800, corner_radius=10, fg_color=("#fef9e7", "#332711"), padx=15, pady=12)
        self.result_label.pack(fill="x", padx=5, pady=10)

        self.hourly_frame = ctk.CTkScrollableFrame(self, corner_radius=12, height=180)
        self.hourly_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def display_hourly_risk(self, state):
        for w in self.hourly_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.hourly_frame, text="🟢 Low  🟡 Moderate  🟠 High  🔴 Danger", font=("Segoe UI", 11), text_color="gray60").pack(pady=(0, 5))
        for res in self.calculator.get_hourly_results(state):
            ctk.CTkLabel(self.hourly_frame, text=f"  {res['hour']:02d}:00    |    {res['temperature']}°C (feels {res['feels_like']}°C)    |    {res['level']}    |    {res['water_ml']} ml/h", font=("Segoe UI", 12, "bold"), fg_color=get_level_color(res["level"]), corner_radius=8, anchor="w", padx=12, height=34, text_color="#ffffff").pack(fill="x", pady=3)

    def on_click(self):
        state = self.selected_state.get()
        summary, level = self.calculator.create_summary(state)
        self.result_label.configure(text=summary, fg_color=get_level_color(level), text_color="#ffffff")
        self.display_hourly_risk(state)


# ==========================================
# CITY COMPARE PAGE (Side-by-Side Dashboard Cards)
# ==========================================
class CityComparePage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.comparer = CityCompare(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

    def display_widgets(self):
        ctk.CTkButton(self, text="← Back to home page", font=("Segoe UI", 12, "bold"), width=140, height=32, corner_radius=8, fg_color="transparent", text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"), command=lambda: self.app.show_page("home")).pack(anchor="nw", padx=0, pady=(0, 5))
        
        ctk.CTkLabel(self, text="City Compare", font=("Segoe UI", 24, "bold")).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(self, text="Pick two Malaysian cities to compare their weather, rain chances, and outdoor comfort.", font=("Segoe UI", 13), text_color=("gray50", "gray70")).pack(anchor="w", pady=(0, 15))

        # Top Control Bar
        ctrl_card = ctk.CTkFrame(self, corner_radius=14, border_width=1, border_color=("#e1e1e1", "#2d2d2d"), fg_color=("#ffffff", "#1a1a1a"))
        ctrl_card.pack(fill="x", padx=0, pady=(0, 20))

        ctrl_grid = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        ctrl_grid.pack(fill="x", padx=20, pady=15)
        ctrl_grid.columnconfigure((0, 1, 2), weight=1)

        # First City Selector
        col1 = ctk.CTkFrame(ctrl_grid, fg_color="transparent")
        col1.grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkLabel(col1, text="First city", font=("Segoe UI", 11), text_color=("gray50", "gray70")).pack(anchor="w", pady=(0, 3))
        self.state_a = ctk.StringVar(value=self.states[0])
        ctk.CTkComboBox(col1, variable=self.state_a, values=self.states, font=("Segoe UI", 13), height=38, corner_radius=8).pack(fill="x")

        # Second City Selector
        col2 = ctk.CTkFrame(ctrl_grid, fg_color="transparent")
        col2.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkLabel(col2, text="Second city", font=("Segoe UI", 11), text_color=("gray50", "gray70")).pack(anchor="w", pady=(0, 3))
        self.state_b = ctk.StringVar(value=self.states[1] if len(self.states) > 1 else self.states[0])
        ctk.CTkComboBox(col2, variable=self.state_b, values=self.states, font=("Segoe UI", 13), height=38, corner_radius=8).pack(fill="x")

        # Compare Button Column
        col3 = ctk.CTkFrame(ctrl_grid, fg_color="transparent")
        col3.grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkLabel(col3, text="", font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 3)) # spacer
        ctk.CTkButton(col3, text="Compare", font=("Segoe UI", 14, "bold"), height=38, corner_radius=8, fg_color="#2563eb", hover_color="#1d4ed8", command=self.on_click).pack(fill="x")

        # Side-by-Side Comparison Cards Container
        self.cards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_container.pack(fill="both", expand=True, padx=0, pady=0)
        self.cards_container.columnconfigure((0, 1), weight=1)
        self.cards_container.rowconfigure(0, weight=1)

        # Initial prompt card / placeholder view
        self.result_card = ctk.CTkLabel(
            self.cards_container, text="Select two cities above and click 'Compare' to view side-by-side metrics.",
            font=("Segoe UI", 13), text_color=("gray50", "gray70"),
            corner_radius=14, fg_color=("#f8f9fa", "#1e1e1e"), border_width=1, border_color=("#e1e1e1", "#2d2d2d")
        )
        self.result_card.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=2, pady=2)

    def on_click(self):
        state_a, state_b = self.state_a.get(), self.state_b.get()
        city_a = self.app.weather_data.get_city_data(state_a)
        city_b = self.app.weather_data.get_city_data(state_b)

        if not city_a or not city_b:
            return

        score_a = self.comparer.calculate_comfort_score(city_a)
        score_b = self.comparer.calculate_comfort_score(city_b)

        # Clear existing card widgets
        for widget in self.cards_container.winfo_children():
            widget.destroy()

        # Build Side-by-Side Cards
        self.build_city_card(self.cards_container, 0, state_a, city_a, score_a)
        self.build_city_card(self.cards_container, 1, state_b, city_b, score_b)

    def build_city_card(self, parent, col, state_name, city_data, score):
        card = ctk.CTkFrame(parent, corner_radius=14, border_width=1, border_color=("#e1e1e1", "#2d2d2d"), fg_color=("#ffffff", "#1a1a1a"))
        card.grid(row=0, column=col, sticky="nsew", padx=6, pady=2)

        # Card Header
        header_box = ctk.CTkFrame(card, fg_color="transparent")
        header_box.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(header_box, text=f"City: {state_name}", font=("Segoe UI", 11), text_color=("gray50", "gray70")).pack(anchor="w")
        ctk.CTkLabel(header_box, text=city_data["name"], font=("Segoe UI", 20, "bold")).pack(anchor="w")

        # Metric Box (Temperature & Comfort Score)
        metric_box = ctk.CTkFrame(card, corner_radius=10, fg_color=("#f8f9fa", "#222222"))
        metric_box.pack(fill="x", padx=16, pady=8)

        temp_frame = ctk.CTkFrame(metric_box, fg_color="transparent")
        temp_frame.pack(side="left", padx=14, pady=12)
        ctk.CTkLabel(temp_frame, text=f"{city_data['temperature']}°C", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ctk.CTkLabel(temp_frame, text=f"Humidity: {city_data['humidity']}% | UV: {city_data['uv_index']}", font=("Segoe UI", 11), text_color=("gray50", "gray70")).pack(anchor="w")

        score_frame = ctk.CTkFrame(metric_box, fg_color="transparent")
        score_frame.pack(side="right", padx=14, pady=12)
        ctk.CTkLabel(score_frame, text="Comfort score", font=("Segoe UI", 10), text_color=("gray50", "gray70")).pack(anchor="e")
        ctk.CTkLabel(score_frame, text=f"{score} / 100", font=("Segoe UI", 18, "bold"), text_color=get_score_color(score)).pack(anchor="e")

        # Verdict / Recommendation text
        desc_box = ctk.CTkFrame(card, fg_color="transparent")
        desc_box.pack(fill="x", padx=16, pady=10)
        
        status_text = "Very comfortable for being outside" if score >= 70 else ("Moderate conditions" if score >= 40 else "Challenging conditions")
        ctk.CTkLabel(desc_box, text=status_text, font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))

        # Rain Chance Footer Row
        footer_box = ctk.CTkFrame(card, fg_color="transparent")
        footer_box.pack(fill="x", padx=16, pady=(0, 16))
        
        ctk.CTkLabel(footer_box, text="Rain chance", font=("Segoe UI", 12), text_color=("gray50", "gray70")).pack(side="left")
        ctk.CTkLabel(footer_box, text=f"{city_data['rain_chance']}%", font=("Segoe UI", 13, "bold")).pack(side="right")
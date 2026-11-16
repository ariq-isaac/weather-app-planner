# THIS IS THE FIRST / HOMEPAGE OF THE PROGRAM

import tkinter as tk

# Imports the weather data and the logic classes
from data import WeatherData
from logic import CityCompare
from logic import TodaysPlanner
from logic import ActivityAdvisor
from logic import HydrationCalculator

# Imports the tkinter pages and shared UI components from ui.py
from ui import (
    Theme,
    FlatButton,
    MenuCard,
    WeatherIcon,
    WeatherSceneBanner,
    TodaysPlanPage,
    ActivityAdvisorPage,
    HydrationSafetyPage,
    CityComparePage,
    font,
    make_banner,
    make_card,
    make_dropdown,
    describe_weather,
    get_entry_for_state,
    apply_weather,
    current_ambient,
    register_surface,
    default_state,
)


# ==========================================
# THE HOME PAGE
# ==========================================
class HomePage(tk.Frame):

    # Page Initialization
    def __init__(self, parent, app):
        bg = current_ambient()
        super().__init__(parent, bg=bg)
        self.app = app
        register_surface(self)
        self.states = self.app.weather_data.get_states()
        self.display_widgets()

    # Display Widgets
    def display_widgets(self):
        # Clean light header matching the rest of the UI
        self.header, _, _ = make_banner(
            self,
            "Weather Planner",
            "Check live Malaysian city conditions, comfort scores, and outdoor plans."
        )

        # Main centered content container
        content = tk.Frame(self, bg=current_ambient())
        content.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        register_surface(content)

        # ------------------------------------------
        # TOP LIVE WEATHER PREVIEW CARD
        # ------------------------------------------
        hero_card = make_card(content, highlight=True)
        hero_card.pack(fill="x", pady=(0, 16))

        hero_inner = tk.Frame(hero_card, bg=Theme.CARD)
        hero_inner.pack(fill="x", padx=20, pady=16)
        hero_inner.grid_columnconfigure(0, weight=3)
        hero_inner.grid_columnconfigure(1, weight=2)

        # Left side: Scenic animated banner
        self.scene = WeatherSceneBanner(hero_inner, height=112)
        self.scene.grid(row=0, column=0, sticky="nsew", padx=(0, 18))

        # Right side: Location picker + live weather metrics
        info_col = tk.Frame(hero_inner, bg=Theme.CARD)
        info_col.grid(row=0, column=1, sticky="nsew")

        top_bar = tk.Frame(info_col, bg=Theme.CARD)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(
            top_bar, text="Current location", font=font(9, "bold"),
            bg=Theme.CARD, fg=Theme.MUTED
        ).pack(side="left")

        self.selected_state = tk.StringVar(value=default_state(self.states))
        self.selected_state.trace_add("write", lambda *args: self.refresh_hero())
        self.state_menu = make_dropdown(info_col, self.selected_state, self.states)
        self.state_menu.pack(fill="x", pady=(0, 12))

        # Metrics row inside hero card
        metrics_row = tk.Frame(info_col, bg=Theme.CARD)
        metrics_row.pack(fill="x")

        self.hero_icon = WeatherIcon(metrics_row, size=44, box_bg="#F8FAFC")
        self.hero_icon.pack(side="left", padx=(0, 12))

        temp_box = tk.Frame(metrics_row, bg=Theme.CARD)
        temp_box.pack(side="left")

        self.hero_temp = tk.Label(
            temp_box, text="--°C", font=font(18, "bold"),
            bg=Theme.CARD, fg=Theme.TEXT, anchor="w"
        )
        self.hero_temp.pack(anchor="w")

        self.hero_cond = tk.Label(
            temp_box, text="Loading...", font=font(9),
            bg=Theme.CARD, fg=Theme.MUTED, anchor="w"
        )
        self.hero_cond.pack(anchor="w")

        score_box = tk.Frame(metrics_row, bg=Theme.CARD)
        score_box.pack(side="right")

        tk.Label(
            score_box, text="Comfort", font=font(9),
            bg=Theme.CARD, fg=Theme.MUTED, anchor="e"
        ).pack(anchor="e")

        self.hero_score = tk.Label(
            score_box, text="-- / 100", font=font(12, "bold"),
            bg=Theme.CARD, fg=Theme.PRIMARY, anchor="e"
        )
        self.hero_score.pack(anchor="e")

        # ------------------------------------------
        # 2x2 NAVIGATION CARDS GRID
        # ------------------------------------------
        self.button_frame = tk.Frame(content, bg=current_ambient())
        self.button_frame.pack(fill="both", expand=True)
        self.button_frame.grid_columnconfigure(0, weight=1, uniform="menu_cols")
        self.button_frame.grid_columnconfigure(1, weight=1, uniform="menu_cols")
        register_surface(self.button_frame)

        self.todays_plan = MenuCard(
            self.button_frame,
            "Today's Plan",
            "Hour-by-hour comfort outlook for your state",
            self.open_todays_plan,
            icon_kind="clear"
        )
        self.todays_plan.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))

        self.activity_advisor = MenuCard(
            self.button_frame,
            "Activity Advisor",
            "Advice for what to do in the current weather",
            self.open_activity_advisor,
            icon_kind="cloudy"
        )
        self.activity_advisor.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))

        self.hydration_safety = MenuCard(
            self.button_frame,
            "Hydration & Safety",
            "Heat risk and how much water you need",
            self.open_hydration_safety,
            icon_kind="hot"
        )
        self.hydration_safety.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))

        self.city_compare = MenuCard(
            self.button_frame,
            "City Compare",
            "Compare two places side by side",
            self.open_city_compare,
            icon_kind="rain"
        )
        self.city_compare.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))

        # Bottom footer bar with Exit button
        footer = tk.Frame(content, bg=current_ambient())
        footer.pack(fill="x", pady=(6, 0))
        register_surface(footer)

        self.exit = FlatButton(
            footer, "Exit Application", self.app.window.destroy,
            style="secondary", size=10, padx=18, pady=8
        )
        self.exit.pack(side="right")

        # Load initial weather preview
        self.refresh_hero()

    def refresh_hero(self):
        state = self.selected_state.get()
        apply_weather(self.app, state)
        entry, score = get_entry_for_state(self.app, state)
        kind, night, label, temp, rain = describe_weather(entry)

        self.scene.set_weather(kind, night)
        self.hero_icon.set_kind(kind, night)
        self.hero_temp.config(text=f"{temp}°C" if temp is not None else "--°C")
        self.hero_cond.config(text=f"{label}  •  Rain {rain}%")
        self.hero_score.config(text=f"{int(score)} / 100")

    # Functions that will be used as event listeners for buttons
    def open_city_compare(self):
        self.app.show_page("city_compare")

    def open_todays_plan(self):
        self.app.show_page("todays_plan")

    def open_activity_advisor(self):
        self.app.show_page("activity_advisor")

    def open_hydration_safety(self):
        self.app.show_page("hydration_safety")


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
        self.weather_data = WeatherData()

        # The logic objects are made once here (they need the weather data)
        # Every page uses them through the app, for example self.app.todays_planner
        self.todays_planner = TodaysPlanner(self.weather_data)
        self.activity_advisor = ActivityAdvisor(self.weather_data)
        self.hydration_calculator = HydrationCalculator(self.weather_data)
        self.city_compare = CityCompare(self.weather_data)

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
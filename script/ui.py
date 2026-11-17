# UI LAYER
# This file builds the user interface for every tkinter page (including the home page).
# All the calculations are done by the classes in logic.py.
# All the data is read through the WeatherData class in data.py.
# The main window and the page switching come from homepage.py.
# Each page creates the logic classes it needs and uses them.

import math
import random
from datetime import datetime
import tkinter as tk
from tkinter import font as tkfont

# imports the functions for the logic / calculation
from logic import TodaysPlanner
from logic import ActivityAdvisor
from logic import HydrationCalculator
from logic import CityCompare


# ==========================================
# THEME & PALETTES (Clean Light UI)
# ==========================================
class Theme:
    BG = "#F8FAFC"            # clean off-white page background
    CARD = "#FFFFFF"          # pure white card background
    INPUT_BG = "#FFFFFF"
    PRIMARY = "#2563EB"       # bright royal blue button & active border
    PRIMARY_DARK = "#1D4ED8"
    PRIMARY_SOFT = "#EFF6FF"
    PRIMARY_BORDER = "#93C5FD"
    TEXT = "#0F172A"          # deep slate heading text
    SUBTEXT = "#475569"
    MUTED = "#64748B"
    BORDER = "#E2E8F0"

    # (row background, accent stripe)
    GOOD = ("#DCFCE7", "#22C55E")
    MODERATE = ("#FEF3C7", "#F59E0B")
    HIGH = ("#FFEDD5", "#F97316")
    DANGER = ("#FEE2E2", "#EF4444")


# Subtle ambient tint based on live weather (stays very light and clean)
AMBIENT_BG = {
    "clear": "#F8FAFC",
    "hot": "#FFFBF5",
    "cloudy": "#F8FAFC",
    "rain": "#F1F5F9",
    "storm": "#EEF2F6",
    "night": "#F4F6FB",
}

SKY = {
    "clear": ("#3888E8", "#B6E0FE"),
    "hot": ("#EA580C", "#FDE68A"),
    "cloudy": ("#64748B", "#CBD5E1"),
    "rain": ("#334155", "#94A3B8"),
    "storm": ("#1E293B", "#475569"),
}

CLOUD = {
    "clear": "#FFFFFF",
    "hot": "#FFFBEB",
    "cloudy": "#F1F5F9",
    "rain": "#CBD5E1",
    "storm": "#94A3B8",
}

NIGHT = "#0B132B"

_font_family = None


# ==========================================
# SMALL HELPER FUNCTIONS
# ==========================================
def font(size=11, weight="normal"):
    """Picks the cleanest sans-serif font available."""
    global _font_family

    # Only look for the font the first time, then remember it
    if _font_family is None:
        available = set(tkfont.families())
        _font_family = "Arial"
        for name in ("Segoe UI", "Inter", "Helvetica Neue", "Ubuntu", "Arial"):
            if name in available:
                _font_family = name
                break

    return (_font_family, size, weight)


def blend(color_a, color_b, amount):
    """Mixes two hex colors. amount 0 = all A, 1 = all B."""
    mixed_parts = []

    # A hex color like "#2563EB" has three parts: red, green, blue
    # The parts sit at string positions 1-3, 3-5 and 5-7
    for start in (1, 3, 5):
        part_a = int(color_a[start:start + 2], 16)
        part_b = int(color_b[start:start + 2], 16)
        mixed_parts.append(int(part_a + (part_b - part_a) * amount))

    return "#%02x%02x%02x" % tuple(mixed_parts)


def default_state(states):
    """Returns the Sarawak entry if there is one, otherwise the first state."""
    for state in states:
        if "sarawak" in state.lower():
            return state

    if len(states) > 0:
        return states[0]
    return ""


def describe_weather(entry):
    """Turns one hourly entry into (kind, is_night, label, temperature, rain_pct).
    This only picks what to DISPLAY (icon type and wording). No scoring happens here."""
    hour = datetime.now().hour
    is_night = hour < 6 or hour >= 19

    kind = "clear"
    temp = None
    rain = 0

    try:
        rain = entry.get("rain_chance_pct", 0)
        temp = entry.get("temp_c", None)

        if rain >= 85:
            kind = "storm"
        elif rain >= 60:
            kind = "rain"
        elif rain >= 30:
            kind = "cloudy"
        elif temp is not None and temp >= 34 and not is_night:
            kind = "hot"
    except (AttributeError, TypeError):
        # entry is None (no data yet), so we keep the defaults above
        pass

    if 5 <= hour <= 9:
        cloudy_label = "Misty Morning Clouds"
    else:
        cloudy_label = "Partly Cloudy"

    if is_night:
        clear_label = "Clear Night"
    else:
        clear_label = "Clear & Sunny"

    labels = {
        "storm": "Thunderstorm",
        "rain": "Light Rain Showers",
        "cloudy": cloudy_label,
        "hot": "Hot & Sunny",
        "clear": clear_label,
    }
    return kind, is_night, labels[kind], temp, rain


# ==========================================
# GLOBAL WEATHER SYNC
# ==========================================
class Mood:
    """Holds the 'current weather' that every page shares."""
    app = None
    state = None
    entry = None
    planner = None
    icons = []
    themed_surfaces = []


def register_surface(widget):
    """Remembers a widget so its background can change with the weather."""
    Mood.themed_surfaces.append(widget)


def current_ambient():
    """Returns the page background color for the current weather."""
    kind, night, _, _, _ = describe_weather(Mood.entry)

    if night and kind in ("clear", "cloudy"):
        return AMBIENT_BG["night"]
    return AMBIENT_BG.get(kind, Theme.BG)


def get_entry_for_state(app, state):
    """Gets the weather entry and comfort score for the current hour.
    The work is done by a TodaysPlanner from logic.py (made once, then reused)."""
    if Mood.planner is None:
        Mood.planner = TodaysPlanner(app.weather_data)
    return Mood.planner.get_current_entry(state)


def apply_weather(app, state):
    """Updates the shared weather, then re-tints the page backgrounds and icons.
    Returns (entry, score) so the caller does not have to look them up again."""
    entry, score = get_entry_for_state(app, state)

    Mood.app = app
    Mood.state = state
    Mood.entry = entry

    bg = current_ambient()

    # Re-tint every registered background
    for widget in list(Mood.themed_surfaces):
        try:
            widget.config(bg=bg)
        except tk.TclError:
            # The widget was destroyed, so forget it
            Mood.themed_surfaces.remove(widget)

    # Refresh every live icon
    for icon in list(Mood.icons):
        try:
            icon.set_weather()
        except tk.TclError:
            Mood.icons.remove(icon)

    return entry, score


# ==========================================
# ANIMATED WEATHER ICON BADGE (GIF-like vector icon)
# ==========================================
class WeatherIcon(tk.Canvas):
    """Rounded soft icon box with animated sun, cloud, rain, or storm."""

    def __init__(self, parent, size=44, fixed_kind=None, box_bg="#F8FAFC"):
        super().__init__(
            parent, width=size, height=size, bg=box_bg,
            highlightthickness=1, highlightbackground=Theme.BORDER, bd=0
        )
        self.size = size
        self.fixed_kind = fixed_kind
        self.kind = fixed_kind or "cloudy"
        self.night = False
        self.t = random.randint(0, 40)

        # An icon without a fixed kind follows the live weather
        if fixed_kind is None:
            Mood.icons.append(self)
            self.set_weather()

        self.after(45, self.animate)

    def set_kind(self, kind, night=False):
        self.kind = kind
        self.night = night

    def set_weather(self):
        if self.fixed_kind is None:
            kind, night, _, _, _ = describe_weather(Mood.entry)
            self.kind = kind
            self.night = night

    def animate(self):
        try:
            if self.winfo_ismapped():
                self.t += 1
                self.draw()
                self.after(50, self.animate)
            else:
                # Hidden pages animate slowly to save CPU
                self.after(300, self.animate)
        except tk.TclError:
            # The widget was destroyed, so stop animating
            pass

    def draw(self):
        self.delete("all")
        s = self.size
        cx = s / 2
        cy = s / 2

        if self.kind in ("clear", "hot") and not self.night:
            # Sun with spinning rays
            r = s * 0.22
            pulse = math.sin(self.t * 0.1) * (s * 0.02)
            for i in range(8):
                ang = self.t * 0.03 + i * (math.pi / 4)
                self.create_line(
                    cx + math.cos(ang) * (r + 3), cy + math.sin(ang) * (r + 3),
                    cx + math.cos(ang) * (r + 7 + pulse), cy + math.sin(ang) * (r + 7 + pulse),
                    fill="#F59E0B", width=2, capstyle="round"
                )
            self.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#FBBF24", outline="")

        elif self.kind == "clear" and self.night:
            # Moon made of a yellow circle with a background circle cut out
            bob = math.sin(self.t * 0.08) * 1.5
            r = s * 0.24
            self.create_oval(cx - r, cy - r + bob, cx + r, cy + r + bob,
                             fill="#FACC15", outline="")
            self.create_oval(cx - r * 0.3, cy - r * 1.1 + bob,
                             cx + r * 1.2, cy + r * 0.6 + bob,
                             fill=self.cget("bg"), outline="")
        else:
            # Sun peeking behind the cloud
            if self.kind == "cloudy" and not self.night:
                pulse = math.sin(self.t * 0.08) * 1.2
                self.create_oval(
                    cx + s * 0.02 - pulse, cy - s * 0.24 - pulse,
                    cx + s * 0.28 + pulse, cy + s * 0.02 + pulse,
                    fill="#FBBF24", outline=""
                )

            drift = math.sin(self.t * 0.07) * (s * 0.035)

            if self.kind in ("rain", "storm"):
                y_off = -s * 0.05
            else:
                y_off = s * 0.03

            if self.kind == "cloudy":
                cloud_fill = "#FFFFFF"
                cloud_outline = "#CBD5E1"
            else:
                cloud_fill = "#94A3B8"
                cloud_outline = "#64748B"

            # The cloud is three circles and one rectangle
            for dx, dy, rad in ((-0.15, 0.04, 0.14), (0.0, -0.05, 0.18), (0.16, 0.04, 0.14)):
                x = cx + dx * s + drift
                y = cy + dy * s + y_off
                r = rad * s
                self.create_oval(x - r, y - r, x + r, y + r,
                                 fill=cloud_fill, outline=cloud_outline, width=1)
            self.create_rectangle(
                cx - 0.16 * s + drift, cy + y_off,
                cx + 0.16 * s + drift, cy + 0.17 * s + y_off,
                fill=cloud_fill, outline=""
            )

            # Falling rain drops
            if self.kind in ("rain", "storm"):
                for i, dx in enumerate((-0.12, 0.0, 0.12)):
                    drop_y = (self.t * 2.0 + i * 7) % (s * 0.26)
                    x = cx + dx * s
                    y = cy + s * 0.16 + drop_y
                    self.create_line(x, y, x - 2, y + 5, fill="#2563EB", width=2, capstyle="round")

            # Lightning bolt that flashes now and then
            if self.kind == "storm" and (self.t % 26) < 6:
                self.create_line(
                    cx, cy + 4, cx - 4, cy + 11, cx + 2, cy + 11, cx - 3, cy + 19,
                    fill="#F59E0B", width=2
                )


# ==========================================
# ANIMATED SCENIC WEATHER BANNER (Inside Cards)
# ==========================================
class WeatherSceneBanner(tk.Canvas):
    """Animated coastal city landscape banner whose sky & weather update live."""

    def __init__(self, parent, height=120):
        super().__init__(parent, height=height, bg="#7CC8FF",
                         highlightthickness=0, bd=0)
        self.w = 420
        self.h = height
        self.t = random.randint(0, 60)
        self.kind = "cloudy"
        self.night = False
        self.clouds = []
        self.drops = []
        self.flash = 0

        self.build_particles()
        self.bind("<Configure>", self.on_resize)
        self.after(40, self.tick)

    def set_weather(self, kind, night=False):
        # Only rebuild the clouds and drops when the weather really changed
        if kind != self.kind or night != self.night:
            self.kind = kind
            self.night = night
            self.build_particles()

    def on_resize(self, event):
        self.w = max(200, event.width)
        self.build_particles()

    def build_particles(self):
        cloud_counts = {"clear": 3, "hot": 2, "cloudy": 6, "rain": 6, "storm": 7}
        count = cloud_counts.get(self.kind, 4)

        # Each cloud: [x position, y position, size, speed]
        self.clouds = []
        for _ in range(count):
            cloud = [
                random.random(),
                random.uniform(0.10, 0.42),
                random.uniform(0.75, 1.3),
                random.uniform(0.15, 0.45),
            ]
            self.clouds.append(cloud)

        drop_counts = {"rain": 28, "storm": 55}
        drop_count = drop_counts.get(self.kind, 0)

        # Each drop: [x, y, fall speed, length]
        self.drops = []
        for _ in range(drop_count):
            drop = [
                random.uniform(0, self.w),
                random.uniform(0, self.h),
                random.uniform(6, 10),
                random.uniform(7, 11),
            ]
            self.drops.append(drop)

    def tick(self):
        try:
            if self.winfo_ismapped():
                self.t += 1
                self.draw_scene()
                self.after(40, self.tick)
            else:
                self.after(300, self.tick)
        except tk.TclError:
            pass

    def draw_scene(self):
        self.delete("all")
        w = self.w
        h = self.h

        # 1. Sky gradient
        top, bottom = SKY.get(self.kind, SKY["clear"])
        if self.night:
            top = blend(top, NIGHT, 0.72)
            bottom = blend(bottom, NIGHT, 0.62)

        steps = 16
        for i in range(steps):
            y0 = i * h / steps
            y1 = (i + 1) * h / steps + 1
            color = blend(top, bottom, i / (steps - 1))
            self.create_rectangle(0, y0, w, y1, fill=color, outline="")

        # Lightning flash
        if self.kind == "storm" and self.flash == 0 and random.random() < 0.01:
            self.flash = 4
        if self.flash > 0:
            self.create_rectangle(0, 0, w, h, fill="#FFFFFF", stipple="gray25", outline="")
            self.flash -= 1

        # 2. Sun or Moon
        if self.kind in ("clear", "hot", "cloudy"):
            cx = w * 0.80
            cy = h * 0.24
            if self.night:
                self.create_oval(cx - 12, cy - 12, cx + 12, cy + 12, fill="#FEF08A", outline="")
                self.create_oval(cx - 5, cy - 15, cx + 17, cy + 7, fill=top, outline="")
            else:
                pulse = math.sin(self.t * 0.08) * 2
                self.create_oval(cx - 18 - pulse, cy - 18 - pulse,
                                 cx + 18 + pulse, cy + 18 + pulse,
                                 fill="#FDE047", outline="")

        # 3. Drifting puffy clouds
        cloud_color = CLOUD.get(self.kind, "#FFFFFF")
        if self.night:
            cloud_color = blend(cloud_color, "#1E293B", 0.5)

        for cloud in self.clouds:
            x = (cloud[0] * w + cloud[3] * self.t) % (w + 180) - 90
            y = cloud[1] * h
            size = cloud[2]
            for dx, dy, r in ((-18, 4, 11), (-4, -3, 14), (12, 2, 12), (24, 5, 9)):
                self.create_oval(x + (dx - r) * size, y + (dy - r) * size,
                                 x + (dx + r) * size, y + (dy + r) * size,
                                 fill=cloud_color, outline="")

        # 4. Coastal hills & bay
        horizon = h * 0.62

        if self.night:
            water_color = "#1E3A8A"
        elif self.kind in ("clear", "hot"):
            water_color = "#2563EB"
        else:
            water_color = "#475569"

        self.create_rectangle(0, horizon, w, h, fill=water_color, outline="")

        ripple_color = blend(water_color, "#FFFFFF", 0.25)
        for i in range(6):
            rx = ((i * 85 + self.t * 0.6) % (w + 40)) - 20
            ry = horizon + 10 + (i % 3) * 11
            self.create_line(rx, ry, rx + 26, ry, fill=ripple_color, width=1)

        if self.night:
            hill_dark = "#0F291E"
            hill_mid = "#163828"
            land_color = "#1E293B"
        else:
            hill_dark = "#1E4620"
            hill_mid = "#2D5A27"
            land_color = "#334155"

        self.create_polygon(
            0, horizon, 0, h * 0.34, w * 0.16, h * 0.38,
            w * 0.34, h * 0.50, w * 0.52, horizon,
            fill=hill_dark, outline=""
        )
        self.create_polygon(
            0, horizon, 0, h * 0.44, w * 0.22, h * 0.48,
            w * 0.44, horizon,
            fill=hill_mid, outline=""
        )
        self.create_polygon(
            0, h, 0, horizon - 4, w * 0.38, horizon + 4,
            w * 0.56, horizon + 18, w * 0.42, h,
            fill=land_color, outline=""
        )

        # Small city buildings on the land
        building_colors = ("#F8FAFC", "#FDE68A", "#E2E8F0", "#FCA5A5")
        for bx in range(8, int(w * 0.44), 14):
            by = horizon - 2 + (bx / (w * 0.45)) * 12
            bh = 5 + (bx % 7)
            if self.night and bx % 3 == 0:
                color = "#FACC15"      # a lit window at night
            else:
                color = building_colors[bx % 4]
            self.create_rectangle(bx, by - bh, bx + 8, by, fill=color, outline="")

        if self.night:
            road_color = "#475569"
        else:
            road_color = "#CBD5E1"
        self.create_line(w * 0.52, horizon + 8, w, horizon + 5, fill=road_color, width=2)

        # 5. Rain streaks
        if len(self.drops) > 0:
            if self.night:
                rain_color = "#94A3B8"
            else:
                rain_color = "#E0F2FE"

            for drop in self.drops:
                drop[1] += drop[2]          # fall down
                drop[0] -= drop[2] * 0.2    # slide a little to the left
                if drop[1] > h:
                    # Back to the top at a new random x
                    drop[1] = -drop[3]
                    drop[0] = random.uniform(0, w + 30)
                self.create_line(drop[0], drop[1], drop[0] - 2, drop[1] + drop[3],
                                 fill=rain_color, width=1)


# ==========================================
# REUSABLE CLEAN UI COMPONENTS
# ==========================================
class FlatButton(tk.Label):
    """Crisp SaaS-style button."""

    STYLES = {
        "primary": dict(bg=Theme.PRIMARY, fg="white",
                        hover=Theme.PRIMARY_DARK, border=Theme.PRIMARY),
        "secondary": dict(bg=Theme.CARD, fg=Theme.TEXT,
                          hover="#F1F5F9", border=Theme.BORDER),
        "icon": dict(bg=Theme.CARD, fg=Theme.SUBTEXT,
                     hover="#F1F5F9", border=Theme.BORDER),
    }

    def __init__(self, parent, text, command, style="primary",
                 size=10, padx=20, pady=9):
        colors = self.STYLES[style]

        if style == "primary":
            weight = "bold"
        else:
            weight = "normal"

        super().__init__(
            parent,
            text=text,
            font=font(size, weight),
            bg=colors["bg"],
            fg=colors["fg"],
            padx=padx,
            pady=pady,
            cursor="hand2",
            takefocus=1,
            highlightthickness=1,
            highlightbackground=colors["border"],
            highlightcolor=Theme.PRIMARY
        )
        self.colors = colors
        self.command = command

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_press)
        self.bind("<Return>", self.on_press)
        self.bind("<space>", self.on_press)

    def on_enter(self, event):
        self.config(bg=self.colors["hover"])

    def on_leave(self, event):
        self.config(bg=self.colors["bg"])

    def on_press(self, event):
        self.command()


class MenuCard(tk.Frame):
    """Clean white navigation card for the home page."""

    def __init__(self, parent, title, description, command,
                 accent=Theme.PRIMARY, icon_kind="clear"):
        super().__init__(
            parent,
            bg=Theme.CARD,
            highlightthickness=1,
            highlightbackground=Theme.BORDER
        )
        self.command = command
        self.accent = accent

        self.icon = WeatherIcon(self, size=42, fixed_kind=icon_kind, box_bg=Theme.BG)
        self.icon.pack(side="left", padx=(16, 4), pady=14)

        self.arrow = tk.Label(
            self, text="›", font=font(20),
            bg=Theme.CARD, fg=Theme.MUTED
        )
        self.arrow.pack(side="right", padx=(0, 18))

        self.body = tk.Frame(self, bg=Theme.CARD)
        self.body.pack(side="left", fill="both", expand=True, padx=12, pady=14)

        self.title_label = tk.Label(
            self.body, text=title, font=font(13, "bold"),
            bg=Theme.CARD, fg=Theme.TEXT, anchor="w"
        )
        self.title_label.pack(fill="x")

        self.desc_label = tk.Label(
            self.body, text=description, font=font(10),
            bg=Theme.CARD, fg=Theme.MUTED, anchor="w"
        )
        self.desc_label.pack(fill="x", pady=(2, 0))

        # Every part of the card changes color together on hover
        self.surfaces = [self, self.body, self.title_label,
                         self.desc_label, self.arrow]

        # Every part of the card is clickable
        for widget in self.surfaces + [self.icon]:
            widget.config(cursor="hand2")
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)
            widget.bind("<Button-1>", self.on_press)

    def on_press(self, event):
        self.command()

    def on_enter(self, event):
        self.config(highlightbackground=Theme.PRIMARY_BORDER)
        for widget in self.surfaces:
            widget.config(bg=Theme.PRIMARY_SOFT)
        self.arrow.config(fg=Theme.PRIMARY)

    def on_leave(self, event):
        # Moving between two parts of the same card also triggers <Leave>,
        # so we only reset the colors when the mouse really left the card
        try:
            under_mouse = self.winfo_containing(*self.winfo_pointerxy())
        except (KeyError, tk.TclError):
            under_mouse = None

        if under_mouse in self.surfaces or under_mouse is self.icon:
            return

        self.config(highlightbackground=Theme.BORDER)
        for widget in self.surfaces:
            widget.config(bg=Theme.CARD)
        self.arrow.config(fg=Theme.MUTED)


def make_banner(parent, title, subtitle=None, back_command=None):
    """Clean light header. Returns the header frame."""
    bg = current_ambient()

    header = tk.Frame(parent, bg=bg)
    header.pack(fill="x", padx=28, pady=(20, 12))
    register_surface(header)

    if back_command is not None:
        back_label = tk.Label(
            header, text="← Back to home page", font=font(10),
            bg=bg, fg=Theme.SUBTEXT, cursor="hand2", anchor="w"
        )
        back_label.pack(anchor="w", pady=(0, 6))
        register_surface(back_label)

        # The back link changes color when the mouse is on it
        back_label.bind("<Button-1>", lambda e: back_command())
        back_label.bind("<Enter>", lambda e: back_label.config(fg=Theme.PRIMARY))
        back_label.bind("<Leave>", lambda e: back_label.config(fg=Theme.SUBTEXT))

    title_label = tk.Label(
        header, text=title, font=font(22, "bold"),
        bg=bg, fg=Theme.TEXT, anchor="w"
    )
    title_label.pack(anchor="w")
    register_surface(title_label)

    if subtitle:
        subtitle_label = tk.Label(
            header, text=subtitle, font=font(10),
            bg=bg, fg=Theme.MUTED, anchor="w"
        )
        subtitle_label.pack(anchor="w", pady=(3, 0))
        register_surface(subtitle_label)

    return header


def make_card(parent, highlight=False):
    if highlight:
        border_color = Theme.PRIMARY_BORDER
    else:
        border_color = Theme.BORDER

    return tk.Frame(
        parent, bg=Theme.CARD,
        highlightthickness=1,
        highlightbackground=border_color
    )


def make_field_label(parent, text):
    return tk.Label(
        parent, text=text, font=font(10, "bold"),
        bg=Theme.CARD, fg=Theme.TEXT, anchor="w"
    )


def make_dropdown(parent, variable, options):
    menu = tk.OptionMenu(parent, variable, *options)
    menu.config(
        font=font(10), anchor="w", padx=12, pady=8,
        bg=Theme.INPUT_BG, fg=Theme.TEXT,
        activebackground="#F8FAFC", activeforeground=Theme.TEXT,
        relief="flat", bd=0, cursor="hand2",
        highlightthickness=1, highlightbackground=Theme.BORDER,
        highlightcolor=Theme.PRIMARY
    )
    menu["menu"].config(
        font=font(10), bg=Theme.CARD, fg=Theme.TEXT,
        activebackground=Theme.PRIMARY, activeforeground="white",
        bd=0, relief="flat"
    )
    return menu


def make_result_card(parent, text, wraplength=600):
    card = make_card(parent)

    inner = tk.Frame(card, bg=Theme.CARD)
    inner.pack(fill="x", padx=18, pady=16)

    icon = WeatherIcon(inner, size=44, box_bg=Theme.BG)
    icon.pack(side="left", padx=(0, 14), anchor="n")

    label = tk.Label(
        inner, text=text, font=font(11), bg=Theme.CARD, fg=Theme.TEXT,
        justify="left", anchor="w", wraplength=wraplength
    )
    label.pack(side="left", fill="x", expand=True)

    return card, label


def make_legend(parent, items):
    bg = current_ambient()

    legend = tk.Frame(parent, bg=bg)
    register_surface(legend)

    for color, text in items:
        swatch = tk.Frame(legend, bg=color, width=10, height=10)
        swatch.pack(side="left", padx=(10, 4))

        label = tk.Label(legend, text=text, font=font(9, "bold"), bg=bg, fg=Theme.MUTED)
        label.pack(side="left")
        register_surface(label)

    return legend


def make_row(parent, cells, colors, weights):
    background, accent = colors

    row = tk.Frame(parent, bg=background)
    row.pack(fill="x", pady=2)

    # Colored stripe on the left side of the row
    stripe = tk.Frame(row, bg=accent, width=4)
    stripe.pack(side="left", fill="y")

    inner = tk.Frame(row, bg=background)
    inner.pack(side="left", fill="x", expand=True, padx=14, pady=7)

    last_column = len(cells) - 1

    for column, text in enumerate(cells):
        inner.grid_columnconfigure(column, weight=weights[column], uniform="cols")

        # The first and last cells are bold, the last one is right-aligned
        is_edge = column == 0 or column == last_column
        if is_edge:
            weight = "bold"
        else:
            weight = "normal"

        if column == last_column:
            side = "e"
        else:
            side = "w"

        label = tk.Label(
            inner, text=text,
            font=font(10, weight),
            bg=background, fg=Theme.TEXT,
            anchor=side
        )
        label.grid(row=0, column=column, sticky="ew")


# ==========================================
# PAGES
# ==========================================
class BasePage(tk.Frame):
    """Shared code for every page (including the home page)."""

    def __init__(self, parent, app):
        bg = current_ambient()
        super().__init__(parent, bg=bg)
        self.app = app
        register_surface(self)

        try:
            parent.configure(bg=bg)
            register_surface(parent)
        except tk.TclError:
            pass

    def make_content(self):
        """Creates a vertically scrollable container with mouse-wheel support."""
        bg = current_ambient()

        wrapper = tk.Frame(self, bg=bg)
        wrapper.pack(fill="both", expand=True)
        register_surface(wrapper)

        canvas = tk.Canvas(wrapper, bg=bg, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        register_surface(canvas)

        box = tk.Frame(canvas, bg=bg)
        register_surface(box)
        window_id = canvas.create_window((0, 0), window=box, anchor="nw")

        # Keep the scroll area the same size as the content
        box.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))

        def on_mousewheel(event):
            if not canvas.winfo_ismapped():
                return

            if event.num == 4:
                canvas.yview_scroll(-1, "units")       # Linux scroll up
            elif event.num == 5:
                canvas.yview_scroll(1, "units")        # Linux scroll down
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_wheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
            canvas.bind_all("<Button-4>", on_mousewheel)
            canvas.bind_all("<Button-5>", on_mousewheel)

        def unbind_wheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        # The wheel only scrolls while the mouse is over this page
        wrapper.bind("<Enter>", bind_wheel)
        wrapper.bind("<Leave>", unbind_wheel)

        inner_box = tk.Frame(box, bg=bg)
        inner_box.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        register_surface(inner_box)
        return inner_box

    def on_state_selected(self, *args):
        """Runs every time the dropdown value changes."""
        apply_weather(self.app, self.selected_state.get())

    def build_state_selector(self, parent, button_text, command):
        """Horizontal control bar: [dropdown] [button]."""
        bar = make_card(parent)
        bar.pack(fill="x")

        inner = tk.Frame(bar, bg=Theme.CARD)
        inner.pack(fill="x", padx=18, pady=14)
        inner.grid_columnconfigure(0, weight=3)
        inner.grid_columnconfigure(1, weight=0)

        label = make_field_label(inner, "Select city / state")
        label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.selected_state = tk.StringVar(value=default_state(self.states))
        self.selected_state.trace_add("write", self.on_state_selected)
        apply_weather(self.app, self.selected_state.get())

        menu = make_dropdown(inner, self.selected_state, self.states)
        menu.grid(row=1, column=0, sticky="ew", padx=(0, 12))

        button = FlatButton(inner, button_text, command, padx=24, pady=9)
        button.grid(row=1, column=1, sticky="e")
        return menu, button

    def go_back(self):
        self.app.show_page("home")


# ==========================================
# THE HOME PAGE
# ==========================================
class HomePage(BasePage):

    # Page Initialization
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.states = self.app.weather_data.get_states()
        self.display_widgets()

    # Display Widgets
    # The page is built in three parts, one method for each part
    def display_widgets(self):
        self.header = make_banner(
            self,
            "Weather Planner",
            "Check live Malaysian city conditions, comfort scores, and outdoor plans."
        )

        # Main content container
        content = tk.Frame(self, bg=current_ambient())
        content.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        register_surface(content)

        self.build_hero_card(content)
        self.build_menu_cards(content)
        self.build_footer(content)

        # Load the first weather preview
        self.refresh_hero()

    # ------------------------------------------
    # PART 1: TOP LIVE WEATHER PREVIEW CARD
    # ------------------------------------------
    def build_hero_card(self, content):
        hero_card = make_card(content, highlight=True)
        hero_card.pack(fill="x", pady=(0, 16))

        hero_inner = tk.Frame(hero_card, bg=Theme.CARD)
        hero_inner.pack(fill="x", padx=20, pady=16)
        hero_inner.grid_columnconfigure(0, weight=3)
        hero_inner.grid_columnconfigure(1, weight=2)

        # Left side: animated scenic banner
        self.scene = WeatherSceneBanner(hero_inner, height=112)
        self.scene.grid(row=0, column=0, sticky="nsew", padx=(0, 18))

        # Right side: location picker and live weather numbers
        info_col = tk.Frame(hero_inner, bg=Theme.CARD)
        info_col.grid(row=0, column=1, sticky="nsew")

        top_bar = tk.Frame(info_col, bg=Theme.CARD)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(
            top_bar, text="Current location", font=font(9, "bold"),
            bg=Theme.CARD, fg=Theme.MUTED
        ).pack(side="left")

        self.selected_state = tk.StringVar(value=default_state(self.states))
        self.selected_state.trace_add("write", self.on_state_changed)

        self.state_menu = make_dropdown(info_col, self.selected_state, self.states)
        self.state_menu.pack(fill="x", pady=(0, 12))

        # Row with the icon, the temperature and the comfort score
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
    # PART 2: 2x2 NAVIGATION CARDS GRID
    # ------------------------------------------
    def build_menu_cards(self, content):
        self.button_frame = tk.Frame(content, bg=current_ambient())
        self.button_frame.pack(fill="both", expand=True)
        self.button_frame.grid_columnconfigure(0, weight=1, uniform="menu_cols")
        self.button_frame.grid_columnconfigure(1, weight=1, uniform="menu_cols")
        register_surface(self.button_frame)

        self.todays_plan = self.add_menu_card(
            0, 0, "Today's Plan",
            "Hour-by-hour comfort outlook for your state",
            self.open_todays_plan, "clear"
        )
        self.activity_advisor = self.add_menu_card(
            0, 1, "Activity Advisor",
            "Advice for what to do in the current weather",
            self.open_activity_advisor, "cloudy"
        )
        self.hydration_safety = self.add_menu_card(
            1, 0, "Hydration & Safety",
            "Heat risk and how much water you need",
            self.open_hydration_safety, "hot"
        )
        self.city_compare = self.add_menu_card(
            1, 1, "City Compare",
            "Compare two places side by side",
            self.open_city_compare, "rain"
        )

    # Creates one menu card and puts it in the grid
    def add_menu_card(self, row, column, title, description, command, icon_kind):
        card = MenuCard(
            self.button_frame, title, description, command,
            icon_kind=icon_kind
        )

        # Left column leaves a gap on its right, right column leaves a gap on its left
        if column == 0:
            horizontal_gap = (0, 8)
        else:
            horizontal_gap = (8, 0)

        card.grid(row=row, column=column, sticky="nsew",
                  padx=horizontal_gap, pady=(0, 12))
        return card

    # ------------------------------------------
    # PART 3: FOOTER WITH THE EXIT BUTTON
    # ------------------------------------------
    def build_footer(self, content):
        footer = tk.Frame(content, bg=current_ambient())
        footer.pack(fill="x", pady=(6, 0))
        register_surface(footer)

        self.exit = FlatButton(
            footer, "Exit Application", self.app.window.destroy,
            style="secondary", size=10, padx=18, pady=8
        )
        self.exit.pack(side="right")

    # ------------------------------------------
    # UPDATING THE PREVIEW CARD
    # ------------------------------------------

    # Runs every time the dropdown changes
    def on_state_changed(self, *args):
        self.refresh_hero()

    def refresh_hero(self):
        state = self.selected_state.get()

        # apply_weather updates the page colors and returns the weather and score
        entry, score = apply_weather(self.app, state)
        kind, night, label, temp, rain = describe_weather(entry)

        self.scene.set_weather(kind, night)
        self.hero_icon.set_kind(kind, night)

        if temp is not None:
            self.hero_temp.config(text=f"{temp}°C")
        else:
            self.hero_temp.config(text="--°C")

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


class TodaysPlanPage(BasePage):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.planner = TodaysPlanner(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

    def display_widgets(self):
        self.header = make_banner(
            self,
            "Today's Plan",
            "See how every hour of the day looks for outdoor comfort.",
            back_command=self.go_back
        )

        content = self.make_content()

        self.state_menu, self.plan_button = self.build_state_selector(
            content, "Create Plan", self.on_click
        )

        card, self.result_label = make_result_card(
            content, "Choose a location and press Create Plan"
        )
        card.pack(fill="x", pady=(14, 10))

        self.hourly_frame = tk.Frame(content, bg=current_ambient())
        self.hourly_frame.pack(fill="x")
        register_surface(self.hourly_frame)

    def get_score_colors(self, score):
        if score >= 70:
            return Theme.GOOD
        if score >= 40:
            return Theme.MODERATE
        return Theme.DANGER

    def display_hourly_scores(self, state):
        # Remove the rows from the previous search
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        legend = make_legend(self.hourly_frame, [
            (Theme.GOOD[1], "Good"),
            (Theme.MODERATE[1], "Moderate"),
            (Theme.DANGER[1], "Poor"),
        ])
        legend.pack(pady=(0, 6))

        for item in self.planner.score_hours(state):
            entry = item["entry"]
            score = item["score"]

            cells = [
                f"{entry['hour']:02d}:00",
                f"{entry['temp_c']}°C",
                f"Rain {entry['rain_chance_pct']}%",
                f"Score {score}/100",
            ]
            make_row(
                self.hourly_frame,
                cells,
                self.get_score_colors(score),
                weights=[1, 1, 1, 1]
            )

    def on_click(self):
        state = self.selected_state.get()
        self.result_label.config(text=self.planner.create_plan(state))
        self.display_hourly_scores(state)


class ActivityAdvisorPage(BasePage):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.advisor = ActivityAdvisor(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

    def display_widgets(self):
        self.header = make_banner(
            self,
            "Activity Advisor",
            "Find out what suits the weather right now.",
            back_command=self.go_back
        )

        content = self.make_content()

        self.dropdown, self.advice_button = self.build_state_selector(
            content, "Get Advice", self.show_advice
        )

        card, self.result_label = make_result_card(
            content, "Choose a location and press Get Advice"
        )
        card.pack(fill="x", pady=(14, 0))

    def show_advice(self):
        text = self.advisor.create_advice_text(self.selected_state.get())

        if text is None:
            self.result_label.config(text="No weather data found.")
            return

        self.result_label.config(text=text)


class HydrationSafetyPage(BasePage):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.calculator = HydrationCalculator(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

    def display_widgets(self):
        self.header = make_banner(
            self,
            "Hydration & Safety",
            "Stay safe and well hydrated in the heat.",
            back_command=self.go_back
        )

        content = self.make_content()

        self.state_menu, self.check_button = self.build_state_selector(
            content, "Check Safety", self.on_click
        )

        self.result_card, self.result_label = make_result_card(
            content, "Choose a location and press Check Safety"
        )
        self.result_card.pack(fill="x", pady=(14, 10))

        self.hourly_frame = tk.Frame(content, bg=current_ambient())
        self.hourly_frame.pack(fill="x")
        register_surface(self.hourly_frame)

    def get_level_colors(self, level):
        if level == "Low":
            return Theme.GOOD
        if level == "Moderate":
            return Theme.MODERATE
        if level == "High":
            return Theme.HIGH
        return Theme.DANGER

    def display_hourly_risk(self, state):
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        legend = make_legend(self.hourly_frame, [
            (Theme.GOOD[1], "Low"),
            (Theme.MODERATE[1], "Moderate"),
            (Theme.HIGH[1], "High"),
            (Theme.DANGER[1], "Danger"),
        ])
        legend.pack(pady=(0, 6))

        for result in self.calculator.get_hourly_results(state):
            cells = [
                f"{result['hour']:02d}:00",
                f"{result['temperature']}°C (feels {result['feels_like']}°C)",
                f"{result['level']}",
                f"{result['water_ml']} ml/h",
            ]
            make_row(
                self.hourly_frame,
                cells,
                self.get_level_colors(result["level"]),
                weights=[1, 3, 2, 2]
            )

    def color_result_card(self, color):
        """Paints the result card (and everything inside it) one color."""
        self.result_card.config(bg=color)

        # The inner frame sits inside the card, and the icon and text sit inside that
        for inner in self.result_card.winfo_children():
            inner.config(bg=color)
            for child in inner.winfo_children():
                # The animated icon draws its own background, so skip it
                if isinstance(child, tk.Label):
                    child.config(bg=color)

    def on_click(self):
        state = self.selected_state.get()
        summary, level = self.calculator.create_summary(state)

        self.result_label.config(text=summary)
        self.color_result_card(self.get_level_colors(level)[0])
        self.display_hourly_risk(state)


# ==========================================
# CITY COMPARE PAGE
# ==========================================
class CityCompareCard(tk.Frame):
    """Side-by-side comparison card. It only DISPLAYS what the page gives it."""

    def __init__(self, parent, role_label, highlight=False):
        if highlight:
            border_color = Theme.PRIMARY_BORDER
        else:
            border_color = Theme.BORDER

        super().__init__(
            parent,
            bg=Theme.CARD,
            highlightthickness=1,
            highlightbackground=border_color
        )
        inner = tk.Frame(self, bg=Theme.CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        # Top row: "First city" on left, "Region" on right
        top_row = tk.Frame(inner, bg=Theme.CARD)
        top_row.pack(fill="x")

        tk.Label(
            top_row, text=role_label, font=font(9),
            bg=Theme.CARD, fg=Theme.MUTED
        ).pack(side="left")

        self.region_lbl = tk.Label(
            top_row, text="Malaysia", font=font(9),
            bg=Theme.CARD, fg=Theme.MUTED
        )
        self.region_lbl.pack(side="right")

        # City / State title
        self.city_lbl = tk.Label(
            inner, text="—", font=font(16, "bold"),
            bg=Theme.CARD, fg=Theme.TEXT, anchor="w"
        )
        self.city_lbl.pack(fill="x", pady=(2, 12))

        # Scenic animated weather landscape banner
        self.scene = WeatherSceneBanner(inner, height=118)
        self.scene.pack(fill="x", pady=(0, 14))

        # Middle row: [Icon + Temp + Condition] on the left, [Comfort score] on the right
        mid_row = tk.Frame(inner, bg=Theme.CARD)
        mid_row.pack(fill="x", pady=(0, 14))

        self.icon = WeatherIcon(mid_row, size=44, fixed_kind="cloudy", box_bg="#F8FAFC")
        self.icon.pack(side="left", padx=(0, 12))

        temp_col = tk.Frame(mid_row, bg=Theme.CARD)
        temp_col.pack(side="left")

        self.temp_lbl = tk.Label(
            temp_col, text="--°C", font=font(20, "bold"),
            bg=Theme.CARD, fg=Theme.TEXT, anchor="w"
        )
        self.temp_lbl.pack(anchor="w")

        self.cond_lbl = tk.Label(
            temp_col, text="Loading...", font=font(9),
            bg=Theme.CARD, fg=Theme.MUTED, anchor="w"
        )
        self.cond_lbl.pack(anchor="w")

        score_col = tk.Frame(mid_row, bg=Theme.CARD)
        score_col.pack(side="right")

        tk.Label(
            score_col, text="Comfort score", font=font(9),
            bg=Theme.CARD, fg=Theme.MUTED, anchor="e"
        ).pack(anchor="e")

        score_num_row = tk.Frame(score_col, bg=Theme.CARD)
        score_num_row.pack(anchor="e")

        self.score_lbl = tk.Label(
            score_num_row, text="--", font=font(15, "bold"),
            bg=Theme.CARD, fg=Theme.TEXT
        )
        self.score_lbl.pack(side="left")

        tk.Label(
            score_num_row, text=" / 100", font=font(11),
            bg=Theme.CARD, fg=Theme.MUTED
        ).pack(side="left", pady=(3, 0))

        # Thin divider line
        tk.Frame(inner, bg=Theme.BORDER, height=1).pack(fill="x", pady=(0, 12))

        # Comfort summary text
        self.comfort_desc = tk.Label(
            inner, text="Select cities and click Compare", font=font(10),
            bg=Theme.CARD, fg=Theme.SUBTEXT, anchor="w"
        )
        self.comfort_desc.pack(fill="x", pady=(0, 12))

        # Bottom row: "Rain chance" on the left, the percentage on the right
        bot_row = tk.Frame(inner, bg=Theme.CARD)
        bot_row.pack(fill="x")

        tk.Label(
            bot_row, text="Rain chance", font=font(10),
            bg=Theme.CARD, fg=Theme.MUTED
        ).pack(side="left")

        self.rain_lbl = tk.Label(
            bot_row, text="--%", font=font(10, "bold"),
            bg=Theme.CARD, fg=Theme.TEXT
        )
        self.rain_lbl.pack(side="right")

    def update_data(self, state_name, entry, score, comfort_text):
        """Fills the card. The comfort_text comes from logic.py (through the page)."""
        kind, night, label, temp, rain = describe_weather(entry)

        # State names can look like "Kuching (Sarawak)"
        # Split them so the city is the title and the state is the small label
        if "(" in state_name and state_name.endswith(")"):
            city_part, state_part = state_name[:-1].split("(", 1)
            self.city_lbl.config(text=city_part.strip())
            self.region_lbl.config(text=state_part.strip())
        else:
            self.city_lbl.config(text=state_name)
            self.region_lbl.config(text="Malaysia")

        self.scene.set_weather(kind, night)
        self.icon.set_kind(kind, night)

        if temp is not None:
            self.temp_lbl.config(text=f"{temp}°C")
        else:
            self.temp_lbl.config(text="--°C")

        self.cond_lbl.config(text=label)
        self.score_lbl.config(text=str(int(score)))
        self.rain_lbl.config(text=f"{rain}%")
        self.comfort_desc.config(text=comfort_text)


class CityComparePage(BasePage):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.comparer = CityCompare(app.weather_data)
        self.planner = TodaysPlanner(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

    def display_widgets(self):
        self.header = make_banner(
            self,
            "City Compare",
            "Pick two Malaysian cities to compare their weather, rain chances, and outdoor comfort.",
            back_command=self.go_back
        )

        content = self.make_content()

        self.build_control_bar(content)
        self.build_city_cards(content)
        self.build_summary(content)

        # Show a comparison as soon as the page opens
        self.on_click()

    # Horizontal control bar: [First city] [Second city] [Compare] [⇄]
    def build_control_bar(self, content):
        self.button_frame = make_card(content)
        self.button_frame.pack(fill="x", pady=(0, 16))

        bar = tk.Frame(self.button_frame, bg=Theme.CARD)
        bar.pack(fill="x", padx=18, pady=14)
        bar.grid_columnconfigure(0, weight=2)
        bar.grid_columnconfigure(1, weight=2)
        bar.grid_columnconfigure(2, weight=0)
        bar.grid_columnconfigure(3, weight=0)

        first_label = make_field_label(bar, "First city")
        first_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))
        second_label = make_field_label(bar, "Second city")
        second_label.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=(0, 5))

        first_default = default_state(self.states)
        self.state_a = tk.StringVar(value=first_default)
        self.menu_a = make_dropdown(bar, self.state_a, self.states)
        self.menu_a.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        # The second city starts as the first state that is different from the first city
        second_default = first_default
        for state in self.states:
            if state != first_default:
                second_default = state
                break

        self.state_b = tk.StringVar(value=second_default)
        self.menu_b = make_dropdown(bar, self.state_b, self.states)
        self.menu_b.grid(row=1, column=1, sticky="ew", padx=(0, 12))

        self.compare_button = FlatButton(bar, "Compare", self.on_click, padx=26, pady=9)
        self.compare_button.grid(row=1, column=2, sticky="ew", padx=(0, 8))

        self.swap_button = FlatButton(bar, "⇄", self.swap_cities, style="icon", padx=11, pady=9)
        self.swap_button.grid(row=1, column=3, sticky="ew")

    # The two side-by-side cards
    def build_city_cards(self, content):
        cards_grid = tk.Frame(content, bg=current_ambient())
        cards_grid.pack(fill="both", expand=True)
        cards_grid.grid_columnconfigure(0, weight=1, uniform="compare_cards")
        cards_grid.grid_columnconfigure(1, weight=1, uniform="compare_cards")
        register_surface(cards_grid)

        self.card_a = CityCompareCard(cards_grid, "First city", highlight=True)
        self.card_a.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_b = CityCompareCard(cards_grid, "Second city", highlight=False)
        self.card_b.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    # The text summary at the bottom (written by logic.py)
    def build_summary(self, content):
        self.summary_card = make_card(content)
        self.summary_card.pack(fill="x", pady=(14, 0))

        self.result_label = tk.Label(
            self.summary_card, text="", font=font(10),
            bg=Theme.CARD, fg=Theme.SUBTEXT, anchor="w", justify="left",
            padx=18, pady=12
        )
        self.result_label.pack(fill="x")

    def swap_cities(self):
        city_a = self.state_a.get()
        city_b = self.state_b.get()
        self.state_a.set(city_b)
        self.state_b.set(city_a)
        self.on_click()

    def update_card(self, card, state):
        """Fills one card. The score comes from the same CityCompare logic
        as the text summary, so the numbers on screen always match."""
        entry, _ = get_entry_for_state(self.app, state)
        data = self.app.weather_data.get_city_data(state)

        if data is None:
            card.update_data(state, entry, 0, "No weather data found.")
            return

        score = self.comparer.calculate_comfort_score(data)
        comfort_text = self.planner.describe_comfort(score)
        card.update_data(state, entry, score, comfort_text)

    def on_click(self):
        city_a = self.state_a.get()
        city_b = self.state_b.get()

        # The page tint follows the first city
        apply_weather(self.app, city_a)

        self.update_card(self.card_a, city_a)
        self.update_card(self.card_b, city_b)

        text = self.comparer.create_comparison_text(city_a, city_b)
        self.result_label.config(text=text)
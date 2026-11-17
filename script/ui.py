# UI LAYER
# This file only builds the user interface
# All the calculations are done by the classes in logic.py.
# All the data is read through the WeatherData class in data.py.

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


def font(size=11, weight="normal"):
    """Picks the cleanest sans-serif font available."""
    global _font_family
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
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    mixed = [int(x + (y - x) * amount) for x, y in zip(a, b)]
    return "#%02x%02x%02x" % tuple(mixed)


def default_state(states):
    """Returns 'Sarawak' (or an entry containing 'Sarawak') if available, else the first state."""
    for s in states:
        if "sarawak" in s.lower():
            return s
    return states[0] if states else ""


def describe_weather(entry):
    """Turns one hourly entry into (kind, is_night, label, temperature, rain_pct)."""
    hour = datetime.now().hour
    is_night = hour < 6 or hour >= 19
    kind, temp, rain = "clear", None, 0
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
        pass

    labels = {
        "storm": "Thunderstorm",
        "rain": "Light Rain Showers",
        "cloudy": "Misty Morning Clouds" if 5 <= hour <= 9 else "Partly Cloudy",
        "hot": "Hot & Sunny",
        "clear": "Clear Night" if is_night else "Clear & Sunny",
    }
    return kind, is_night, labels[kind], temp, rain


# ==========================================
# GLOBAL WEATHER SYNC
# ==========================================
class Mood:
    app = None
    state = None
    entry = None
    planner = None
    icons = []
    themed_surfaces = []


def register_surface(widget):
    Mood.themed_surfaces.append(widget)


def current_ambient():
    kind, night, _, _, _ = describe_weather(Mood.entry)
    if night and kind in ("clear", "cloudy"):
        return AMBIENT_BG["night"]
    return AMBIENT_BG.get(kind, Theme.BG)


def get_entry_for_state(app, state):
    """Fetches the weather entry and comfort score for a state at the current hour."""
    try:
        if Mood.planner is None:
            Mood.planner = TodaysPlanner(app.weather_data)
        hours = Mood.planner.score_hours(state)
        hr = datetime.now().hour
        best = min(hours, key=lambda h: abs(h["entry"]["hour"] - hr))
        return best["entry"], best["score"]
    except Exception:
        return None, 80


def apply_weather(app, state):
    """Updates global weather context and refreshes subtle page tints and icons."""
    Mood.app, Mood.state = app, state
    Mood.entry, _ = get_entry_for_state(app, state)

    bg = current_ambient()
    for widget in list(Mood.themed_surfaces):
        try:
            widget.config(bg=bg)
        except tk.TclError:
            Mood.themed_surfaces.remove(widget)

    for icon in list(Mood.icons):
        try:
            icon.set_weather()
        except tk.TclError:
            Mood.icons.remove(icon)


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
            self.after(50 if self.winfo_ismapped() else 300, self.animate)
        except tk.TclError:
            pass

    def draw(self):
        self.delete("all")
        s = self.size
        cx, cy = s / 2, s / 2

        if self.kind in ("clear", "hot") and not self.night:
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
            bob = math.sin(self.t * 0.08) * 1.5
            r = s * 0.24
            self.create_oval(cx - r, cy - r + bob, cx + r, cy + r + bob,
                             fill="#FACC15", outline="")
            self.create_oval(cx - r * 0.3, cy - r * 1.1 + bob,
                             cx + r * 1.2, cy + r * 0.6 + bob,
                             fill=self.cget("bg"), outline="")
        else:
            # Sun peeking behind cloud
            if self.kind == "cloudy" and not self.night:
                pulse = math.sin(self.t * 0.08) * 1.2
                self.create_oval(
                    cx + s * 0.02 - pulse, cy - s * 0.24 - pulse,
                    cx + s * 0.28 + pulse, cy + s * 0.02 + pulse,
                    fill="#FBBF24", outline=""
                )

            drift = math.sin(self.t * 0.07) * (s * 0.035)
            y_off = -s * 0.05 if self.kind in ("rain", "storm") else s * 0.03
            cloud_fill = "#FFFFFF" if self.kind == "cloudy" else "#94A3B8"
            cloud_outline = "#CBD5E1" if self.kind == "cloudy" else "#64748B"

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

            if self.kind in ("rain", "storm"):
                for i, dx in enumerate((-0.12, 0.0, 0.12)):
                    drop_y = (self.t * 2.0 + i * 7) % (s * 0.26)
                    x = cx + dx * s
                    y = cy + s * 0.16 + drop_y
                    self.create_line(x, y, x - 2, y + 5, fill="#2563EB", width=2, capstyle="round")

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
        if (kind, night) != (self.kind, self.night):
            self.kind = kind
            self.night = night
            self.build_particles()

    def on_resize(self, event):
        self.w = max(200, event.width)
        self.build_particles()

    def build_particles(self):
        count = {"clear": 3, "hot": 2, "cloudy": 6, "rain": 6, "storm": 7}.get(self.kind, 4)
        self.clouds = [
            [random.random(), random.uniform(0.10, 0.42),
             random.uniform(0.75, 1.3), random.uniform(0.15, 0.45)]
            for _ in range(count)
        ]
        drop_count = {"rain": 28, "storm": 55}.get(self.kind, 0)
        self.drops = [
            [random.uniform(0, self.w), random.uniform(0, self.h),
             random.uniform(6, 10), random.uniform(7, 11)]
            for _ in range(drop_count)
        ]

    def tick(self):
        try:
            if self.winfo_ismapped():
                self.t += 1
                self.draw_scene()
            self.after(40 if self.winfo_ismapped() else 300, self.tick)
        except tk.TclError:
            pass

    def draw_scene(self):
        self.delete("all")
        w, h = self.w, self.h

        # 1. Sky gradient
        top, bottom = SKY.get(self.kind, SKY["clear"])
        if self.night:
            top = blend(top, NIGHT, 0.72)
            bottom = blend(bottom, NIGHT, 0.62)

        steps = 16
        for i in range(steps):
            y0 = i * h / steps
            y1 = (i + 1) * h / steps + 1
            self.create_rectangle(0, y0, w, y1,
                                  fill=blend(top, bottom, i / (steps - 1)), outline="")

        # Lightning flash
        if self.kind == "storm" and self.flash == 0 and random.random() < 0.01:
            self.flash = 4
        if self.flash > 0:
            self.create_rectangle(0, 0, w, h, fill="#FFFFFF", stipple="gray25", outline="")
            self.flash -= 1

        # 2. Sun or Moon
        if self.kind in ("clear", "hot", "cloudy"):
            cx, cy = w * 0.80, h * 0.24
            if self.night:
                self.create_oval(cx - 12, cy - 12, cx + 12, cy + 12, fill="#FEF08A", outline="")
                self.create_oval(cx - 5, cy - 15, cx + 17, cy + 7, fill=top, outline="")
            else:
                pulse = math.sin(self.t * 0.08) * 2
                self.create_oval(cx - 18 - pulse, cy - 18 - pulse,
                                 cx + 18 + pulse, cy + 18 + pulse,
                                 fill="#FDE047", outline="")

        # 3. Drifting puffy clouds
        c_color = CLOUD.get(self.kind, "#FFFFFF")
        if self.night:
            c_color = blend(c_color, "#1E293B", 0.5)
        for c in self.clouds:
            x = (c[0] * w + c[3] * self.t) % (w + 180) - 90
            y = c[1] * h
            s = c[2]
            for dx, dy, r in ((-18, 4, 11), (-4, -3, 14), (12, 2, 12), (24, 5, 9)):
                self.create_oval(x + (dx - r) * s, y + (dy - r) * s,
                                 x + (dx + r) * s, y + (dy + r) * s,
                                 fill=c_color, outline="")

        # 4. Coastal hills & bay
        horizon = h * 0.62
        water_color = "#1E3A8A" if self.night else (
            "#2563EB" if self.kind in ("clear", "hot") else "#475569"
        )
        self.create_rectangle(0, horizon, w, h, fill=water_color, outline="")
        ripple_color = blend(water_color, "#FFFFFF", 0.25)
        for i in range(6):
            rx = ((i * 85 + self.t * 0.6) % (w + 40)) - 20
            ry = horizon + 10 + (i % 3) * 11
            self.create_line(rx, ry, rx + 26, ry, fill=ripple_color, width=1)

        hill_dark = "#0F291E" if self.night else "#1E4620"
        hill_mid = "#163828" if self.night else "#2D5A27"
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
            fill="#1E293B" if self.night else "#334155", outline=""
        )
        building_colors = ("#F8FAFC", "#FDE68A", "#E2E8F0", "#FCA5A5")
        for bx in range(8, int(w * 0.44), 14):
            by = horizon - 2 + (bx / (w * 0.45)) * 12
            bh = 5 + (bx % 7)
            col = "#FACC15" if (self.night and bx % 3 == 0) else building_colors[bx % 4]
            self.create_rectangle(bx, by - bh, bx + 8, by, fill=col, outline="")

        self.create_line(w * 0.52, horizon + 8, w, horizon + 5,
                         fill="#CBD5E1" if not self.night else "#475569", width=2)

        # 5. Rain streaks
        if self.drops:
            r_col = "#E0F2FE" if not self.night else "#94A3B8"
            for d in self.drops:
                d[1] += d[2]
                d[0] -= d[2] * 0.2
                if d[1] > h:
                    d[1], d[0] = -d[3], random.uniform(0, w + 30)
                self.create_line(d[0], d[1], d[0] - 2, d[1] + d[3], fill=r_col, width=1)


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
        super().__init__(
            parent,
            text=text,
            font=font(size, "bold" if style == "primary" else "normal"),
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
        self.bind("<Enter>", lambda e: self.config(bg=self.colors["hover"]))
        self.bind("<Leave>", lambda e: self.config(bg=self.colors["bg"]))
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Return>", lambda e: self.command())
        self.bind("<space>", lambda e: self.command())


class MenuCard(tk.Frame):
    """Clean white navigation card for HomePage."""

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

        self.surfaces = [self, self.body, self.title_label,
                         self.desc_label, self.arrow]

        for widget in self.surfaces + [self.icon]:
            widget.config(cursor="hand2")
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)
            widget.bind("<Button-1>", lambda e: self.command())

    def on_enter(self, event):
        self.config(highlightbackground=Theme.PRIMARY_BORDER)
        for widget in self.surfaces:
            widget.config(bg=Theme.PRIMARY_SOFT)
        self.arrow.config(fg=Theme.PRIMARY)

    def on_leave(self, event):
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
    """Clean light editorial header."""
    bg = current_ambient()
    header = tk.Frame(parent, bg=bg)
    header.pack(fill="x", padx=28, pady=(20, 12))
    register_surface(header)

    if back_command is not None:
        back_lbl = tk.Label(
            header, text="← Back to home page", font=font(10),
            bg=bg, fg=Theme.SUBTEXT, cursor="hand2", anchor="w"
        )
        back_lbl.pack(anchor="w", pady=(0, 6))
        back_lbl.bind("<Button-1>", lambda e: back_command())
        back_lbl.bind("<Enter>", lambda e: back_lbl.config(fg=Theme.PRIMARY))
        back_lbl.bind("<Leave>", lambda e: back_lbl.config(fg=Theme.SUBTEXT))
        register_surface(back_lbl)

    title_lbl = tk.Label(
        header, text=title, font=font(22, "bold"),
        bg=bg, fg=Theme.TEXT, anchor="w"
    )
    title_lbl.pack(anchor="w")
    register_surface(title_lbl)

    if subtitle:
        sub_lbl = tk.Label(
            header, text=subtitle, font=font(10),
            bg=bg, fg=Theme.MUTED, anchor="w"
        )
        sub_lbl.pack(anchor="w", pady=(3, 0))
        register_surface(sub_lbl)

    return header, None, header


def make_card(parent, highlight=False):
    return tk.Frame(
        parent, bg=Theme.CARD,
        highlightthickness=1,
        highlightbackground=Theme.PRIMARY_BORDER if highlight else Theme.BORDER
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
        tk.Frame(legend, bg=color, width=10, height=10).pack(side="left", padx=(10, 4))
        lbl = tk.Label(legend, text=text, font=font(9, "bold"), bg=bg, fg=Theme.MUTED)
        lbl.pack(side="left")
        register_surface(lbl)
    return legend


def make_row(parent, cells, colors, weights):
    background, accent = colors
    row = tk.Frame(parent, bg=background)
    row.pack(fill="x", pady=2)

    tk.Frame(row, bg=accent, width=4).pack(side="left", fill="y")

    inner = tk.Frame(row, bg=background)
    inner.pack(side="left", fill="x", expand=True, padx=14, pady=7)

    for column, text in enumerate(cells):
        inner.grid_columnconfigure(column, weight=weights[column], uniform="cols")
        is_edge = column == 0 or column == len(cells) - 1
        tk.Label(
            inner, text=text,
            font=font(10, "bold" if is_edge else "normal"),
            bg=background, fg=Theme.TEXT,
            anchor="e" if column == len(cells) - 1 else "w"
        ).grid(row=0, column=column, sticky="ew")


# ==========================================
# PAGES
# ==========================================
class BasePage(tk.Frame):
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

        box.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))

        def _on_mousewheel(event):
            if canvas.winfo_ismapped():
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
                else:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(_event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_wheel(_event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        wrapper.bind("<Enter>", _bind_wheel)
        wrapper.bind("<Leave>", _unbind_wheel)

        inner_box = tk.Frame(box, bg=bg)
        inner_box.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        register_surface(inner_box)
        return inner_box

    def build_state_selector(self, parent, button_text, command):
        """Horizontal control bar."""
        bar = make_card(parent)
        bar.pack(fill="x")

        inner = tk.Frame(bar, bg=Theme.CARD)
        inner.pack(fill="x", padx=18, pady=14)
        inner.grid_columnconfigure(0, weight=3)
        inner.grid_columnconfigure(1, weight=0)

        make_field_label(inner, "Select city / state").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        self.selected_state = tk.StringVar(value=default_state(self.states))
        self.selected_state.trace_add(
            "write",
            lambda *args: apply_weather(self.app, self.selected_state.get())
        )
        apply_weather(self.app, self.selected_state.get())

        menu = make_dropdown(inner, self.selected_state, self.states)
        menu.grid(row=1, column=0, sticky="ew", padx=(0, 12))

        button = FlatButton(inner, button_text, command, padx=24, pady=9)
        button.grid(row=1, column=1, sticky="e")
        return menu, button

    def go_back(self):
        self.app.show_page("home")


class HomePage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.display_widgets()

    def display_widgets(self):
        self.banner, _, self.header = make_banner(
            self,
            "Weather Planner",
            "Pick a tool to check forecasts, comfort scores, and outdoor safety."
        )

        self.button_frame = self.make_content()

        self.todays_plan = MenuCard(
            self.button_frame,
            "Today's Plan",
            "Hour-by-hour comfort outlook for your state",
            self.open_todays_plan,
            icon_kind="clear"
        )
        self.todays_plan.pack(fill="x", pady=5)

        self.activity_advisor = MenuCard(
            self.button_frame,
            "Activity Advisor",
            "Advice for what to do in the current weather",
            self.open_activity_advisor,
            icon_kind="cloudy"
        )
        self.activity_advisor.pack(fill="x", pady=5)

        self.hydration_safety = MenuCard(
            self.button_frame,
            "Hydration & Safety",
            "Heat risk and how much water you need",
            self.open_hydration_safety,
            icon_kind="hot"
        )
        self.hydration_safety.pack(fill="x", pady=5)

        self.city_compare = MenuCard(
            self.button_frame,
            "City Compare",
            "Compare two places side by side",
            self.open_city_compare,
            icon_kind="rain"
        )
        self.city_compare.pack(fill="x", pady=5)

        self.exit = FlatButton(
            self.button_frame, "Exit", self.app.window.destroy,
            style="secondary", size=10, pady=8
        )
        self.exit.pack(fill="x", pady=(14, 0))

        apply_weather(self.app, default_state(self.app.weather_data.get_states()))

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
        self.banner, self.back_button, self.header = make_banner(
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
        for widget in self.hourly_frame.winfo_children():
            widget.destroy()

        make_legend(self.hourly_frame, [
            (Theme.GOOD[1], "Good"),
            (Theme.MODERATE[1], "Moderate"),
            (Theme.DANGER[1], "Poor"),
        ]).pack(pady=(0, 6))

        for item in self.planner.score_hours(state):
            entry = item["entry"]
            score = item["score"]

            make_row(
                self.hourly_frame,
                [
                    f"{entry['hour']:02d}:00",
                    f"{entry['temp_c']}°C",
                    f"Rain {entry['rain_chance_pct']}%",
                    f"Score {score}/100",
                ],
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
        self.banner, self.back_button, self.header = make_banner(
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
        self.banner, self.back_button, self.header = make_banner(
            self,
            "Hydration & Safety",
            "Stay safe and well hydrated in the heat.",
            back_command=self.go_back
        )

        content = self.make_content()

        self.state_menu, self.check_button = self.build_state_selector(
            content, "Check Safety", self.on_click
        )

        card, self.result_label = make_result_card(
            content, "Choose a location and press Check Safety"
        )
        card.pack(fill="x", pady=(14, 10))

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

        make_legend(self.hourly_frame, [
            (Theme.GOOD[1], "Low"),
            (Theme.MODERATE[1], "Moderate"),
            (Theme.HIGH[1], "High"),
            (Theme.DANGER[1], "Danger"),
        ]).pack(pady=(0, 6))

        for result in self.calculator.get_hourly_results(state):
            make_row(
                self.hourly_frame,
                [
                    f"{result['hour']:02d}:00",
                    f"{result['temperature']}°C (feels {result['feels_like']}°C)",
                    f"{result['level']}",
                    f"{result['water_ml']} ml/h",
                ],
                self.get_level_colors(result["level"]),
                weights=[1, 3, 2, 2]
            )

    def on_click(self):
        state = self.selected_state.get()
        summary, level = self.calculator.create_summary(state)
        bg = self.get_level_colors(level)[0]
        self.result_label.config(text=summary, bg=bg)
        self.result_label.master.config(bg=bg)
        for child in self.result_label.master.winfo_children():
            child.config(bg=bg)
        self.display_hourly_risk(state)


# ==========================================
# CITY COMPARE PAGE
# ==========================================
class CityCompareCard(tk.Frame):
    """Side-by-side comparison card."""

    def __init__(self, parent, role_label, highlight=False):
        super().__init__(
            parent,
            bg=Theme.CARD,
            highlightthickness=1,
            highlightbackground=Theme.PRIMARY_BORDER if highlight else Theme.BORDER
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

        # City / State Title
        self.city_lbl = tk.Label(
            inner, text="—", font=font(16, "bold"),
            bg=Theme.CARD, fg=Theme.TEXT, anchor="w"
        )
        self.city_lbl.pack(fill="x", pady=(2, 12))

        # Scenic animated weather landscape banner
        self.scene = WeatherSceneBanner(inner, height=118)
        self.scene.pack(fill="x", pady=(0, 14))

        # Middle metrics row: [Icon + Temp + Condition] | [Comfort score 94 / 100]
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

        # Comfort score on the right
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

        # Subtle horizontal divider
        tk.Frame(inner, bg=Theme.BORDER, height=1).pack(fill="x", pady=(0, 12))

        # Comfort summary text
        self.comfort_desc = tk.Label(
            inner, text="Select cities and click Compare", font=font(10),
            bg=Theme.CARD, fg=Theme.SUBTEXT, anchor="w"
        )
        self.comfort_desc.pack(fill="x", pady=(0, 12))

        # Bottom row: Rain chance on left, percentage on right
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

    def update_data(self, state_name, entry, score):
        kind, night, label, temp, rain = describe_weather(entry)

        if "(" in state_name and state_name.endswith(")"):
            city_part, state_part = state_name[:-1].split("(", 1)
            self.city_lbl.config(text=city_part.strip())
            self.region_lbl.config(text=state_part.strip())
        else:
            self.city_lbl.config(text=state_name)
            self.region_lbl.config(text="Malaysia")

        self.scene.set_weather(kind, night)
        self.icon.set_kind(kind, night)

        self.temp_lbl.config(text=f"{temp}°C" if temp is not None else "--°C")
        self.cond_lbl.config(text=label)
        self.score_lbl.config(text=str(int(score)))
        self.rain_lbl.config(text=f"{rain}%")

        if score >= 80:
            desc = "Very comfortable for being outside"
        elif score >= 60:
            desc = "Pleasant conditions for outdoor plans"
        elif score >= 40:
            desc = "Moderate comfort — check rain or heat"
        else:
            desc = "Uncomfortable outdoors — indoor plans advised"
        self.comfort_desc.config(text=desc)


class CityComparePage(BasePage):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.comparer = CityCompare(app.weather_data)
        self.states = app.weather_data.get_states()
        self.display_widgets()

    def display_widgets(self):
        # Clean light header
        self.banner, self.back_button, self.header = make_banner(
            self,
            "City Compare",
            "Pick two Malaysian cities to compare their weather, rain chances, and outdoor comfort.",
            back_command=self.go_back
        )

        content = self.make_content()

        # Horizontal filter bar: [First city] [Second city] [Compare] [⇄]
        self.button_frame = make_card(content)
        self.button_frame.pack(fill="x", pady=(0, 16))

        bar = tk.Frame(self.button_frame, bg=Theme.CARD)
        bar.pack(fill="x", padx=18, pady=14)
        bar.grid_columnconfigure(0, weight=2)
        bar.grid_columnconfigure(1, weight=2)
        bar.grid_columnconfigure(2, weight=0)
        bar.grid_columnconfigure(3, weight=0)

        make_field_label(bar, "First city").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))
        make_field_label(bar, "Second city").grid(row=0, column=1, sticky="w", padx=(0, 10), pady=(0, 5))

        first_default = default_state(self.states)
        self.state_a = tk.StringVar(value=first_default)
        self.menu_a = make_dropdown(bar, self.state_a, self.states)
        self.menu_a.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        second_default = next((s for s in self.states if s != first_default), first_default)
        self.state_b = tk.StringVar(value=second_default)
        self.menu_b = make_dropdown(bar, self.state_b, self.states)
        self.menu_b.grid(row=1, column=1, sticky="ew", padx=(0, 12))

        self.compare_button = FlatButton(bar, "Compare", self.on_click, padx=26, pady=9)
        self.compare_button.grid(row=1, column=2, sticky="ew", padx=(0, 8))

        self.swap_button = FlatButton(bar, "⇄", self.swap_cities, style="icon", padx=11, pady=9)
        self.swap_button.grid(row=1, column=3, sticky="ew")

        # Side-by-side comparison cards container
        cards_grid = tk.Frame(content, bg=current_ambient())
        cards_grid.pack(fill="both", expand=True)
        cards_grid.grid_columnconfigure(0, weight=1, uniform="compare_cards")
        cards_grid.grid_columnconfigure(1, weight=1, uniform="compare_cards")
        register_surface(cards_grid)

        self.card_a = CityCompareCard(cards_grid, "First city", highlight=True)
        self.card_a.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_b = CityCompareCard(cards_grid, "Second city", highlight=False)
        self.card_b.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Subtle text summary pill at bottom (retains logic.py create_comparison_text)
        self.summary_card = make_card(content)
        self.summary_card.pack(fill="x", pady=(14, 0))
        self.result_label = tk.Label(
            self.summary_card, text="", font=font(10),
            bg=Theme.CARD, fg=Theme.SUBTEXT, anchor="w", justify="left",
            padx=18, pady=12
        )
        self.result_label.pack(fill="x")

        # Populate immediately on open
        self.on_click()

    def swap_cities(self):
        a, b = self.state_a.get(), self.state_b.get()
        self.state_a.set(b)
        self.state_b.set(a)
        self.on_click()

    def on_click(self):
        city_a = self.state_a.get()
        city_b = self.state_b.get()

        apply_weather(self.app, city_a)

        entry_a, score_a = get_entry_for_state(self.app, city_a)
        entry_b, score_b = get_entry_for_state(self.app, city_b)

        self.card_a.update_data(city_a, entry_a, score_a)
        self.card_b.update_data(city_b, entry_b, score_b)

        text = self.comparer.create_comparison_text(city_a, city_b)
        self.result_label.config(text=text)
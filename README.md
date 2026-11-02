# Weather App Planner 

This Weather Planner App is a Python GUI app that fetches weather forecasts to help plan your day around heat,
with hourly activity planning, safe-window advice, hydration guidance, and city comparison

### Pages:
1. Homepage
2. Activity Advisor
3. City Compare
4. Hydration Safety
5. Todays Plan

#

### Features:

1. **Todays Plan Page**: 
Input city -> Fetch forecast -> Score each hour ->
Score each hour -> Show Planner

2. **Activity Advisor**: 
Input city -> Fetch forecast
-> Apply limit -> Safe Window -> Show advice

3. **Hydration And Safety**:
Input city -> Fetch forecast -> Find peak heat ->
Set Advice -> Show water goal

4. **City Compare**:
Add city -> Fetch forecast -> Score each city ->
Rank cities -> Show comparison

#

### Weather Database:

(NOTE: the database is hardcoded instead of fetching actual up-to-date weather data)

The weather database is kept in a JSON file inside `./database`.

Since weather database will only display weather forecast from the 6th hour to 20th hour,
each program will import the datetime module to get the current hour and fetch the weather forecast based on that hour.

#

### What every Python file must have (not including homepage.py):

```
# -- Import all needed libraries --
import tkinter as tk
import ... 

# -- Class name (use the page name. for city_compare.py the class name is CityComparePage) --

class PageName(tk.Frame):
    # Page Initialization
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.app = app
        self.load_data()
        self.display_widgets()

    # Display Widgets
    def display_widgets(self):
        ...

    # Gets the weather of one place for the current hour
    def get_city_data(self, state):
        place = self.data[state]

        # The json only has hours 6 to 20, so keep the hour inside that range
        hour = datetime.now().hour
        if hour < 6:
            hour = 6
        if hour > 20:
            hour = 20

        for entry in place["hours"]:
            if entry["hour"] == hour:
                return {
                    "name": place["city"],
                    "temperature": entry["temp_c"],
                    "humidity": entry["humidity_pct"],
                    "uv_index": entry["uv_index"],
                    "rain_chance": entry["rain_chance_pct"],
                }

    # --- Here you can put the unique functions that belongs to each page ---

    # Adds event listener to the buttons
    def on_click(self):
        ...

    # Goes back to the home page
    def go_back(self):
        self.app.show_page("home")
```

#### Notes:
1. Each page must have exactly one class. and they must be the name of the filename/page name. For example, in a `city_compare.py` file the class name should be `CityComparePage`.
2. Each program have the same `__init__()`, `get_city_data()` and `go_back()` function (or methods in a class sense), while `display_widgets()` and `on_click()` are unique to each page. They all must be in the same class
#

### How to run:

1. Open `./script/homepage.py` (Entry Point)
2. Run `python homepage.py` in the terminal 

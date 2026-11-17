# Weather Planner App

This Weather Planner App is a Python GUI app built with **CustomTkinter** that reads weather forecasts to help plan your day around heat, featuring hourly activity planning, activity advice, hydration guidance, and city comparison.

Github Repository Link: https://github.com/ariq-isaac/weather-app-planner

## Pages

1. Homepage
2. Today's Plan
3. Activity Advisor
4. Hydration & Safety
5. City Compare

---

## Features

1. **Today's Plan**:
Choose state -> Read forecast -> Score each hour ->
Show best hour and scrollable color-coded hourly scores.

2. **Activity Advisor**:
Choose state -> Read current hour's weather ->
Check rain, UV and heat -> Show advice and suggested activities.

3. **Hydration & Safety**:
Choose state -> Read current hour's weather -> Calculate feels-like temperature ->
Set risk level -> Show water goal and scrollable hourly risk breakdown.

4. **City Compare**:
Choose two states -> Read current hour's weather -> Score each city ->
Show comparison and recommendation.

---

## Weather Database

*(NOTE: the database is hardcoded instead of fetching actual up-to-date weather data)*

The weather database is kept in a JSON file inside `./database`.

Since the weather database only has forecasts from the 6th hour to the 20th hour,
`data.py` uses the datetime module to get the current hour and reads the forecast for that hour.
If the current hour is before 6 or after 20, the closest hour (6 or 20) is used instead.

---

## What every Python file does

1. `data.py`: Loads the weather database from `./database/malaysia_weather.json` and looks up the weather for a state (including the current hour).
2. `logic.py`: Handles all the business logic, calculations, and color-formatting utilities. These are intentionally separated from the User Interface code.
3. `ui.py`: Builds the modern CustomTkinter User Interface for every app page inside clean card frames.
4. `homepage.py`: The entry point of the program. It sets up CustomTkinter appearance themes, initializes the main window, loads the weather data once, and manages page navigation.

---

### Modules imported
1. `customtkinter` : To create the modern polished user interface
2. `json` : To read the weather database
3. `os` : Builds the path to the JSON file
4. `datetime` : Gets the current hour

### How to run:

1. Install customtkinter: `pip install customtkinter`
2. Run `python homepage.py` in your terminal (Make sure you are inside ./script/ folder)

# Weather Planner App
 
This Weather Planner App is a Python GUI app that reads weather forecasts to help plan your day around heat,
with hourly activity planning, activity advice, hydration guidance, and city comparison.
 
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
Show best hour and hourly scores
2. **Activity Advisor**:
Choose state -> Read current hour's weather ->
Check rain, UV and heat -> Show advice and suggested activities
3. **Hydration & Safety**:
Choose state -> Read current hour's weather -> Calculate feels-like temperature ->
Set risk level -> Show water goal and hourly risk
4. **City Compare**:
Choose two states -> Read current hour's weather -> Score each city ->
Show comparison and recommendation
---
 
## Weather Database
 
(NOTE: the database is hardcoded instead of fetching actual up-to-date weather data)
 
The weather database is kept in a JSON file inside `./database`.
 
Since the weather database only has forecasts from the 6th hour to the 20th hour,
`data.py` uses the datetime module to get the current hour and reads the forecast for that hour.
If the current hour is before 6 or after 20, the closest hour (6 or 20) is used instead.
 
---
 
## What every Python file does
 
1. `data.py`: Loads the weather database from `./database/malaysia_weather.json` and looks up the weather for a state (including the current hour).
2. `logic.py`: Handles all the business logic and calculations. These are intentionally separated from the User Interface code to improve design. The pages in `ui.py` create the logic classes and use them.
3. `ui.py`: Creates the User Interface for every tkinter page (including the home page). The main window comes from `homepage.py`.
4. `homepage.py`: The entry point of the program. It creates the main window, loads the weather data once, creates all the pages from `ui.py`, and handles switching between pages.
---
 
### Modules imported
1. `tkinter` : To create the user interface (`tkinter.font` is used to pick the font)
2. `json` : To read the weather database
3. `os` : Builds the path to the JSON file
4. `datetime` : Gets the current hour
5. `math` : Calculates the movement of the animated weather icons and scenes
6. `random` : Gives the animated clouds, rain drops and icons random positions and speeds
### How to run:
 
1. Open `./script/homepage.py` (Entry Point)
2. Run `python homepage.py` in the terminal
 

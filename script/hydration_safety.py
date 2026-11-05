


import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date, datetime

# ==================================
# DATABASE
# ==================================

connection = sqlite3.connect("hydration.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    daily_goal INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS water_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    log_date TEXT NOT NULL,
    log_time TEXT NOT NULL
)
""")

connection.commit()

# ==================================
# MAIN WINDOW
# ==================================

root = tk.Tk()
root.title("Hydration Safety")
root.geometry("500x650")
root.resizable(False, False)

current_user = None
daily_goal = 2000

# ==================================
# DATABASE FUNCTIONS
# ==================================

def get_total():
    if current_user is None:
        return 0

    cursor.execute("""
    SELECT SUM(amount) FROM water_logs
    WHERE user_id = ? AND log_date = ?
    """, (current_user, str(date.today())))

    result = cursor.fetchone()[0]

    return result if result else 0


def update_display():
    total = get_total()

    total_label.config(
        text=f"{total} mL"
    )

    remaining = max(0, daily_goal - total)

    remaining_label.config(
        text=f"Remaining: {remaining} mL"
    )

    percentage = min(
        100, (total / daily_goal) * 100
    )

    progress["value"] = percentage

    percentage_label.config(
        text=f"{percentage:.1f}% of daily goal"
    )

    update_history()


def update_history():
    history_list.delete(0, tk.END)

    if current_user is None:
        return

    cursor.execute("""
    SELECT amount, log_time
    FROM water_logs
    WHERE user_id = ? AND log_date = ?
    ORDER BY id DESC
    """, (current_user, str(date.today())))

    records = cursor.fetchall()

    for amount, log_time in records:
        history_list.insert(
            tk.END,
            f"{log_time} - {amount} mL"
        )


# ==================================
# CREATE USER
# ==================================

def create_user():

    global current_user, daily_goal

    name = name_entry.get().strip()

    try:
        goal = int(goal_entry.get())
    except ValueError:
        messagebox.showerror(
            "Error",
            "Please enter a valid daily goal."
        )
        return

    if not name:
        messagebox.showerror(
            "Error",
            "Please enter your name."
        )
        return

    if not 250 <= goal <= 10000:
        messagebox.showerror(
            "Error",
            "Goal must be between 250 and 10000 mL."
        )
        return

    cursor.execute("""
    INSERT INTO users (name, daily_goal)
    VALUES (?, ?)
    """, (name, goal))

    connection.commit()

    current_user = cursor.lastrowid
    daily_goal = goal

    profile_label.config(
        text=f"User: {name}"
    )

    name_entry.delete(0, tk.END)

    update_display()

    messagebox.showinfo(
        "Success",
        "Profile created successfully!"
    )


# ==================================
# ADD WATER INTAKE
# ==================================

def add_water():

    if current_user is None:
        messagebox.showwarning(
            "Warning",
            "Please create a profile first."
        )
        return

    try:
        amount = int(amount_entry.get())
    except ValueError:
        messagebox.showerror(
            "Error",
            "Please enter a valid amount."
        )
        return

    if not 1 <= amount <= 5000:
        messagebox.showerror(
            "Error",
            "Enter an amount between 1 and 5000 mL."
        )
        return

    current_total = get_total()

    if amount >= 1000:
        messagebox.showwarning(
            "Hydration Safety",
            "This is a large single intake entry. "
            "Avoid drinking large amounts quickly."
        )

    cursor.execute("""
    INSERT INTO water_logs
    (user_id, amount, log_date, log_time)
    VALUES (?, ?, ?, ?)
    """, (
        current_user,
        amount,
        str(date.today()),
        datetime.now().strftime("%H:%M:%S")
    ))

    connection.commit()

    amount_entry.delete(0, tk.END)

    update_display()

    new_total = current_total + amount

    if new_total >= daily_goal:
        messagebox.showinfo(
            "Daily Goal",
            "Your tracking goal has been reached. "
            "Do not force yourself to drink more."
        )


# ==================================
# MAIN INTERFACE
# ==================================

title_label = tk.Label(
    root,
    text="Hydration Safety",
    font=("Arial", 22, "bold")
)
title_label.pack(pady=15)

profile_label = tk.Label(
    root,
    text="User: Not registered",
    font=("Arial", 11)
)
profile_label.pack()

# PROFILE SECTION

profile_frame = tk.LabelFrame(
    root,
    text="Create Profile",
    padx=15,
    pady=10
)
profile_frame.pack(
    fill="x",
    padx=20,
    pady=15
)

tk.Label(
    profile_frame,
    text="Name:"
).pack(anchor="w")

name_entry = tk.Entry(
    profile_frame,
    width=40
)
name_entry.pack(pady=5)

tk.Label(
    profile_frame,
    text="Daily Tracking Goal (mL):"
).pack(anchor="w")

goal_entry = tk.Entry(
    profile_frame,
    width=40
)
goal_entry.insert(0, "2000")
goal_entry.pack(pady=5)

tk.Button(
    profile_frame,
    text="Create Profile",
    command=create_user,
    width=20
).pack(pady=8)

# WATER INTAKE SECTION

water_frame = tk.LabelFrame(
    root,
    text="Water Intake",
    padx=15,
    pady=10
)
water_frame.pack(
    fill="x",
    padx=20,
    pady=5
)

tk.Label(
    water_frame,
    text="Enter water amount (mL):"
).pack(anchor="w")

amount_entry = tk.Entry(
    water_frame,
    width=40
)
amount_entry.pack(pady=5)

tk.Button(
    water_frame,
    text="Add Water",
    command=add_water,
    width=20
).pack(pady=8)

# DAILY SUMMARY

summary_frame = tk.LabelFrame(
    root,
    text="Daily Summary",
    padx=15,
    pady=10
)
summary_frame.pack(
    fill="x",
    padx=20,
    pady=10
)

total_label = tk.Label(
    summary_frame,
    text="0 mL",
    font=("Arial", 24, "bold")
)
total_label.pack()

remaining_label = tk.Label(
    summary_frame,
    text="Remaining: 2000 mL"
)
remaining_label.pack(pady=5)

progress = ttk.Progressbar(
    summary_frame,
    length=350,
    maximum=100
)
progress.pack(pady=8)

percentage_label = tk.Label(
    summary_frame,
    text="0% of daily goal"
)
percentage_label.pack()

# HISTORY SECTION

history_frame = tk.LabelFrame(
    root,
    text="Today's Drinking History",
    padx=15,
    pady=10
)
history_frame.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=5
)

history_list = tk.Listbox(
    history_frame,
    height=5,
    width=45
)
history_list.pack(
    fill="both",
    expand=True
)

# SAFETY INFORMATION

safety_label = tk.Label(
    root,
    text=(
        "Safety: Drink gradually. Do not force water intake. "
        "Follow medical fluid restrictions if prescribed."
    ),
    font=("Arial", 9),
    wraplength=450,
    fg="gray"
)
safety_label.pack(pady=12)

# ==================================
# CLOSE APPLICATION
# ==================================

def close_application():
    connection.close()
    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_application
)

# ==================================
# RUN APPLICATION
# ==================================

root.mainloop()

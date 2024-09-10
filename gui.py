from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import importlib
import sys
import json
import os

class SettingsGUI:
    def __init__(self, master):
        self.master = master
        master.title("Visa Appointment Rescheduler Settings")
        master.geometry("500x900") 

        self.settings = self.load_settings()
        self.dependencies = ["requests", "selenium", "webdriver_manager"]

        self.dev_frame_visible = False
        self.create_widgets()

    def load_settings(self):
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                return json.load(f)
        else:
            # Default settings if file doesn't exist
            date_start = str(datetime.now().date())
            date_end = str(datetime.now().date().replace(year=datetime.now().year + 1))
            return {
                "USER_EMAIL": "",
                "USER_PASSWORD": "",
                "EARLIEST_ACCEPTABLE_DATE": date_start,
                "LATEST_ACCEPTABLE_DATE": date_end,
                "HEADLESS_MODE": False,
                "TEST_MODE": True,
                "DETACH": True,
                "NEW_SESSION_AFTER_FAILURES": 5,
                "NEW_SESSION_DELAY": 120,
                "TIMEOUT": 10,
                "FAIL_RETRY_DELAY": 30,
                "DATE_REQUEST_DELAY": 30,
                "DATE_REQUEST_MAX_RETRY": 60,
                "DATE_REQUEST_MAX_TIME": 30 * 60,
                "LOGIN_URL": "https://ais.usvisa-info.com/en-ca/niv/users/sign_in",
                "AVAILABLE_DATE_REQUEST_SUFFIX": "/days/94.json?appointments[expedite]=false",
                "APPOINTMENT_PAGE_URL": "https://ais.usvisa-info.com/en-ca/niv/schedule/{id}/appointment",
                "PAYMENT_PAGE_URL": "https://ais.usvisa-info.com/en-ca/niv/schedule/{id}/payment",
                "REQUEST_HEADERS": {
                    "X-Requested-With": "XMLHttpRequest",
                }
            }

    def save_settings(self):
    # Get settings from the GUI
        settings = {
            "USER_EMAIL": self.user_email.get(),
            "USER_PASSWORD": self.user_password.get(),
            "EARLIEST_ACCEPTABLE_DATE": self.earliest_date.get(),
            "LATEST_ACCEPTABLE_DATE": self.latest_date.get(),
            "SHOW_GUI": self.show_gui.get(),
            "TEST_MODE": self.test_mode.get(),
            "SELECTED_CITY": self.selected_city.get()
        }

        # Validate dates
        try:
            earliest = datetime.strptime(self.earliest_date.get(), "%Y-%m-%d")
            latest = datetime.strptime(self.latest_date.get(), "%Y-%m-%d")
            if earliest > latest:
                messagebox.showerror("Error", "Earliest date cannot be later than latest date.")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        
        dev_settings = {setting: self.dev_vars[setting].get() for setting in self.dev_vars}
        settings.update(dev_settings)

        # Map city to value and update the suffix
        city_values = {
            "Calgary": 89,
            "Halifax": 90,
            "Montreal": 91,
            "Ottawa": 92,
            "Quebec City": 93,
            "Toronto": 94,
            "Vancouver": 95
        }

        selected_city_value = city_values.get(self.selected_city.get(), 94)
        settings["AVAILABLE_DATE_REQUEST_SUFFIX"] = f"/days/{selected_city_value}.json?appointments[expedite]=false"

        # Save settings to file
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        messagebox.showinfo("Success", "Settings saved successfully!")

    def create_widgets(self):
        # Account Info
        ttk.Label(self.master, text="Account Information", font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(self.master, text="Email:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.user_email = tk.StringVar(value=self.settings.get("USER_EMAIL", ""))
        ttk.Entry(self.master, textvariable=self.user_email, width=40).grid(row=1, column=1, pady=2)

        ttk.Label(self.master, text="Password:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.user_password = tk.StringVar(value=self.settings.get("USER_PASSWORD", ""))
        ttk.Entry(self.master, textvariable=self.user_password, show="*", width=40).grid(row=2, column=1, pady=2)

        # Appointment Dates
        ttk.Label(self.master, text="Appointment Dates", font=("TkDefaultFont", 12, "bold")).grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Label(self.master, text="Earliest Acceptable Date:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
        self.earliest_date = tk.StringVar(value=self.settings.get("EARLIEST_ACCEPTABLE_DATE", ""))
        ttk.Entry(self.master, textvariable=self.earliest_date, width=40).grid(row=4, column=1, pady=2)
 
        ttk.Label(self.master, text="Latest Acceptable Date:").grid(row=5, column=0, sticky="e", padx=5, pady=2)
        self.latest_date = tk.StringVar(value=self.settings.get("LATEST_ACCEPTABLE_DATE", ""))
        ttk.Entry(self.master, textvariable=self.latest_date, width=40).grid(row=5, column=1, pady=2)

        # Other Settings
        ttk.Label(self.master, text="Other Settings", font=("TkDefaultFont", 12, "bold")).grid(row=12, column=0, columnspan=2, pady=10)
        self.show_gui = tk.BooleanVar(value=self.settings.get("SHOW_GUI", True))
        ttk.Checkbutton(self.master, text="Headless mode", variable=self.show_gui).grid(row=13, column=0, columnspan=2, pady=2)

        self.test_mode = tk.BooleanVar(value=self.settings.get("TEST_MODE", True))
        ttk.Checkbutton(self.master, text="Test Mode", variable=self.test_mode).grid(row=14, column=0, columnspan=2, pady=2)

        # Dependency Management
        ttk.Label(self.master, text="Dependency Management", font=("TkDefaultFont", 12, "bold")).grid(row=17, column=0, columnspan=2, pady=10)
        
        self.dependency_buttons_frame = tk.Frame(self.master)
        self.dependency_buttons_frame.grid(row=20, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.dependency_buttons = {}

        for i, dep in enumerate(self.dependencies):
            status = self.check_dependency(dep)
            button_text = f"{dep}: {'Installed' if status else 'Not Installed'}"

            # Create button with initial color based on status using tk.Button
            button = tk.Button(self.dependency_buttons_frame, text=button_text, command=lambda d=dep: self.install_dependency(d))

            # Set background color based on status
            if status:
                button.config(bg="green", fg="white")
            else:
                button.config(bg="gray", fg="white")

            button.grid(row=0, column=i, padx=5) 

            self.dependency_buttons[dep] = button


        # Collapsible Dev Section Toggle Button
        self.toggle_button = ttk.Button(self.master, text="Show Developer Options", command=self.toggle_dev_section)
        self.toggle_button.grid(row=21, column=0, columnspan=2, pady=10)

        # Dev Section Frame (initially hidden)
        self.dev_frame = ttk.Frame(self.master)
        self.dev_frame.grid(row=22, column=0, columnspan=2, sticky="nsew", pady=2)
        self.dev_frame.grid_remove()  # Hide initially

        # Developer Settings (inside the collapsible section)
        ttk.Label(self.dev_frame, text="Developer Options", font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        self.create_dev_widgets()
        self.create_city_dropdown()
        # Save and Start Buttons
        save_start_frame = ttk.Frame(self.master)
        save_start_frame.grid(row=25, column=0, columnspan=2, pady=10)

        save_button = ttk.Button(save_start_frame, text="Save Settings", command=self.save_settings)
        start_button = ttk.Button(save_start_frame, text="Start Rescheduler", command=self.start_rescheduler)

        # Pack the buttons side by side with some padding
        save_button.pack(side="left", padx=10)
        start_button.pack(side="left", padx=10)

        # Center the frame in its grid cell
        save_start_frame.grid_columnconfigure(0, weight=1)

    def create_city_dropdown(self):
        """Creates a dropdown menu for city selection."""
        cities = ["Calgary", "Halifax", "Montreal", "Ottawa", "Quebec City", "Toronto", "Vancouver"]
        self.selected_city = tk.StringVar()
        self.selected_city.set(cities[5])

        ttk.Label(self.master, text="Select City:").grid(row=10, column=0, sticky="e", padx=5, pady=2)

        city_dropdown = ttk.OptionMenu(self.master, self.selected_city, cities[5], *cities)
        city_dropdown.grid(row=10, column=1, pady=2)
        city_dropdown.config(width=35, style="TMenubutton")

    def toggle_dev_section(self):
        """Toggle visibility of developer options section."""
        if self.dev_frame_visible:
            self.dev_frame.grid_remove()
            self.toggle_button.config(text="Show Developer Options")
        else:
            self.dev_frame.grid()
            self.toggle_button.config(text="Hide Developer Options")
        self.dev_frame_visible = not self.dev_frame_visible

    def create_dev_widgets(self):
        """Creates widgets for developer settings within the collapsible frame."""
        dev_settings = {
            "DETACH": True,
            "NEW_SESSION_AFTER_FAILURES": 5,
            "NEW_SESSION_DELAY": 120,
            "TIMEOUT": 10,
            "FAIL_RETRY_DELAY": 30,
            "DATE_REQUEST_DELAY": 30,
            "DATE_REQUEST_MAX_RETRY": 60,
            "DATE_REQUEST_MAX_TIME": 30 * 60,
            "LOGIN_URL": "https://ais.usvisa-info.com/en-ca/niv/users/sign_in",
            "AVAILABLE_DATE_REQUEST_SUFFIX": "/days/94.json?appointments[expedite]=false",
            "APPOINTMENT_PAGE_URL": "https://ais.usvisa-info.com/en-ca/niv/schedule/{id}/appointment",
            "PAYMENT_PAGE_URL": "https://ais.usvisa-info.com/en-ca/niv/schedule/{id}/payment",
            "REQUEST_HEADERS": {
                "X-Requested-With": "XMLHttpRequest",
            }
        }

        self.dev_vars = {}
    
        for i, (setting, value) in enumerate(dev_settings.items()):
            ttk.Label(self.dev_frame, text=f"{setting}:").grid(row=i+1, column=0, sticky="e", padx=5, pady=2)
            
            # Choose the appropriate type of variable
            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
            elif isinstance(value, int):
                var = tk.IntVar(value=value)
            else:
                var = tk.StringVar(value=str(value))
            
            ttk.Entry(self.dev_frame, textvariable=var, width=40).grid(row=i+1, column=1, pady=2)
            self.dev_vars[setting] = var

    def check_dependency(self, package):
        try:
            importlib.import_module(package)
            return True
        except ImportError:
            return False

    def install_dependency(self, package):
        if self.check_dependency(package):
            messagebox.showinfo("Info", f"{package} is already installed.")
            return

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            messagebox.showinfo("Success", f"{package} has been successfully installed.")
            
            for dep in self.dependencies:
                self.update_dependency_button(dep)

        except subprocess.CalledProcessError:
            messagebox.showerror("Error", f"Failed to install {package}. Please install it manually.")

    def update_dependency_button(self, package):
        status = self.check_dependency(package)
        self.dependency_buttons[package].config(text=f"{package}: {'Installed' if status else 'Not Installed'}")


    def start_rescheduler(self):
        self.save_settings()  # Save settings before starting
        
        # Check if all dependencies are installed
        missing_deps = [dep for dep in self.dependencies if not self.check_dependency(dep)]
        if missing_deps:
            messagebox.showerror("Error", f"Missing dependencies: {', '.join(missing_deps)}. Please install them before starting.")
            return

        try:
            subprocess.Popen([sys.executable, "reschedule.py"])
            messagebox.showinfo("Success", "Rescheduler started successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start rescheduler: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SettingsGUI(root)
    root.mainloop()
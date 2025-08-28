import sqlite3
import tkinter as tk
from tkinter import messagebox
import os
import threading
import pystray
from PIL import Image
import subprocess
import datetime
import time

# ----------------- USER CONFIGURATION -----------------
# Set the path where Ollama is installed on your system (Windows/Linux/macOS)
OLLAMA_DIR = r"C:\Path\To\Ollama"  # <-- CHANGE THIS to your Ollama directory

# Set the Ollama host (default is localhost)
OLLAMA_HOST = "127.0.0.1:11434"  # <-- CHANGE IF NEEDED

# Path to your system tray icon image
ICON_PATH = "icon.png"  # <-- CHANGE TO YOUR ICON FILE PATH

# Model to use
OLLAMA_MODEL = "mistral"  # <-- CHANGE MODEL IF NEEDED

# ------------------------------------------------------

# --- Add Ollama to PATH ---
os.environ["PATH"] = OLLAMA_DIR + ";" + os.environ.get("PATH", "")
os.environ["OLLAMA_HOST"] = OLLAMA_HOST

# --- Function to call Ollama ---
def ask_ollama(query):
    """
    Sends a query to Ollama AI model and returns the response.
    """
    try:
        process = subprocess.Popen(
            ["ollama", "run", OLLAMA_MODEL],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace"
        )
        stdout, stderr = process.communicate(query, timeout=30)
        if stderr:
            print("Ollama Error:", stderr)
        return stdout.strip() if stdout else "No response from AI."
    except subprocess.TimeoutExpired:
        process.kill()
        return "Request timed out."

# --- Database Initialization ---
def init_db():
    """
    Initialize the SQLite database and create tables if not exists.
    """
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                remind_time TEXT,
                notified INTEGER DEFAULT 0
            )
        """)

# --- Reminder Functions ---
def add_reminder(user_id, message, remind_time):
    """
    Add a reminder to the database.
    """
    with sqlite3.connect("users.db") as conn:
        conn.execute(
            "INSERT INTO reminders (user_id, message, remind_time) VALUES (?, ?, ?)",
            (user_id, message, remind_time)
        )

def check_reminders(chat_window, user_id):
    """
    Periodically check for due reminders and display them in the chat.
    """
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, message FROM reminders WHERE user_id = ? AND remind_time = ? AND notified = 0",
                (user_id, now)
            )
            reminders = cursor.fetchall()
            for reminder in reminders:
                chat_window.after(0, chat_window.update_chat, f"Reminder: {reminder[1]}", "System")
                cursor.execute("UPDATE reminders SET notified = 1 WHERE id = ?", (reminder[0],))
        time.sleep(60)  # Check every minute

# --- User Authentication Functions ---
def validate_login(username, password):
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        return cursor.fetchone()

def register_user(username, password):
    try:
        with sqlite3.connect("users.db") as conn:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        return True
    except sqlite3.IntegrityError:
        return False

# --- Chat Window ---
class ChatWindow(tk.Tk):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.title("ThinkBot Assistant")
        self.geometry("400x500")
        self.protocol('WM_DELETE_WINDOW', self.withdraw)
        
        self.chat_history = tk.Text(self, wrap=tk.WORD, state="disabled")
        self.chat_history.pack(fill=tk.BOTH, expand=True)
        self.chat_history.tag_configure("user_tag", background="lightgrey", foreground="black", font=("Helvetica", 12))
        
        input_frame = tk.Frame(self)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        self.user_input = tk.Entry(input_frame)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_input.bind("<Return>", lambda e: self.send_message())
        
        self.send_btn = tk.Button(input_frame, text="📤", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)
        
        threading.Thread(target=check_reminders, args=(self, user_id), daemon=True).start()
    
    def update_chat(self, message, sender):
        self.chat_history.config(state="normal")
        if sender == "You":
            self.chat_history.insert(tk.END, f"{sender}: {message}\n\n", "user_tag")
        else:
            self.chat_history.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_history.config(state="disabled")
        self.chat_history.see(tk.END)

    def send_message(self):
        query = self.user_input.get().strip()
        if not query:
            return
        self.user_input.delete(0, tk.END)
        self.send_btn.config(state="disabled")
        self.update_chat(query, "You")

        def get_response():
            if "remind me" in query.lower():
                self.set_reminder(query)
                response = "Reminder set!"
            else:
                response = ask_ollama(query)
            self.after(0, self.update_chat, response, "AI")
            self.after(0, self.send_btn.config, {"state": "normal"})

        threading.Thread(target=get_response, daemon=True).start()

    def set_reminder(self, query):
        now = datetime.datetime.now()
        if "in" in query:
            try:
                # Extract numbers from query as minutes
                time_parts = [int(s) for s in query.split() if s.isdigit()]
                minutes = time_parts[0] if time_parts else 1
                remind_time = (now + datetime.timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M")
            except:
                return self.update_chat("Could not set reminder. Format: 'Remind me in 10 minutes'", "System")
        else:
            remind_time = now.strftime("%Y-%m-%d") + " " + query.split()[-1]
        message = query.replace("remind me", "").strip()
        add_reminder(self.user_id, message, remind_time)

# --- Login Window ---
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ThinkBot Login")
        self.geometry("300x200")

        tk.Label(self, text="Username:").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Password:").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Login", command=self.attempt_login).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Register", command=self.attempt_register).pack(side=tk.RIGHT, padx=5)

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if user := validate_login(username, password):
            self.destroy()
            ChatWindow(user[0]).mainloop()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def attempt_register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "All fields are required")
            return
        if register_user(username, password):
            messagebox.showinfo("Success", "User registered successfully. You can now log in.")
        else:
            messagebox.showerror("Error", "Username already exists. Please choose another.")

# --- Main Entry Point ---
if __name__ == "__main__":
    init_db()
    LoginWindow().mainloop()

import sqlite3
import tkinter as tk
from tkinter import messagebox
import os
import threading
import pystray
from PIL import Image
import subprocess

# ----------------- USER CONFIGURATION -----------------
# Set the path where Ollama is installed on your system
OLLAMA_DIR = r"C:\Users\YOUR_USERNAME\AppData\Local\Programs\Ollama"  # <-- CHANGE THIS

# Set the Ollama host (IP:PORT) if different
OLLAMA_HOST = "192.168.1.5:11568"  # <-- CHANGE IP AND PORT YOU WANT USE

# Path to your system tray icon image
ICON_PATH = "icon.png"  # <-- CHANGE TO YOUR ICON FILE PATH

# ------------------------------------------------------

# --- Add Ollama to PATH ---
os.environ["PATH"] = OLLAMA_DIR + ";" + os.environ["PATH"]
os.environ["OLLAMA_HOST"] = OLLAMA_HOST

# --- Function to call Ollama ---
def ask_ollama(query):
    """
    Sends a query to Ollama AI model and returns the response.
    """
    try:
        process = subprocess.Popen(
            ["ollama", "run", "deepseek-r1:1.5b"],  # Change model if needed
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace"
        )
        stdout, stderr = process.communicate(query, timeout=30)
        if stderr:
            print("Ollama Error:", stderr)
        return stdout
    except subprocess.TimeoutExpired:
        process.kill()
        return "Request timed out."

# --- Database Initialization ---
def init_db():
    """
    Initialize the SQLite database and create users table if not exists.
    """
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)

# --- User Authentication Functions ---
def validate_login(username, password):
    """
    Validate user login credentials.
    """
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        return cursor.fetchone()

def register_user(username, password):
    """
    Register a new user in the database.
    """
    try:
        with sqlite3.connect("users.db") as conn:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        return True
    except sqlite3.IntegrityError:
        return False

# --- System Tray Icon ---
def create_tray_icon(window):
    """
    Create a system tray icon with Show and Exit options.
    """
    try:
        image = Image.open(ICON_PATH)
    except Exception as e:
        print("Error loading tray icon:", e)
        image = Image.new("RGB", (64, 64), color="white")
    menu = pystray.Menu(
        pystray.MenuItem('Show', lambda: window.deiconify()),
        pystray.MenuItem('Exit', lambda: os._exit(0))
    )
    icon = pystray.Icon("ThinkBot", image, "ThinkBot Assistant", menu)
    return icon

# --- Chat Window ---
class ChatWindow(tk.Tk):
    def __init__(self, user_id):
        super().__init__()
        self.title("ThinkBot Assistant")
        self.geometry("400x500")
        self.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)

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

        self.tray_icon = create_tray_icon(self)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def minimize_to_tray(self):
        self.withdraw()

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
            try:
                response = ask_ollama(query)
                self.after(0, self.update_chat, response, "AI")
            finally:
                self.after(0, self.send_btn.config, {"state": "normal"})

        threading.Thread(target=get_response, daemon=True).start()

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
            messagebox.showinfo("Success", "Registration successful!")
        else:
            messagebox.showerror("Error", "Username already exists")

# --- Main Entry Point ---
if __name__ == "__main__":
    init_db()
    LoginWindow().mainloop()

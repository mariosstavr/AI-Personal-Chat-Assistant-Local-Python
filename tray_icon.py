import sqlite3
import tkinter as tk
from tkinter import messagebox
import os
import threading
import pystray
from PIL import Image
import subprocess

# --- Add the directory containing ollama.exe to PATH ---
ollama_dir = r"C:\Users\Marios\AppData\Local\Programs\Ollama"
os.environ["PATH"] = ollama_dir + ";" + os.environ["PATH"]

# --- Set the Ollama host environment variable ---
os.environ["OLLAMA_HOST"] = "10.0.0.142:11434"

# --- Function to call Ollama ---
def ask_ollama(query):
    try:
        process = subprocess.Popen(
            ["ollama", "run", "deepseek-r1:1.5b"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",   # Force UTF-8 encoding
            errors="replace"    # Replace characters that can't be decoded
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

# --- System Tray Icon ---
def create_tray_icon(window):
    try:
        image = Image.open("icon.png")  # Ensure you have an icon.png file in your working directory
    except Exception as e:
        print("Error loading tray icon:", e)
        image = Image.new("RGB", (64, 64), color="white")
    menu = pystray.Menu(
        pystray.MenuItem('Show', lambda: window.deiconify()),
        pystray.MenuItem('Exit', lambda: os._exit(0))
    )
    icon = pystray.Icon("myStirixis", image, "myStirixis Assistant", menu)
    return icon

# --- Chat Window ---
class ChatWindow(tk.Tk):
    def __init__(self, user_id):
        super().__init__()
        self.title("myStirixis Assistant")
        self.geometry("400x500")
        self.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)
        self.chat_history = tk.Text(self, wrap=tk.WORD, state="disabled")
        self.chat_history.pack(fill=tk.BOTH, expand=True)
        # Configure a tag for user messages (grey template)
        self.chat_history.tag_configure("user_tag", background="lightgrey", foreground="black", font=("Helvetica", 12))
        
        input_frame = tk.Frame(self)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        self.user_input = tk.Entry(input_frame)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_input.bind("<Return>", lambda e: self.send_message())
        # Here you can change the button text to an emoji (e.g., 📤)
        self.send_btn = tk.Button(input_frame, text="📤", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)
        self.tray_icon = create_tray_icon(self)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def minimize_to_tray(self):
        self.withdraw()
    
    def update_chat(self, message, sender):
        self.chat_history.config(state="normal")
        if sender == "You":
            # Insert user message with "user_tag" for grey background
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
        self.title("Login")
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

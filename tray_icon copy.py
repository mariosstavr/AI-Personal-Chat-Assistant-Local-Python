import sqlite3
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
import os
import threading
import pystray
from PIL import Image
import subprocess
import requests

os.environ["OLLAMA_HOST"] = "10.0.0.208:11434"


def ask_ollama_http(query):
    url = "10.0.0.208:11434/api/v1/run/deepseek-r1"  # Adjust this endpoint if needed
    data = {"query": query}
    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print("HTTP Request Error:", e)
        return "Request failed."
def ask_ollama(query):
    try:
        process = subprocess.Popen(
            ["ollama", "run", "deepseek-r1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(query, timeout=30)
        if stderr:
            print("Ollama Error:", stderr)
        return stdout
    except subprocess.TimeoutExpired:
        process.kill()
        return "Request timed out."


# --- Initialize the User Database ---
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- User Authentication Functions ---
def validate_login(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def register_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        messagebox.showerror("Registration Error", "Username already exists!")
    finally:
        conn.close()

# --- Chat Window ---
def open_chat(user_id):
    chat_window = tk.Tk()
    chat_window.title("myStirixis Assistant")
    chat_window.geometry("400x500")

    # Chat history (read-only)
    chat_history = tk.Text(chat_window, wrap=tk.WORD, state="disabled")
    chat_history.pack(fill=tk.BOTH, expand=True)

    # User input field
    user_input = tk.Entry(chat_window)
    user_input.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=5, pady=5)

    # Send button function
    def send_message():
        query = user_input.get()
        user_input.delete(0, tk.END)
        chat_history.config(state="normal")
        chat_history.insert(tk.END, f"You: {query}\n\n")
        chat_history.config(state="disabled")
        
        # Get Ollama response in a separate thread to avoid freezing the UI
        def get_ollama_response():
            response = ask_ollama(query)
            chat_history.config(state="normal")
            chat_history.insert(tk.END, f"AI: {response}\n\n")
            chat_history.config(state="disabled")
            chat_history.see(tk.END)  # Auto-scroll to bottom
        threading.Thread(target=get_ollama_response).start()

    send_button = tk.Button(chat_window, text="Send", command=send_message)
    send_button.pack(side=tk.RIGHT, padx=5, pady=5)

    chat_window.mainloop()

# --- Login / Registration Window ---
def open_login():
    login_window = tk.Tk()
    login_window.title("Login")
    login_window.geometry("300x200")

    tk.Label(login_window, text="Username:").pack(pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Password:").pack(pady=5)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack(pady=5)

    # Attempt login
    def attempt_login():
        username = username_entry.get()
        password = password_entry.get()
        user_id = validate_login(username, password)
        if user_id:
            messagebox.showinfo("Login Successful", f"Welcome, {username}!")
            login_window.destroy()  # Close login window
            open_chat(user_id)      # Open chat window for this user
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    # Attempt registration
    def attempt_register():
        username = username_entry.get()
        password = password_entry.get()
        if username and password:
            register_user(username, password)
            messagebox.showinfo("Registration", "User registered successfully. Please log in.")
        else:
            messagebox.showerror("Registration Failed", "Please enter both username and password.")

    tk.Button(login_window, text="Login", command=attempt_login).pack(pady=5)
    tk.Button(login_window, text="Register", command=attempt_register).pack(pady=5)

    login_window.mainloop()

# --- Main Entry Point ---
if __name__ == "__main__":
    open_login()

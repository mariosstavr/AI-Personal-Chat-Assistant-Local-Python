This is a Tkinter-based AI chat assistant named ThinkBot Assistant, which integrates user authentication, a chat interface, and a system tray icon.
It connects to Ollama, an AI model, to generate responses and uses an SQLite database to store user credentials.

Key Features:
User Authentication (SQLite)

Users can register and log in using a local SQLite database.
Secure user validation with unique usernames and passwords.
AI Chatbot (Ollama Integration)

Users can interact with an AI assistant powered by Ollama (deepseek-r1:1.5b).
Queries are sent to the AI, and responses are displayed in the chat window.
Background threading prevents UI freezing while waiting for responses.
Graphical User Interface (GUI) with Tkinter

A login window for authentication.
A chat window that allows users to send messages and receive AI responses.
Styled chat messages (e.g., user messages have a light gray background).
System Tray Integration (pystray)

The app runs in the system tray when minimized.
Users can restore the window or exit via a right-click menu.
Uses a custom tray icon.png (fallbacks to a blank image if missing).
Multi-threading for Smooth UI

The chatbot runs on a separate thread to ensure a smooth user experience.
Technical Stack:
Python (Core language)
SQLite3 (Database for user authentication)
Tkinter (GUI framework)
Pystray (System tray icon support)
PIL (Pillow) (For image handling)
Subprocess (For executing AI model queries)

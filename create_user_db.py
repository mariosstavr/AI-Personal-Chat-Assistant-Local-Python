import sqlite3

def init_db():
    # Connect to the database (creates the file if it doesn't exist)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Create the users table if it doesn't already exist
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Save (commit) the changes and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("User database (users.db) created successfully.")

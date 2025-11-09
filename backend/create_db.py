# create_db.py
import sqlite3
import bcrypt

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);
""")

# Default user: admin / admin123
password = b"admin123"
hashed = bcrypt.hashpw(password, bcrypt.gensalt())

cursor.execute(
    "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
    ("admin", hashed)
)

conn.commit()
conn.close()

print("✅ Created app.db with default user: admin / admin123")

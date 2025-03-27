import sqlite3
import os
from pathlib import Path

def init_database():
    # Create database directory if it doesn't exist
    db_dir = Path("data")
    db_dir.mkdir(exist_ok=True)
    
    db_path = db_dir / "auth.db"
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (username TEXT PRIMARY KEY,
                 password TEXT,
                 created_at TIMESTAMP,
                 last_login TIMESTAMP)''')
    
    # Create chats table
    c.execute('''CREATE TABLE IF NOT EXISTS chats
                (chat_id TEXT PRIMARY KEY,
                 username TEXT,
                 title TEXT,
                 created_at TIMESTAMP,
                 last_updated TIMESTAMP,
                 FOREIGN KEY (username) REFERENCES users(username))''')
    
    # Create chat_messages table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 chat_id TEXT,
                 role TEXT,
                 content TEXT,
                 timestamp TIMESTAMP,
                 FOREIGN KEY (chat_id) REFERENCES chats(chat_id))''')
    
    # Create resources table
    c.execute('''CREATE TABLE IF NOT EXISTS resources
                (resource_id TEXT PRIMARY KEY,
                 username TEXT,
                 query TEXT,
                 content TEXT,
                 created_at TIMESTAMP,
                 FOREIGN KEY (username) REFERENCES users(username))''')
    
    # Create quizzes table
    c.execute('''CREATE TABLE IF NOT EXISTS quizzes
                (quiz_id TEXT PRIMARY KEY,
                 username TEXT,
                 topic TEXT,
                 questions TEXT,
                 score INTEGER,
                 submitted BOOLEAN,
                 created_at TIMESTAMP,
                 FOREIGN KEY (username) REFERENCES users(username))''')
    
    # Create roadmaps table
    c.execute('''CREATE TABLE IF NOT EXISTS roadmaps
                (id TEXT PRIMARY KEY,
                 username TEXT,
                 topic TEXT,
                 content TEXT,
                 created_at TIMESTAMP,
                 FOREIGN KEY (username) REFERENCES users(username))''')
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
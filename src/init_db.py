import os
from pymongo import MongoClient
from datetime import datetime
from pathlib import Path

def init_database():
    # Get MongoDB connection string from environment variable or use default
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
    db_name = os.environ.get("MONGODB_DB_NAME", "learning_assistant")
    
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    # Create collections (equivalent to tables in SQL)
    users = db.users
    chats = db.chats
    chat_messages = db.chat_messages
    resources = db.resources
    quizzes = db.quizzes
    roadmaps = db.roadmaps
    
    # Create indexes for better query performance
    users.create_index("username", unique=True)
    chats.create_index("username")
    chats.create_index("chat_id", unique=True)
    chat_messages.create_index("chat_id")
    resources.create_index("username")
    resources.create_index("resource_id", unique=True)
    quizzes.create_index("username")
    quizzes.create_index("quiz_id", unique=True)
    roadmaps.create_index("username")
    roadmaps.create_index("id", unique=True)
    
    print("MongoDB database initialized successfully!")

if __name__ == "__main__":
    init_database()
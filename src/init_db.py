import os
from pymongo import MongoClient
from datetime import datetime
from pathlib import Path

def init_database():
    """
    Initializes the MongoDB database for the AI Coding Tutor application.

    This script connects to MongoDB, creates necessary collections (if they don't exist),
    and sets up indexes on various fields to optimize query performance.
    It uses environment variables for MongoDB URI and database name, with defaults
    if the environment variables are not set.
    """
    # Get MongoDB connection string from environment variable, with a default value.
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
    # Get database name from environment variable, with a default value.
    db_name = os.environ.get("MONGODB_DB_NAME", "learning_assistant")
    
    # Connect to the MongoDB server.
    client = MongoClient(mongo_uri)
    # Select the database (it will be created if it doesn't exist upon first write operation).
    db = client[db_name]
    
    # Get references to collections.
    # MongoDB is schema-less, so collections are created when the first document is inserted,
    # or when an index is created on them.
    users = db.users
    chats = db.chats
    chat_messages = db.chat_messages
    resources = db.resources
    quizzes = db.quizzes
    roadmaps = db.roadmaps
    
    # Create indexes to improve query performance.
    # Indexes are crucial for faster lookups, especially on fields used in queries.
    # `unique=True` enforces that values for the indexed field are unique across the collection.

    # For the 'users' collection:
    users.create_index("username", unique=True) # Usernames must be unique.

    # For the 'chats' collection:
    chats.create_index("username") # To quickly find all chats for a user.
    chats.create_index("chat_id", unique=True) # Chat IDs must be unique.

    # For the 'chat_messages' collection:
    chat_messages.create_index("chat_id") # To quickly find all messages for a chat.

    # For the 'resources' collection:
    resources.create_index("username") # To find resources saved by a user.
    resources.create_index("resource_id", unique=True) # Resource IDs must be unique.

    # For the 'quizzes' collection:
    quizzes.create_index("username") # To find quizzes taken by a user.
    quizzes.create_index("quiz_id", unique=True) # Quiz IDs must be unique.

    # For the 'roadmaps' collection:
    roadmaps.create_index("username") # To find roadmaps created by a user.
    roadmaps.create_index("id", unique=True) # Roadmap IDs must be unique.
    
    print("MongoDB database initialized successfully!")

# This allows the script to be run directly to initialize the database.
if __name__ == "__main__":
    init_database()
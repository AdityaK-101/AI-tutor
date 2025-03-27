from pymongo import MongoClient
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.config import MONGO_URI, DB_NAME, COLLECTIONS

class Database:
    def __init__(self):
        from src.chat_interface import ChatInterface
        self.chat_interface = ChatInterface()
        from src.auth import Auth
        self.auth = Auth()
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]

    def save_chat_history(self, user_id, message, response):
        """Save chat message and response to database"""
        try:
            collection = self.db[COLLECTIONS["chat_history"]]
            chat_data = {
                "user_id": user_id,
                "message": message,
                "response": response,
                "timestamp": datetime.now()
            }
            return collection.insert_one(chat_data)
        except Exception as e:
            print(f"Error saving chat: {e}")
            return None

    def get_chat_history(self, user_id, limit=10):
        """Get chat history for a user"""
        try:
            collection = self.db[COLLECTIONS["chat_history"]]
            return list(collection.find(
                {"user_id": user_id},
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit))
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []

    def save_quiz_result(self, user_id, topic, score):
        """Save quiz result to database"""
        try:
            collection = self.db[COLLECTIONS["quiz_results"]]
            result = {
                "user_id": user_id,
                "topic": topic,
                "score": score,
                "timestamp": datetime.now()
            }
            return collection.insert_one(result)
        except Exception as e:
            print(f"Error saving quiz result: {e}")
            return None

    def get_resources(self, filters=None):
        """Get learning resources based on filters"""
        try:
            collection = self.db[COLLECTIONS["resources"]]
            return list(collection.find(filters or {}, {"_id": 0}))
        except Exception as e:
            print(f"Error getting resources: {e}")
            return []

    def get_user_progress(self, user_id):
        """Get user's learning progress"""
        try:
            collection = self.db[COLLECTIONS["quiz_results"]]
            return list(collection.find(
                {"user_id": user_id},
                {"_id": 0}
            ).sort("timestamp", -1))
        except Exception as e:
            print(f"Error getting user progress: {e}")
            return []

    def save_roadmap(self, user_id, path, steps):
        """Save generated learning roadmap"""
        try:
            collection = self.db[COLLECTIONS["roadmaps"]]
            roadmap_data = {
                "user_id": user_id,
                "path": path,
                "steps": steps,
                "timestamp": datetime.now()
            }
            return collection.insert_one(roadmap_data)
        except Exception as e:
            print(f"Error saving roadmap: {e}")
            return None 
from pymongo import MongoClient
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.config import MONGO_URI, DB_NAME, COLLECTIONS

class Database:
    """
    Handles interactions with the MongoDB database.

    This class provides methods for connecting to the database and performing
    CRUD (Create, Read, Update, Delete) operations on various collections
    related to chat history, quiz results, resources, and learning roadmaps.
    """
    def __init__(self):
        """
        Initializes the Database class.

        Establishes a connection to the MongoDB database using the URI and
        database name specified in the configuration. It also initializes
        instances of ChatInterface and Auth for potential use within database methods.
        """
        # Import here to avoid circular dependencies, as other modules might import Database
        from src.chat_interface import ChatInterface
        self.chat_interface = ChatInterface() # Instance for potential AI interactions from DB methods
        from src.auth import Auth
        self.auth = Auth() # Instance for user-related operations if needed from DB methods

        # Establish connection to MongoDB
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME] # Select the database

    def save_chat_history(self, user_id, message, response):
        """
        Saves a chat message and its corresponding AI response to the database.

        Args:
            user_id: The ID of the user who initiated the chat.
            message: The user's message.
            response: The AI's response to the message.

        Returns:
            The result of the insert operation (e.g., InsertOneResult object)
            or None if an error occurs.
        """
        try:
            # Get the specific collection for chat history
            collection = self.db[COLLECTIONS["chat_history"]]
            chat_data = {
                "user_id": user_id, # To associate chat with a user
                "message": message, # User's message
                "response": response, # AI's response
                "timestamp": datetime.now() # Timestamp of the interaction
            }
            # Insert the chat data into the collection
            return collection.insert_one(chat_data)
        except Exception as e:
            # Log any error that occurs during the database operation
            print(f"Error saving chat: {e}")
            return None # Return None to indicate failure

    def get_chat_history(self, user_id, limit=10):
        """
        Retrieves the chat history for a specific user.

        Args:
            user_id: The ID of the user.
            limit: The maximum number of chat entries to retrieve (defaults to 10).

        Returns:
            A list of chat history entries, sorted by timestamp in descending order.
            Returns an empty list if an error occurs or no history is found.
        """
        try:
            collection = self.db[COLLECTIONS["chat_history"]]
            # Find chat entries for the given user_id
            # {"_id": 0} excludes the MongoDB default _id field from results
            # .sort("timestamp", -1) sorts by timestamp in descending order (most recent first)
            # .limit(limit) restricts the number of results
            return list(collection.find(
                {"user_id": user_id}, # Filter by user_id
                {"_id": 0}            # Projection: exclude _id
            ).sort("timestamp", -1).limit(limit))
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return [] # Return an empty list in case of error

    def save_quiz_result(self, user_id, topic, score):
        """
        Saves the result of a quiz taken by a user.

        Args:
            user_id: The ID of the user.
            topic: The topic of the quiz.
            score: The score achieved by the user.

        Returns:
            The result of the insert operation or None if an error occurs.
        """
        try:
            collection = self.db[COLLECTIONS["quiz_results"]]
            result = {
                "user_id": user_id, # User who took the quiz
                "topic": topic,     # Topic of the quiz
                "score": score,     # Score achieved
                "timestamp": datetime.now() # Timestamp of quiz completion
            }
            return collection.insert_one(result)
        except Exception as e:
            print(f"Error saving quiz result: {e}")
            return None

    def get_resources(self, filters=None):
        """
        Retrieves learning resources based on specified filters.

        Args:
            filters: A dictionary of filters to apply to the query (defaults to None).

        Returns:
            A list of resources matching the filters. Returns an empty list if an error
            occurs or no resources are found.
        """
        try:
            collection = self.db[COLLECTIONS["resources"]]
            # `filters or {}` provides an empty filter if None is passed, returning all documents
            # `{"_id": 0}` excludes the _id field
            return list(collection.find(filters or {}, {"_id": 0}))
        except Exception as e:
            print(f"Error getting resources: {e}")
            return []

    def get_user_progress(self, user_id):
        """
        Retrieves the learning progress (quiz results) for a specific user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of quiz results, sorted by timestamp in descending order.
            Returns an empty list if an error occurs or no progress is found.
        """
        try:
            collection = self.db[COLLECTIONS["quiz_results"]]
            # Find all quiz results for the user, sorted by most recent
            return list(collection.find(
                {"user_id": user_id}, # Filter by user_id
                {"_id": 0}            # Exclude _id
            ).sort("timestamp", -1))
        except Exception as e:
            print(f"Error getting user progress: {e}")
            return []

    def save_roadmap(self, user_id, path, steps):
        """
        Saves a generated learning roadmap for a user.

        Args:
            user_id: The ID of the user.
            path: The learning path or topic of the roadmap.
            steps: A list of steps or milestones in the roadmap.

        Returns:
            The result of the insert operation or None if an error occurs.
        """
        try:
            collection = self.db[COLLECTIONS["roadmaps"]]
            roadmap_data = {
                "user_id": user_id, # User associated with the roadmap
                "path": path,       # The topic/path of the roadmap (e.g., "Python Web Development")
                "steps": steps,     # The actual steps/content of the roadmap
                "timestamp": datetime.now() # Creation timestamp
            }
            return collection.insert_one(roadmap_data)
        except Exception as e:
            print(f"Error saving roadmap: {e}")
            return None
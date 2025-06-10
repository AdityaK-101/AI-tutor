import streamlit as st
import hashlib
import sqlite3
from datetime import datetime
import os
from pathlib import Path
import jwt
from streamlit.runtime.scriptrunner import get_script_run_ctx
import uuid
import json

class Auth:
    """
    Handles user authentication, session management, and database interactions for user data.

    This class manages user registration, login, logout, and stores user-specific data
    such as chat history, saved resources, quizzes, and learning roadmaps.
    It uses SQLite for database storage and JWT for session tokens.
    """
    def __init__(self):
        """
        Initializes the Auth class.

        Sets up the database path, secret key for JWT, initializes the database schema,
        and checks for existing session tokens to maintain user login state.
        """
        # Create database directory if it doesn't exist
        db_dir = Path("data")
        db_dir.mkdir(exist_ok=True)
        
        self.db_path = db_dir / "auth.db"
        self.secret_key = "your-secret-key"  # TODO: Use environment variable for production
        self.init_db()
        
        # Attempt to retrieve auth token from session state or query parameters
        # This allows maintaining session across browser refreshes if token is in URL
        if 'auth_token' not in st.session_state:
            st.session_state.auth_token = st.query_params.get('auth_token', None)
            
        # Initialize authentication status if not already set
        if 'authentication_status' not in st.session_state:
            if st.session_state.auth_token:
                # Verify the token if one exists
                username = self._verify_token(st.session_state.auth_token)
                if username:
                    # Token is valid, user is authenticated
                    st.session_state.authentication_status = True
                    st.session_state.username = username
                else:
                    # Token is invalid, clear auth status
                    st.session_state.authentication_status = None
                    st.session_state.username = None
            else:
                # No token, user is not authenticated
                st.session_state.authentication_status = None
                st.session_state.username = None
    
    def init_db(self):
        """
        Initializes the database schema.

        Creates tables for users, chats, chat messages, resources, quizzes, and roadmaps
        if they do not already exist.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (username TEXT PRIMARY KEY,
                     password TEXT,
                     created_at TIMESTAMP,
                     last_login TIMESTAMP)''')
        
        # Add chats table
        c.execute('''CREATE TABLE IF NOT EXISTS chats
                    (chat_id TEXT PRIMARY KEY,
                     username TEXT,
                     title TEXT,
                     created_at TIMESTAMP,
                     last_updated TIMESTAMP,
                     FOREIGN KEY (username) REFERENCES users(username))''')
        
        # Add chat_messages table
        c.execute('''CREATE TABLE IF NOT EXISTS chat_messages
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     chat_id TEXT,
                     role TEXT,
                     content TEXT,
                     timestamp TIMESTAMP,
                     FOREIGN KEY (chat_id) REFERENCES chats(chat_id))''')
        
        # Add resources table
        c.execute('''CREATE TABLE IF NOT EXISTS resources
                    (resource_id TEXT PRIMARY KEY,
                     username TEXT,
                     query TEXT,
                     content TEXT,
                     created_at TIMESTAMP,
                     FOREIGN KEY (username) REFERENCES users(username))''')
        
        # Add quizzes table
        # 'questions' stored as JSON string
        # 'submitted' is a boolean flag (0 or 1 in SQLite)
        c.execute('''CREATE TABLE IF NOT EXISTS quizzes
                    (quiz_id TEXT PRIMARY KEY,
                     username TEXT,
                     topic TEXT,
                     questions TEXT, # Stores JSON string of questions
                     score INTEGER,
                     submitted BOOLEAN,
                     created_at TIMESTAMP,
                     FOREIGN KEY (username) REFERENCES users(username))''')
        
        # Add roadmaps table
        # 'content' stores the markdown content of the roadmap
        c.execute('''CREATE TABLE IF NOT EXISTS roadmaps
                    (id TEXT PRIMARY KEY,
                     username TEXT,
                     topic TEXT,
                     content TEXT,
                     created_at TIMESTAMP,
                     FOREIGN KEY (username) REFERENCES users(username))''')
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str) -> str:
        """
        Hashes a password using SHA256.

        Args:
            password: The password string to hash.

        Returns:
            The hexadecimal representation of the hashed password.
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _create_token(self, username: str) -> str:
        """
        Creates a JWT token for the user.

        Args:
            username: The username to include in the token.

        Returns:
            A JWT token string.
        """
        return jwt.encode(
            {'username': username, 'exp': datetime.utcnow().timestamp() + 7*24*60*60},
            self.secret_key,
            algorithm='HS256'
        )
    
    def _verify_token(self, token: str) -> str:
        """
        Verifies a JWT token and returns the username if valid.

        Args:
            token: The JWT token string to verify.

        Returns:
            The username if the token is valid, otherwise None.
        """
        try:
            # Decode the token using the secret key and specified algorithm
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            # Check token expiration (handled by jwt.decode) and extract username
            return payload.get('username')
        except jwt.ExpiredSignatureError:
            # Handle expired token specifically if needed, though jwt.decode raises generic JWTError
            return None
        except jwt.InvalidTokenError:
            # Handle other invalid token errors
            return None
    
    def register(self, username: str, password: str) -> bool:
        """
        Registers a new user.

        Args:
            username: The username for the new user.
            password: The password for the new user.

        Returns:
            True if registration is successful, False otherwise (e.g., username already exists).
        """
        hashed_pwd = self._hash_password(password)
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
                     (username, hashed_pwd, datetime.now(), datetime.now()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError: # This error occurs if username (PRIMARY KEY) already exists
            return False
    
    def login(self, username: str, password: str) -> bool:
        """
        Logs in an existing user.

        Args:
            username: The username of the user.
            password: The password of the user.

        Returns:
            True if login is successful, False otherwise.
        """
        hashed_pwd = self._hash_password(password)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone() # Fetch the stored hashed password
        
        # Verify if user exists and password matches
        if result and result[0] == hashed_pwd:
            # Update last_login timestamp
            c.execute("UPDATE users SET last_login = ? WHERE username = ?",
                     (datetime.now(), username))
            conn.commit()
            conn.close() # Close connection after successful operations
            
            # Create a new JWT token for the session
            token = self._create_token(username)
            st.session_state.auth_token = token # Store token in session state
            st.query_params['auth_token'] = token # Optionally, put token in query params for shareable links/persistence
            
            # Set authentication status in session state
            st.session_state.authentication_status = True
            st.session_state.username = username
            
            # Load user's chat history (this might be better handled in the app logic)
            # Consider if loading all chat history on login is always necessary
            st.session_state.messages = self.get_chat_history(username) # This gets history for *all* chats of a user
            
            # Reset welcome screen flag so it shows up on new login
            st.session_state.welcome_shown = False
            
            return True # Login successful
        
        conn.close() # Ensure connection is closed on failure too
        st.session_state.authentication_status = False # Explicitly set auth status to False
        return False # Login failed
    
    def is_logged_in(self) -> bool:
        """
        Checks if a user is currently logged in.

        Returns:
            True if a user is logged in, False otherwise.
        """
        return st.session_state.authentication_status == True
    
    def logout(self):
        """
        Logs out the current user.

        Clears session state related to authentication and user information.
        """
        st.session_state.authentication_status = None
        st.session_state.username = None
        st.session_state.auth_token = None
        st.session_state.messages = []  # Clear messages on logout
        
        # Clear auth token from query params
        if 'auth_token' in st.query_params:
            del st.query_params['auth_token']
    
    def get_current_user(self) -> str:
        """
        Gets the username of the currently logged-in user.

        Returns:
            The username if a user is logged in, otherwise None.
        """
        return st.session_state.username if self.is_logged_in() else None

    def create_new_chat(self, username: str, title: str = "New Chat") -> str:
        """
        Creates a new chat for a user and returns its ID.

        Args:
            username: The username of the user creating the chat.
            title: The initial title for the chat (defaults to "New Chat").

        Returns:
            The unique ID of the newly created chat.
        """
        chat_id = str(uuid.uuid4()) # Generate a unique ID for the chat
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT INTO chats (chat_id, username, title, created_at, last_updated)
                     VALUES (?, ?, ?, ?, ?)""",
                 (chat_id, username, title, datetime.now(), datetime.now()))
        conn.commit()
        conn.close()
        return chat_id

    def get_user_chats(self, username: str):
        """
        Gets all chats for a specific user.

        Args:
            username: The username of the user.

        Returns:
            A list of dictionaries, where each dictionary represents a chat
            and contains 'id', 'title', and 'created_at'.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Fetches chats ordered by the most recently updated
        c.execute("""SELECT chat_id, title, created_at 
                     FROM chats 
                     WHERE username = ? 
                     ORDER BY last_updated DESC""", (username,))
        # Convert list of tuples from DB into list of dicts for easier use
        chats = [{"id": chat_id, "title": title, "created_at": created_at} 
                 for chat_id, title, created_at in c.fetchall()]
        conn.close()
        return chats

    def save_message(self, chat_id: str, role: str, content: str):
        """
        Saves a chat message to the database.

        Args:
            chat_id: The ID of the chat to save the message to.
            role: The role of the message sender (e.g., "user", "assistant").
            content: The content of the message.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now() # Timestamp for the message
        c.execute("""INSERT INTO chat_messages (chat_id, role, content, timestamp)
                     VALUES (?, ?, ?, ?)""",
                 (chat_id, role, content, now))
        # Update the last_updated timestamp of the parent chat
        c.execute("UPDATE chats SET last_updated = ? WHERE chat_id = ?",
                 (now, chat_id))
        conn.commit()
        conn.close()

    def get_chat_history(self, chat_id: str):
        """
        Gets the message history for a specific chat.

        Args:
            chat_id: The ID of the chat.

        Returns:
            A list of dictionaries, where each dictionary represents a message
            and contains 'role' and 'content'. Returns an empty list on error.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            # Retrieve messages ordered by timestamp to maintain conversation flow
            c.execute("""SELECT role, content FROM chat_messages 
                         WHERE chat_id = ? 
                         ORDER BY timestamp ASC""", (chat_id,))
            messages = [{"role": role, "content": content} for role, content in c.fetchall()]
            return messages
        except Exception as e:
            # Log the error for debugging
            print(f"Error retrieving chat history for chat_id {chat_id}: {e}")
            return [] # Return empty list on error to prevent app crashes
        finally:
            if conn:
                conn.close()

    def update_chat_title(self, chat_id: str, new_title: str):
        """
        Updates the title of a chat.

        Args:
            chat_id: The ID of the chat to update.
            new_title: The new title for the chat.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("UPDATE chats SET title = ? WHERE chat_id = ?", (new_title, chat_id))
            conn.commit()
        except Exception as e:
            print(f"Error updating chat title: {e}")
        finally:
            if conn:
                conn.close()

    def delete_chat(self, chat_id: str):
        """
        Deletes a chat and all its associated messages.

        Args:
            chat_id: The ID of the chat to delete.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            # Delete messages first due to foreign key constraint
            c.execute("DELETE FROM chat_messages WHERE chat_id = ?", (chat_id,))
            c.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
            conn.commit()
        finally:
            conn.close()

    def generate_chat_title(self, chat_id: str) -> str:
        """
        Generates a concise title based on the first user message in a chat.

        Args:
            chat_id: The ID of the chat.

        Returns:
            The generated title, or "New Chat" if no suitable title can be generated.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            # Get the first user message from the chat
            c.execute("""SELECT content FROM chat_messages 
                        WHERE chat_id = ? AND role = 'user' 
                        ORDER BY timestamp ASC LIMIT 1""", (chat_id,))
            result = c.fetchone()
            if result:
                message = result[0].strip() # Get the message content
                
                # Heuristic to generate a title:
                # If the message contains a question mark, use the first part of the question.
                # Otherwise, use the first few words of the message.
                if "?" in message:
                    # Extract the first question part
                    questions = [q.strip() for q in message.split("?") if q.strip()]
                    if questions:
                        title_words = questions[0].split()[:6] # Limit to first 6 words
                        title = " ".join(title_words)
                        if len(title) > 30: # Truncate if too long
                            title = title[:30] + "..."
                        title += "?" # Add question mark back if it was part of the title
                else:
                    # Use the first few words of the message
                    words = message.split()
                    title = " ".join(words[:6]) # Limit to first 6 words
                    if len(title) > 30: # Truncate if too long
                        title = title[:30] + "..."
                
                # Update the chat title in the database
                c.execute("UPDATE chats SET title = ? WHERE chat_id = ?", (title, chat_id))
                conn.commit()
                return title
            return "New Chat" # Default title if no message found or other issue
        finally:
            conn.close()

    def save_resource(self, username: str, query: str, content: str) -> str:
        """
        Saves a resource found by a user and returns its ID.

        Args:
            username: The username of the user saving the resource.
            query: The search query that led to the resource.
            content: The content of the resource.

        Returns:
            The unique ID of the saved resource.
        """
        resource_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT INTO resources (resource_id, username, query, content, created_at)
                     VALUES (?, ?, ?, ?, ?)""",
                 (resource_id, username, query, content, datetime.now()))
        conn.commit()
        conn.close()
        return resource_id

    def get_user_resources(self, username: str):
        """
        Gets all resources saved by a specific user.

        Args:
            username: The username of the user.

        Returns:
            A list of dictionaries, where each dictionary represents a resource
            and contains 'id', 'query', and 'created_at'.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT resource_id, query, created_at 
                     FROM resources 
                     WHERE username = ? 
                     ORDER BY created_at DESC""", (username,))
        resources = [{"id": resource_id, "query": query, "created_at": created_at} 
                     for resource_id, query, created_at in c.fetchall()]
        conn.close()
        return resources

    def get_resource_content(self, resource_id: str):
        """
        Gets the content of a specific resource.

        Args:
            resource_id: The ID of the resource.

        Returns:
            The content of the resource, or None if not found.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT content FROM resources WHERE resource_id = ?", (resource_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def delete_resource(self, resource_id: str):
        """
        Deletes a specific resource.

        Args:
            resource_id: The ID of the resource to delete.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM resources WHERE resource_id = ?", (resource_id,))
        conn.commit()
        conn.close()

    def save_quiz(self, username: str, quiz_data: dict) -> str:
        """
        Saves a quiz taken by a user and returns its ID.

        Args:
            username: The username of the user who took the quiz.
            quiz_data: A dictionary containing quiz details like 'topic', 'questions',
                       'score', and 'submitted' status.

        Returns:
            The unique ID of the saved quiz.
        """
        quiz_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Questions are stored as a JSON string in the database
        questions_json = json.dumps(quiz_data["questions"])
        
        c.execute("""INSERT INTO quizzes 
                     (quiz_id, username, topic, questions, score, submitted, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                 (quiz_id, username, quiz_data["topic"], questions_json, 
                  quiz_data.get("score", 0), # Default score to 0 if not provided
                  quiz_data.get("submitted", False), # Default submitted to False
                  datetime.now()))
        conn.commit()
        conn.close()
        return quiz_id

    def get_user_quizzes(self, username: str):
        """
        Gets all quizzes taken by a specific user.

        Args:
            username: The username of the user.

        Returns:
            A list of dictionaries, where each dictionary represents a quiz
            and contains 'id', 'topic', 'score', 'submitted', and 'created_at'.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT quiz_id, topic, score, submitted, created_at 
                     FROM quizzes 
                     WHERE username = ? 
                     ORDER BY created_at DESC""", (username,))
        quizzes = [{"id": quiz_id, "topic": topic, "score": score, 
                    "submitted": submitted, "created_at": created_at} 
                   for quiz_id, topic, score, submitted, created_at in c.fetchall()]
        conn.close()
        return quizzes

    def get_quiz(self, quiz_id: str):
        """
        Gets a specific quiz, including its questions.

        Args:
            quiz_id: The ID of the quiz.

        Returns:
            A dictionary containing quiz details ('topic', 'questions', 'score', 'submitted'),
            or None if the quiz is not found.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT topic, questions, score, submitted 
                     FROM quizzes WHERE quiz_id = ?""", (quiz_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            topic, questions_json, score, submitted = result
            # Deserialize the JSON string of questions back into a list/dict
            return {
                "topic": topic,
                "questions": json.loads(questions_json),
                "score": score,
                "submitted": submitted
            }
        return None # Return None if quiz_id not found

    def update_quiz_score(self, quiz_id: str, score: int):
        """
        Updates the score of a quiz and marks it as submitted.

        Args:
            quiz_id: The ID of the quiz to update.
            score: The score achieved in the quiz.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""UPDATE quizzes 
                     SET score = ?, submitted = TRUE 
                     WHERE quiz_id = ?""", (score, quiz_id))
        conn.commit()
        conn.close()

    def delete_quiz(self, quiz_id: str):
        """
        Deletes a specific quiz.

        Args:
            quiz_id: The ID of the quiz to delete.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM quizzes WHERE quiz_id = ?", (quiz_id,))
        conn.commit()
        conn.close()

    def get_user_roadmaps(self, username):
        """
        Gets all learning roadmaps for a specific user.

        Args:
            username: The username of the user.

        Returns:
            A list of dictionaries, where each dictionary represents a roadmap
            and contains 'id', 'topic', and 'created_at'.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT id, topic, created_at FROM roadmaps 
                     WHERE username = ? 
                     ORDER BY created_at DESC""", (username,))
        roadmaps = [{"id": id, "topic": topic, "created_at": created_at} 
                     for id, topic, created_at in c.fetchall()]
        conn.close()
        return roadmaps

    def get_roadmap(self, roadmap_id):
        """
        Gets a specific learning roadmap by its ID.

        Args:
            roadmap_id: The ID of the roadmap.

        Returns:
            A dictionary containing roadmap details ('id', 'topic', 'content', 'created_at'),
            or None if the roadmap is not found.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT id, topic, content, created_at FROM roadmaps 
                     WHERE id = ?""", (roadmap_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            id, topic, content, created_at = result
            return {
                "id": id,
                "topic": topic,
                "content": content,
                "created_at": created_at
            }
        return None

    def save_roadmap(self, username, roadmap):
        """
        Saves a new learning roadmap for a user.

        Args:
            username: The username of the user creating the roadmap.
            roadmap: A dictionary containing roadmap details ('topic', 'content', 'created_at').

        Returns:
            The unique ID of the newly saved roadmap.
        """
        # Generate a new UUID for the roadmap
        roadmap_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT INTO roadmaps (id, username, topic, content, created_at)
                     VALUES (?, ?, ?, ?, ?)""",
                 (roadmap_id, username, roadmap['topic'], roadmap['content'], roadmap['created_at']))
        conn.commit()
        conn.close()
        return roadmap_id

    def delete_roadmap(self, roadmap_id):
        """
        Deletes a specific learning roadmap.

        Args:
            roadmap_id: The ID of the roadmap to delete.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM roadmaps WHERE id = ?", (roadmap_id,))
        conn.commit()
        conn.close()

def login_page():
    """
    Displays the login and registration page.

    Handles user input for login and registration, interacts with the Auth class
    to authenticate or register users, and manages session state accordingly.

    Returns:
        True if the user is successfully logged in, False otherwise.
    """
        # Initialize Auth class to access login/register methods
    auth = Auth()
    
    # If user is already logged in (e.g., valid token in session), skip login page
    if auth.is_logged_in():
        return True
    
    st.title("AI Coding Tutor")
    
    # Use Streamlit tabs for a clean Login/Register UI
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    # Login Form
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password") # Mask password input
            submit = st.form_submit_button("Login")
            
            if submit:
                if auth.login(username, password):
                    st.success(f"Welcome, {username}! Login successful!")
                    st.session_state.welcome_shown = False  # Ensure welcome message is shown on new login
                    st.rerun() # Rerun the app to navigate past the login page
                else:
                    st.error("Invalid username or password")
    
    # Registration Form
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register = st.form_submit_button("Register")
            
            if register:
                # Basic client-side validation for password
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6: # Simple password length check
                    st.error("Password must be at least 6 characters long")
                else:
                    # Attempt to register the user
                    if auth.register(new_username, new_password):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists") # Handle existing username error
    
    return False # Return False if user is not logged in after attempting login/register
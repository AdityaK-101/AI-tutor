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
    def __init__(self):
        # Create database directory if it doesn't exist
        db_dir = Path("data")
        db_dir.mkdir(exist_ok=True)
        
        self.db_path = db_dir / "auth.db"
        self.secret_key = "your-secret-key"  # In production, use environment variable
        self.init_db()
        
        # Check for existing session token
        if 'auth_token' not in st.session_state:
            st.session_state.auth_token = st.query_params.get('auth_token', None)
            
        # Validate and set authentication status
        if 'authentication_status' not in st.session_state:
            if st.session_state.auth_token:
                username = self._verify_token(st.session_state.auth_token)
                if username:
                    st.session_state.authentication_status = True
                    st.session_state.username = username
                else:
                    st.session_state.authentication_status = None
                    st.session_state.username = None
            else:
                st.session_state.authentication_status = None
                st.session_state.username = None
    
    def init_db(self):
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
        c.execute('''CREATE TABLE IF NOT EXISTS quizzes
                    (quiz_id TEXT PRIMARY KEY,
                     username TEXT,
                     topic TEXT,
                     questions TEXT,
                     score INTEGER,
                     submitted BOOLEAN,
                     created_at TIMESTAMP,
                     FOREIGN KEY (username) REFERENCES users(username))''')
        
        # Add roadmaps table
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
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _create_token(self, username: str) -> str:
        """Create a JWT token for the user"""
        return jwt.encode(
            {'username': username, 'exp': datetime.utcnow().timestamp() + 7*24*60*60},
            self.secret_key,
            algorithm='HS256'
        )
    
    def _verify_token(self, token: str) -> str:
        """Verify JWT token and return username if valid"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload.get('username')
        except:
            return None
    
    def register(self, username: str, password: str) -> bool:
        hashed_pwd = self._hash_password(password)
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
                     (username, hashed_pwd, datetime.now(), datetime.now()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def login(self, username: str, password: str) -> bool:
        hashed_pwd = self._hash_password(password)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        
        if result and result[0] == hashed_pwd:
            # Update last login
            c.execute("UPDATE users SET last_login = ? WHERE username = ?",
                     (datetime.now(), username))
            conn.commit()
            conn.close()
            
            # Create and store auth token
            token = self._create_token(username)
            st.session_state.auth_token = token
            st.query_params['auth_token'] = token
            
            # Update session state
            st.session_state.authentication_status = True
            st.session_state.username = username
            
            # Load chat history
            st.session_state.messages = self.get_chat_history(username)
            
            # Reset welcome screen flag
            st.session_state.welcome_shown = False
            
            return True
        
        conn.close()
        st.session_state.authentication_status = False
        return False
    
    def is_logged_in(self) -> bool:
        return st.session_state.authentication_status == True
    
    def logout(self):
        st.session_state.authentication_status = None
        st.session_state.username = None
        st.session_state.auth_token = None
        st.session_state.messages = []  # Clear messages on logout
        
        # Clear auth token from query params
        if 'auth_token' in st.query_params:
            del st.query_params['auth_token']
    
    def get_current_user(self) -> str:
        return st.session_state.username if self.is_logged_in() else None

    def create_new_chat(self, username: str, title: str = "New Chat") -> str:
        """Create a new chat and return its ID"""
        chat_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT INTO chats (chat_id, username, title, created_at, last_updated)
                     VALUES (?, ?, ?, ?, ?)""",
                 (chat_id, username, title, datetime.now(), datetime.now()))
        conn.commit()
        conn.close()
        return chat_id

    def get_user_chats(self, username: str):
        """Get all chats for a user"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT chat_id, title, created_at 
                     FROM chats 
                     WHERE username = ? 
                     ORDER BY last_updated DESC""", (username,))
        chats = [{"id": chat_id, "title": title, "created_at": created_at} 
                 for chat_id, title, created_at in c.fetchall()]
        conn.close()
        return chats

    def save_message(self, chat_id: str, role: str, content: str):
        """Save a chat message to the database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now()
        c.execute("""INSERT INTO chat_messages (chat_id, role, content, timestamp)
                     VALUES (?, ?, ?, ?)""",
                 (chat_id, role, content, now))
        c.execute("UPDATE chats SET last_updated = ? WHERE chat_id = ?",
                 (now, chat_id))
        conn.commit()
        conn.close()

    def get_chat_history(self, chat_id: str):
        """Get messages for a specific chat"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""SELECT role, content FROM chat_messages 
                         WHERE chat_id = ? 
                         ORDER BY timestamp ASC""", (chat_id,))
            messages = [{"role": role, "content": content} for role, content in c.fetchall()]
            return messages
        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def update_chat_title(self, chat_id: str, new_title: str):
        """Update the title of a chat"""
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
        """Delete a chat and all its messages"""
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
        """Generate a concise title based on the first message in the chat"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            # Get the first user message
            c.execute("""SELECT content FROM chat_messages 
                        WHERE chat_id = ? AND role = 'user' 
                        ORDER BY timestamp ASC LIMIT 1""", (chat_id,))
            result = c.fetchone()
            if result:
                message = result[0].strip()
                
                # Try to extract a meaningful title
                # First, look for questions
                if "?" in message:
                    # Get the first question
                    questions = [q.strip() for q in message.split("?") if q.strip()]
                    if questions:
                        title = questions[0].split()[:6]  # First 6 words of the first question
                        title = " ".join(title)
                        if len(title) > 30:
                            title = title[:30] + "..."
                        title += "?"
                else:
                    # If no question, take the first few words
                    words = message.split()
                    title = " ".join(words[:6])  # First 6 words
                    if len(title) > 30:
                        title = title[:30] + "..."
                
                # Update the chat title
                c.execute("UPDATE chats SET title = ? WHERE chat_id = ?", (title, chat_id))
                conn.commit()
                return title
            return "New Chat"
        finally:
            conn.close()

    def save_resource(self, username: str, query: str, content: str) -> str:
        """Save a resource and return its ID"""
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
        """Get all resources for a user"""
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
        """Get content for a specific resource"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT content FROM resources WHERE resource_id = ?", (resource_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def delete_resource(self, resource_id: str):
        """Delete a resource"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM resources WHERE resource_id = ?", (resource_id,))
        conn.commit()
        conn.close()

    def save_quiz(self, username: str, quiz_data: dict) -> str:
        """Save a quiz and return its ID"""
        quiz_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Convert questions to JSON string
        questions_json = json.dumps(quiz_data["questions"])
        
        c.execute("""INSERT INTO quizzes 
                     (quiz_id, username, topic, questions, score, submitted, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                 (quiz_id, username, quiz_data["topic"], questions_json, 
                  quiz_data.get("score", 0), quiz_data.get("submitted", False),
                  datetime.now()))
        conn.commit()
        conn.close()
        return quiz_id

    def get_user_quizzes(self, username: str):
        """Get all quizzes for a user"""
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
        """Get a specific quiz with its questions"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT topic, questions, score, submitted 
                     FROM quizzes WHERE quiz_id = ?""", (quiz_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            topic, questions_json, score, submitted = result
            return {
                "topic": topic,
                "questions": json.loads(questions_json),
                "score": score,
                "submitted": submitted
            }
        return None

    def update_quiz_score(self, quiz_id: str, score: int):
        """Update quiz score and mark as submitted"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""UPDATE quizzes 
                     SET score = ?, submitted = TRUE 
                     WHERE quiz_id = ?""", (score, quiz_id))
        conn.commit()
        conn.close()

    def delete_quiz(self, quiz_id: str):
        """Delete a quiz"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM quizzes WHERE quiz_id = ?", (quiz_id,))
        conn.commit()
        conn.close()

    def get_user_roadmaps(self, username):
        """Get all roadmaps for a user"""
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
        """Get a specific roadmap by ID"""
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
        """Save a new roadmap"""
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
        """Delete a roadmap"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM roadmaps WHERE id = ?", (roadmap_id,))
        conn.commit()
        conn.close()

def login_page():
    # Initialize authentication
    auth = Auth()
    
    # If already logged in, return True
    if auth.is_logged_in():
        return True
    
    st.title("AI Coding Tutor")
    
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    # Login tab
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if auth.login(username, password):
                    st.success(f"Welcome, {username}! Login successful!")
                    st.session_state.welcome_shown = False  # Reset welcome screen flag
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    # Register tab
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register = st.form_submit_button("Register")
            
            if register:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    if auth.register(new_username, new_password):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists")
    
    return False 
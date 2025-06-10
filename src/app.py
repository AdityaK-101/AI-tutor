import streamlit as st
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.chat_interface import ChatInterface
from src.database import Database
from src.quiz_system import QuizSystem
from src.resource_finder import ResourceFinder
from src.roadmap_generator import RoadmapGenerator
from src.auth import Auth, login_page

def main():
    """
    Main function to run the AI Coding Tutor Streamlit application.

    Initializes authentication, sets up the page configuration,
    and handles navigation between different features of the application.
    """
    st.set_page_config(page_title="AI Coding Tutor", layout="wide")
    
    # Initialize authentication
    auth = Auth()
    
    # Show login page if not logged in. `login_page()` also handles registration.
    if not login_page():
        return # Stop further execution if login is not successful
    
    # Get current user
    username = auth.get_current_user()
    
    # Initialize session state variables if they don't exist
    # `messages` stores the chat history for the current chat session
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    # `current_quiz` stores the state of the quiz being taken
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    # `welcome_shown` flag to display the welcome message only once
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = False
    
    # Initialize core application components
    try:
        chat_interface = ChatInterface()
        db = Database()
        quiz_system = QuizSystem(db, chat_interface)
        resource_finder = ResourceFinder(db)
        roadmap_generator = RoadmapGenerator(db)
    except Exception as e:
        st.error(f"Error initializing components: {e}")
        return
    
    # Sidebar navigation
    with st.sidebar:
        # Add logout button
        if st.button("Logout"):
            auth.logout() # Perform logout operations (clear session, etc.)
            st.rerun() # Rerun the script to reflect the logged-out state
        
        st.subheader("Navigation")
        # Store the previous page to detect page changes
        previous_page = st.session_state.get('current_page')
        
        # Navigation buttons for different features
        st.write("Choose a feature:")
        
        # Using individual buttons for navigation for better UI control
        if st.button("Chat Assistant", use_container_width=True, key="nav_chat"):
            st.session_state.current_page = "Chat Assistant"
            st.rerun() # Rerun to load the selected page
        if st.button("Quiz System", use_container_width=True, key="nav_quiz"):
            st.session_state.current_page = "Quiz System"
            st.rerun()
        if st.button("Resource Finder", use_container_width=True, key="nav_resource"):
            st.session_state.current_page = "Resource Finder"
            st.rerun()
        if st.button("Learning Roadmap", use_container_width=True, key="nav_roadmap"):
            st.session_state.current_page = "Learning Roadmap"
            st.rerun()
        
        # Get the current page from session state (updated by button clicks)
        page = st.session_state.get('current_page')
        
        # Reset feature-specific states when switching between features
        # This ensures a clean state when navigating to a new feature
        if page != previous_page:
            if page == "Quiz System":
                # Reset quiz-related session variables
                st.session_state.current_quiz = None
                st.session_state.current_quiz_id = None
                st.session_state.creating_quiz = False
            elif page == "Learning Roadmap":
                # Reset roadmap-related session variables
                st.session_state.current_roadmap = None
                st.session_state.current_roadmap_id = None
                st.session_state.creating_roadmap = False
            
            # Only rerun if the page has actually changed to avoid unnecessary reruns
            if previous_page is not None:
                st.rerun()
    
    # Main content area: Display content based on the selected page
    # Show welcome message if it hasn't been shown yet
    if not st.session_state.welcome_shown:
        st.title("Welcome to AI Coding Tutor!")
        st.header(f"Hello, {username}!")
        st.markdown("Select a feature from the sidebar to get started.")
        st.session_state.welcome_shown = True
    elif page == "Chat Assistant":
        # Chat selection sidebar
        st.sidebar.subheader("Your Chats")
        
        # New chat button in the sidebar
        if st.sidebar.button("New Chat", key="new_chat_btn"):
            new_chat_id = auth.create_new_chat(username) # Create a new chat entry in the database
            st.session_state.current_chat_id = new_chat_id # Set the new chat as the current one
            st.session_state.messages = [] # Clear previous messages
            st.rerun()
        
        # Get user's existing chats
        chats = auth.get_user_chats(username)
        
        # Initialize current chat if it's not set and chats exist
        # Defaults to the most recent chat
        if 'current_chat_id' not in st.session_state and chats:
            st.session_state.current_chat_id = chats[0]["id"]
            st.session_state.messages = auth.get_chat_history(chats[0]["id"])
        elif not chats: # If the user has no chats
            # Create a new chat automatically if the user has no existing chats
            new_chat_id = auth.create_new_chat(username)
            st.session_state.current_chat_id = new_chat_id
            st.session_state.messages = []
        
        # Display list of user's chats in the sidebar
        for chat in chats:
            col1, col2 = st.sidebar.columns([4, 1]) # Columns for chat title and delete button
            with col1:
                # Truncate long chat titles for display consistency
                display_title = chat["title"]
                if len(display_title) > 25:  # Max length for display
                    display_title = display_title[:25] + "..."
                
                # Button to select a chat
                if st.button(
                    display_title,
                    key=f"chat_{chat['id']}", # Unique key for each chat button
                    use_container_width=True
                ):
                    st.session_state.current_chat_id = chat["id"] # Set selected chat as current
                    st.session_state.messages = auth.get_chat_history(chat["id"]) # Load its history
                    st.rerun()
            
            with col2:
                # Delete button for each chat
                if st.button("🗑️", key=f"delete_{chat['id']}"):
                    # If deleting the currently active chat, clear its state
                    if chat["id"] == st.session_state.current_chat_id:
                        st.session_state.current_chat_id = None
                        st.session_state.messages = []
                    auth.delete_chat(chat["id"]) # Delete chat from database
                    st.rerun()
        
        # Chat interface area
        if st.session_state.current_chat_id:
            # Find the current chat's details (primarily for title)
            current_chat = next(
                (c for c in chats if c["id"] == st.session_state.current_chat_id), 
                {"title": "New Chat"} # Default if chat somehow not found (should not happen)
            )
            
            # Display existing messages in the current chat
            for message in st.session_state.messages:
                with st.chat_message(message["role"]): # "user" or "assistant"
                    st.markdown(message["content"])
            
            # Chat input field for the user
            if prompt := st.chat_input("Ask your coding question"):
                # Display user's message immediately
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Save user message to database and session state
                auth.save_message(st.session_state.current_chat_id, "user", prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Get and display AI's response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."): # Show a loading spinner
                        # Prepare conversation history for the AI model
                        formatted_history = []
                        for msg in st.session_state.messages:
                            formatted_history.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })
                        
                        response = chat_interface.get_ai_response(prompt, formatted_history)
                        st.markdown(response)
                
                # Save AI response to database and session state
                auth.save_message(st.session_state.current_chat_id, "assistant", response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # If this is the first message in a "New Chat", generate a title for it
                if current_chat["title"] == "New Chat":
                    auth.generate_chat_title(st.session_state.current_chat_id)
                    st.rerun() # Rerun to update the chat title in the sidebar
    
    elif page == "Quiz System":
        # Quiz System Page
        st.sidebar.subheader("Your Quizzes")
        
        # Button to create a new quiz
        if st.sidebar.button("New Quiz", key="new_quiz_btn"):
            st.session_state.creating_quiz = True # Flag to show quiz creation UI
            st.session_state.current_quiz = None # Clear any existing quiz state
            st.session_state.current_quiz_id = None
            st.rerun()
        
        # Get user's saved quizzes
        quizzes = auth.get_user_quizzes(username)
        
        # Display saved quizzes in the sidebar
        for quiz in quizzes:
            col1, col2 = st.sidebar.columns([4, 1]) # Columns for quiz title and delete button
            with col1:
                # Display quiz topic and score if submitted
                display_title = f"{quiz['topic']}"
                if quiz['submitted']:
                    display_title += f" (Score: {quiz['score']})"
                
                # Button to load and view a saved quiz
                if st.button(
                    display_title,
                    key=f"quiz_{quiz['id']}", # Unique key
                    use_container_width=True
                ):
                    st.session_state.current_quiz = auth.get_quiz(quiz['id']) # Load quiz from DB
                    st.session_state.current_quiz_id = quiz['id']
                    st.session_state.creating_quiz = False # Not creating, but viewing
                    st.rerun()
            
            with col2:
                # Delete button for each quiz
                if st.button("🗑️", key=f"delete_quiz_{quiz['id']}"):
                    auth.delete_quiz(quiz['id'])
                    # If deleting the currently viewed quiz, clear its state
                    if 'current_quiz_id' in st.session_state and st.session_state.current_quiz_id == quiz['id']:
                        st.session_state.current_quiz = None
                        st.session_state.current_quiz_id = None
                    st.rerun()
        
        # Main content area for Quiz System
        if st.session_state.get('creating_quiz', False): # If 'New Quiz' was clicked
            st.title("Quiz System")
            st.subheader("Create New Quiz")
            
            # Options for quiz type: pre-made or custom generated
            quiz_type = st.radio(
                "Choose Quiz Type",
                ["Pre-made Quizzes", "Generate Custom Quiz"]
            )
            
            if quiz_type == "Pre-made Quizzes":
                topic = st.selectbox(
                    "Select a Topic",
                    ["Python Basics", "Data Structures", "Algorithms", "Object-Oriented Programming"]
                )
                if st.button("Start Quiz"):
                    # Initialize quiz structure for pre-made quiz
                    st.session_state.current_quiz = {
                        "topic": topic,
                        "questions": quiz_system._get_default_questions(topic), # Fetch default questions
                        "current_question": 0, # For potential step-by-step display (not fully used here)
                        "score": 0,
                        "submitted": False # Flag to track if quiz is submitted
                    }
                    # Save the newly started quiz to the database
                    quiz_id = auth.save_quiz(username, st.session_state.current_quiz)
                    st.session_state.current_quiz_id = quiz_id
                    st.session_state.creating_quiz = False # Done creating, now view/take quiz
                    st.rerun()
            else: # Generate Custom Quiz
                topic = st.text_input("Enter the topic for your quiz:")
                num_questions = st.slider("Number of questions", 1, 10, 5)
                difficulty = st.selectbox(
                    "Select difficulty",
                    ["Basic", "Beginner", "Intermediate", "Advanced"],
                    index=0 # Default to "Basic"
                )
                
                if st.button("Generate Quiz"):
                    if topic: # Ensure topic is provided
                        with st.spinner("Generating quiz questions..."):
                            questions = quiz_system._generate_quiz_questions(topic, num_questions, difficulty)
                            if questions:
                                # Initialize quiz structure for custom quiz
                                st.session_state.current_quiz = {
                                    "topic": topic,
                                    "questions": questions,
                                    "current_question": 0,
                                    "score": 0,
                                    "submitted": False
                                }
                                # Save the generated quiz to the database
                                quiz_id = auth.save_quiz(username, st.session_state.current_quiz)
                                st.session_state.current_quiz_id = quiz_id
                                st.session_state.creating_quiz = False
                                st.rerun()
        
        elif st.session_state.current_quiz: # If a quiz is loaded or created
            st.title(f"Quiz: {st.session_state.current_quiz['topic']}")
            quiz_system._display_quiz() # Delegate rendering the quiz to QuizSystem class
        else: # Default view for Quiz System if no quiz is active
            st.title("Quiz System")
            st.markdown("""
            Welcome to the Quiz System! Here you can:
            - Take pre-made quizzes
            - Generate custom quizzes
            - Track your quiz scores
            
            Click "New Quiz" in the sidebar to get started!
            """)
    
    elif page == "Resource Finder":
        # Delegate rendering to the ResourceFinder class
        resource_finder.render()
    
    elif page == "Learning Roadmap":
        # Learning Roadmap Page
        st.sidebar.subheader("Your Roadmaps")
        
        # Button to create a new roadmap
        if st.sidebar.button("New Roadmap", key="new_roadmap_btn"):
            st.session_state.creating_roadmap = True # Flag to show roadmap creation UI
            st.session_state.current_roadmap = None # Clear any existing roadmap state
            st.session_state.current_roadmap_id = None
            st.rerun()
        
        # Get user's saved roadmaps
        roadmaps = auth.get_user_roadmaps(username)
        
        # Display saved roadmaps in the sidebar
        for roadmap in roadmaps:
            col1, col2 = st.sidebar.columns([4, 1]) # Columns for roadmap topic and delete button
            with col1:
                # Button to load and view a saved roadmap
                if st.button(
                    roadmap['topic'],
                    key=f"roadmap_{roadmap['id']}", # Unique key
                    use_container_width=True
                ):
                    st.session_state.current_roadmap = auth.get_roadmap(roadmap['id']) # Load from DB
                    st.session_state.current_roadmap_id = roadmap['id']
                    st.session_state.creating_roadmap = False # Not creating, but viewing
                    st.rerun()
            
            with col2:
                # Delete button for each roadmap
                if st.button("🗑️", key=f"delete_roadmap_{roadmap['id']}"):
                    auth.delete_roadmap(roadmap['id'])
                    # If deleting the currently viewed roadmap, clear its state
                    if 'current_roadmap_id' in st.session_state and st.session_state.current_roadmap_id == roadmap['id']:
                        st.session_state.current_roadmap = None
                        st.session_state.current_roadmap_id = None
                    st.rerun()
        
        # Main content area for Learning Roadmap
        if st.session_state.get('creating_roadmap', False): # If 'New Roadmap' was clicked
            st.title("Learning Roadmap Generator")
            st.subheader("Create New Learning Roadmap")
            topic = st.text_input("What would you like to learn? (e.g., 'Python for web development')")
            
            if st.button("Generate Roadmap") and topic: # Ensure topic is provided
                with st.spinner("Generating your learning roadmap..."):
                    roadmap_content = roadmap_generator.generate_roadmap(topic) # Generate content
                    # Initialize roadmap structure
                    new_roadmap = {
                        "topic": topic,
                        "content": roadmap_content,
                        "created_at": datetime.now() # Timestamp
                    }
                    # Save the new roadmap to the database
                    roadmap_id = auth.save_roadmap(username, new_roadmap)
                    
                    # Update the roadmap object with the ID from the database for consistency
                    new_roadmap["id"] = roadmap_id
                    st.session_state.current_roadmap = new_roadmap # Set as current
                    st.session_state.current_roadmap_id = roadmap_id
                    st.session_state.creating_roadmap = False # Done creating
                    st.rerun()
        
        elif st.session_state.get('current_roadmap'): # If a roadmap is loaded or created
            st.title(st.session_state.current_roadmap['topic'])
            st.markdown(st.session_state.current_roadmap['content']) # Display its content
        else: # Default view for Learning Roadmap if no roadmap is active
            st.title("Learning Roadmap Generator")
            st.markdown("""
            Welcome to the Learning Roadmap Generator! Here you can:
            - Create personalized learning roadmaps
            - Save and manage your roadmaps
            - Track your learning progress
            
            Click "New Roadmap" in the sidebar to get started!
            """)

if __name__ == "__main__":
    main() 
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
    st.set_page_config(page_title="AI Coding Tutor", layout="wide")
    
    # Initialize authentication
    auth = Auth()
    
    # Show login page if not logged in
    if not login_page():
        return
    
    # Get current user
    username = auth.get_current_user()
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = False
    
    # Initialize components
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
            auth.logout()
            st.rerun()
        
        st.subheader("Navigation")
        previous_page = st.session_state.get('current_page')
        
        # Replace radio buttons with individual buttons
        st.write("Choose a feature:")
        
        # Use a single column for all buttons
        if st.button("Chat Assistant", use_container_width=True):
            page = "Chat Assistant"
        if st.button("Quiz System", use_container_width=True):
            page = "Quiz System"
        if st.button("Resource Finder", use_container_width=True):
            page = "Resource Finder"
        if st.button("Learning Roadmap", use_container_width=True):
            page = "Learning Roadmap"
        
        # If no button was clicked, use the previous page or None
        if 'page' not in locals():
            page = previous_page
        
        # Reset states when switching features
        if page != previous_page:
            if page == "Quiz System":
                st.session_state.current_quiz = None
                st.session_state.current_quiz_id = None
                st.session_state.creating_quiz = False
            elif page == "Learning Roadmap":
                st.session_state.current_roadmap = None
                st.session_state.current_roadmap_id = None
                st.session_state.creating_roadmap = False
            
            st.session_state.current_page = page
            
            if previous_page is not None:  # Only rerun if actually switching pages
                st.rerun()
    
    # Main content area
    if not st.session_state.welcome_shown:
        st.title("Welcome to AI Coding Tutor!")
        st.header(f"Hello, {username}!")
        st.markdown("Select a feature from the sidebar to get started.")
        st.session_state.welcome_shown = True
    elif page == "Chat Assistant":
        # Chat selection sidebar
        st.sidebar.subheader("Your Chats")
        
        # New chat button
        if st.sidebar.button("New Chat", key="new_chat_btn"):
            new_chat_id = auth.create_new_chat(username)
            st.session_state.current_chat_id = new_chat_id
            st.session_state.messages = []
            st.rerun()
        
        # Get user's chats
        chats = auth.get_user_chats(username)
        
        # Initialize current chat if needed
        if 'current_chat_id' not in st.session_state and chats:
            st.session_state.current_chat_id = chats[0]["id"]
            st.session_state.messages = auth.get_chat_history(chats[0]["id"])
        elif not chats:
            # Create first chat if user has none
            new_chat_id = auth.create_new_chat(username)
            st.session_state.current_chat_id = new_chat_id
            st.session_state.messages = []
        
        # Chat selection with delete buttons
        for chat in chats:
            col1, col2 = st.sidebar.columns([4, 1])
            with col1:
                # Truncate title if needed to keep button size consistent
                display_title = chat["title"]
                if len(display_title) > 25:  # Adjust this number as needed
                    display_title = display_title[:25] + "..."
                
                if st.button(
                    display_title,
                    key=f"chat_{chat['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_chat_id = chat["id"]
                    st.session_state.messages = auth.get_chat_history(chat["id"])
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_{chat['id']}"):
                    if chat["id"] == st.session_state.current_chat_id:
                        st.session_state.current_chat_id = None
                        st.session_state.messages = []
                    auth.delete_chat(chat["id"])
                    st.rerun()
        
        # Chat interface
        if st.session_state.current_chat_id:
            current_chat = next(
                (c for c in chats if c["id"] == st.session_state.current_chat_id), 
                {"title": "New Chat"}
            )
            
            # Display messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            if prompt := st.chat_input("Ask your coding question"):
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Save user message
                auth.save_message(st.session_state.current_chat_id, "user", prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Get and display AI response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = chat_interface.get_ai_response(prompt, st.session_state.messages)
                        st.markdown(response)
                
                # Save AI response
                auth.save_message(st.session_state.current_chat_id, "assistant", response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Generate title from first message if it's a new chat
                if current_chat["title"] == "New Chat":
                    auth.generate_chat_title(st.session_state.current_chat_id)
                    st.rerun()
    
    elif page == "Quiz System":
        # Quiz selection sidebar
        st.sidebar.subheader("Your Quizzes")
        
        # New quiz button
        if st.sidebar.button("New Quiz", key="new_quiz_btn"):
            st.session_state.creating_quiz = True
            st.session_state.current_quiz = None
            st.session_state.current_quiz_id = None
            st.rerun()
        
        # Get user's quizzes
        quizzes = auth.get_user_quizzes(username)
        
        # Display saved quizzes
        for quiz in quizzes:
            col1, col2 = st.sidebar.columns([4, 1])
            with col1:
                # Show quiz topic with score if submitted
                display_title = f"{quiz['topic']}"
                if quiz['submitted']:
                    display_title += f" (Score: {quiz['score']})"
                
                if st.button(
                    display_title,
                    key=f"quiz_{quiz['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_quiz = auth.get_quiz(quiz['id'])
                    st.session_state.current_quiz_id = quiz['id']
                    st.session_state.creating_quiz = False
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_quiz_{quiz['id']}"):
                    auth.delete_quiz(quiz['id'])
                    if 'current_quiz_id' in st.session_state and st.session_state.current_quiz_id == quiz['id']:
                        st.session_state.current_quiz = None
                        st.session_state.current_quiz_id = None
                    st.rerun()
        
        # Main content area
        if st.session_state.get('creating_quiz', False):
            st.title("Quiz System")
            st.subheader("Create New Quiz")
            
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
                    st.session_state.current_quiz = {
                        "topic": topic,
                        "questions": quiz_system._get_default_questions(topic),
                        "current_question": 0,
                        "score": 0,
                        "submitted": False
                    }
                    # Save to database
                    quiz_id = auth.save_quiz(username, st.session_state.current_quiz)
                    st.session_state.current_quiz_id = quiz_id
                    st.session_state.creating_quiz = False
                    st.rerun()
            else:
                topic = st.text_input("Enter the topic for your quiz:")
                num_questions = st.slider("Number of questions", 1, 10, 5)
                difficulty = st.selectbox(
                    "Select difficulty",
                    ["Basic", "Beginner", "Intermediate", "Advanced"],
                    index=0
                )
                
                if st.button("Generate Quiz"):
                    if topic:
                        with st.spinner("Generating quiz questions..."):
                            questions = quiz_system._generate_quiz_questions(topic, num_questions, difficulty)
                            if questions:
                                st.session_state.current_quiz = {
                                    "topic": topic,
                                    "questions": questions,
                                    "current_question": 0,
                                    "score": 0,
                                    "submitted": False
                                }
                                # Save to database
                                quiz_id = auth.save_quiz(username, st.session_state.current_quiz)
                                st.session_state.current_quiz_id = quiz_id
                                st.session_state.creating_quiz = False
                                st.rerun()
        
        elif st.session_state.current_quiz:
            st.title(f"Quiz: {st.session_state.current_quiz['topic']}")
            quiz_system._display_quiz()
        else:
            st.title("Quiz System")
            st.markdown("""
            Welcome to the Quiz System! Here you can:
            - Take pre-made quizzes
            - Generate custom quizzes
            - Track your quiz scores
            
            Click "New Quiz" in the sidebar to get started!
            """)
    
    elif page == "Resource Finder":
        resource_finder.render()
    
    elif page == "Learning Roadmap":
        # Roadmap selection sidebar
        st.sidebar.subheader("Your Roadmaps")
        
        # New roadmap button
        if st.sidebar.button("New Roadmap", key="new_roadmap_btn"):
            st.session_state.creating_roadmap = True
            st.session_state.current_roadmap = None
            st.session_state.current_roadmap_id = None
            st.rerun()
        
        # Get user's roadmaps
        roadmaps = auth.get_user_roadmaps(username)
        
        # Display saved roadmaps
        for roadmap in roadmaps:
            col1, col2 = st.sidebar.columns([4, 1])
            with col1:
                if st.button(
                    roadmap['topic'],
                    key=f"roadmap_{roadmap['id']}",
                    use_container_width=True
                ):
                    st.session_state.current_roadmap = auth.get_roadmap(roadmap['id'])
                    st.session_state.current_roadmap_id = roadmap['id']
                    st.session_state.creating_roadmap = False
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_roadmap_{roadmap['id']}"):
                    auth.delete_roadmap(roadmap['id'])
                    if 'current_roadmap_id' in st.session_state and st.session_state.current_roadmap_id == roadmap['id']:
                        st.session_state.current_roadmap = None
                        st.session_state.current_roadmap_id = None
                    st.rerun()
        
        # Main content area
        if st.session_state.get('creating_roadmap', False):
            st.title("Learning Roadmap Generator")
            st.subheader("Create New Learning Roadmap")
            topic = st.text_input("What would you like to learn? (e.g., 'Python for web development')")
            
            if st.button("Generate Roadmap") and topic:
                with st.spinner("Generating your learning roadmap..."):
                    roadmap_content = roadmap_generator.generate_roadmap(topic)
                    new_roadmap = {
                        "topic": topic,
                        "content": roadmap_content,
                        "created_at": datetime.now()
                    }
                    # Save to database
                    roadmap_id = auth.save_roadmap(username, new_roadmap)
                    
                    # Update the roadmap with the generated ID
                    new_roadmap["id"] = roadmap_id
                    st.session_state.current_roadmap = new_roadmap
                    st.session_state.current_roadmap_id = roadmap_id
                    st.session_state.creating_roadmap = False
                    st.rerun()
        
        elif st.session_state.get('current_roadmap'):
            st.title(st.session_state.current_roadmap['topic'])
            st.markdown(st.session_state.current_roadmap['content'])
        else:
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
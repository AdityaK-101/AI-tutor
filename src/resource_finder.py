import streamlit as st
from typing import List, Dict
import json
import uuid

class ResourceFinder:
    """
    Provides functionality for finding and displaying learning resources.

    This class allows users to search for learning materials based on a query.
    It uses an AI chat interface to generate explanations and resource links,
    and interacts with the database to save and retrieve user-specific resources.
    The UI is rendered using Streamlit.
    """
    def __init__(self, db):
        """
        Initializes the ResourceFinder.

        Args:
            db: An instance of the Database class for database interactions.
                This also provides access to chat_interface and auth instances.
        """
        self.db = db
        self.chat_interface = self.db.chat_interface
        self.auth = self.db.auth # Access Auth methods for user-specific data

    def generate_resources(self, query: str) -> Dict:
        """
        Generates learning resources based on a user's query using an AI model.

        Constructs a prompt for the AI to provide a detailed explanation, key learning points,
        code examples (if applicable), and links to various types of resources.

        Args:
            query: The user's learning topic or question.

        Returns:
            A dictionary or string (depending on AI response format) containing the
            generated resources and explanations.
        """
        # This prompt is structured to guide the AI in generating a comprehensive
        # and well-organized response that includes both explanations and external links.
        prompt = f"""Given the learning topic or question: "{query}"
        Provide a detailed explanation and resources in the following format:

        1. Quick Overview:
           [Provide a brief, direct explanation of the concept/topic]

        2. Key Learning Points:
           [List the main points to understand about this topic]

        3. Code Examples (if applicable):
           [Provide practical code examples with explanations, preferably in Python if not specified]

        4. Recommended Resources:
           - Direct Links to Documentation: [Include specific URLs to official documentation or key pages]
           - Tutorial Links: [Include specific URLs to relevant tutorials, articles, or blog posts]
           - Video Resources: [Include direct YouTube links or links to other video platforms if relevant]
           - Practice Exercises: [Include direct links to coding exercises, platforms like LeetCode, HackerRank, or specific problem sets]

        Make the response self-contained so users can learn directly from it, while also providing specific links for deeper learning.
        Ensure all links are functional and directly relevant to the sub-topic.
        """
        
        # Call the AI to get the response based on the structured prompt
        response = self.chat_interface.get_ai_response(prompt)
        return response

    def render(self):
        """
        Renders the Resource Finder interface using Streamlit.

        This method sets up the UI with tabs for finding new resources and viewing
        saved resources. It handles user input for search queries, displays AI-generated
        content, and allows users to save or delete resources.
        """
        st.title("Resource Finder")
        
        # Get the current logged-in user's username
        username = st.session_state.username # Assumes username is in session_state
        
        # Initialize session state variables for this feature if they don't exist
        if 'resource_content' not in st.session_state: # Stores the currently generated/displayed resource
            st.session_state.resource_content = None
        if 'last_query' not in st.session_state: # Stores the last search query made by the user
            st.session_state.last_query = ""
        if 'selected_resource_id' not in st.session_state: # ID of the resource selected from saved list
            st.session_state.selected_resource_content = None
            st.session_state.selected_resource_id = None

        # Create two tabs: one for finding new resources, one for viewing saved resources
        tab1, tab2 = st.tabs(["Find Resources", "Saved Resources"])
        
        # "Find Resources" tab
        with tab1:
            # Chat input for the user to enter their learning query
            if query_prompt := st.chat_input("What would you like to learn about?"):
                with st.spinner("Generating personalized learning resources..."):
                    # Generate resources using the AI
                    generated_content = self.generate_resources(query_prompt)
                    # Store the generated content and the query in session state
                    st.session_state.resource_content = generated_content
                    st.session_state.last_query = query_prompt
                    st.rerun() # Rerun to display the new content
            
            # Display the generated resource content if it exists
            if st.session_state.resource_content:
                st.markdown(st.session_state.resource_content) # Display as Markdown
                
                # Buttons for saving the current resource or starting a new search
                col1, col2 = st.columns([1, 5]) # Adjust column ratio as needed
                with col1:
                    if st.button("Save Resource", key="save_current_resource"):
                        # Use the last query as the title for the saved resource, or a default
                        resource_title = st.session_state.get('last_query', 'Saved Resource')
                        # Save the resource to the database via the Auth class instance
                        self.auth.save_resource(username, resource_title, st.session_state.resource_content)
                        st.success("Resource saved successfully!")
                with col2:
                    if st.button("New Search", key="clear_resource"):
                        # Clear the current resource content to allow a new search
                        st.session_state.resource_content = None
                        st.session_state.last_query = ""
                        st.rerun()
        
        # "Saved Resources" tab
        with tab2:
            # Retrieve and display resources saved by the current user
            saved_resources = self.auth.get_user_resources(username)
            
            if not saved_resources:
                st.info("You haven't saved any resources yet.")
            else:
                st.subheader("Your Saved Resources")
                
                # Iterate through saved resources and display them as buttons
                for resource_item in saved_resources:
                    # Truncate long titles for display
                    display_title = resource_item["query"]
                    if len(display_title) > 40: # Max length for button label
                        display_title = display_title[:40] + "..."
                    
                    col1, col2 = st.columns([4, 1]) # Columns for resource title and delete button
                    with col1:
                        # Button to view the content of a saved resource
                        if st.button(
                            display_title, 
                            key=f"resource_{resource_item['id']}", # Unique key for each button
                            use_container_width=True
                        ):
                            # Load the full content of the selected resource
                            full_content = self.auth.get_resource_content(resource_item["id"])
                            if full_content:
                                # Store content and ID in session state to display it
                                st.session_state.selected_resource_content = full_content
                                st.session_state.selected_resource_id = resource_item["id"]
                                st.rerun() # Rerun to display the selected saved resource
                    
                    with col2:
                        # Button to delete a saved resource
                        if st.button("🗑️", key=f"delete_resource_{resource_item['id']}"):
                            self.auth.delete_resource(resource_item["id"])
                            # If the deleted resource was being viewed, clear its content
                            if "selected_resource_id" in st.session_state and \
                               st.session_state.selected_resource_id == resource_item["id"]:
                                st.session_state.selected_resource_content = None
                                st.session_state.selected_resource_id = None
                            st.rerun() # Rerun to reflect the deletion
                
                # Display the content of the selected saved resource
                if "selected_resource_content" in st.session_state and st.session_state.selected_resource_content:
                    st.markdown("---") # Separator
                    st.markdown(st.session_state.selected_resource_content)

    def _display_resources(self, resources):
        """
        Displays a list of resources in an expandable format. (Currently not directly used by render but kept for potential future use)

        Args:
            resources: A list of resource dictionaries, where each dictionary
                       contains details like 'title', 'type', 'difficulty', 'topics', and 'url'.
        """
        if not resources:
            st.warning("No resources found matching your criteria.")
            return
        
        for resource in resources:
            with st.expander(resource["title"]):
                st.write(f"**Type:** {resource['type'].title()}")
                st.write(f"**Difficulty:** {resource['difficulty'].title()}")
                st.write(f"**Topics:** {', '.join(resource['topics'])}")
                st.write(f"**URL:** [{resource['url']}]({resource['url']})") 
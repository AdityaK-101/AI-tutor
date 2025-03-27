import streamlit as st
from typing import List, Dict
import json
import uuid

class ResourceFinder:
    def __init__(self, db):
        self.db = db
        self.chat_interface = self.db.chat_interface
        self.auth = self.db.auth

    def generate_resources(self, query: str) -> Dict:
        """Generate resources based on user query using AI"""
        prompt = f"""Given the learning topic or question: "{query}"
        Provide a detailed explanation and resources in the following format:

        1. Quick Overview:
           [Provide a brief, direct explanation of the concept/topic]

        2. Key Learning Points:
           [List the main points to understand about this topic]

        3. Code Examples (if applicable):
           [Provide practical code examples with explanations]

        4. Recommended Resources:
           - Direct Links to Documentation: [Include specific URLs]
           - Tutorial Links: [Include specific URLs to relevant tutorials]
           - Video Resources: [Include direct YouTube links if relevant]
           - Practice Exercises: [Include direct links to coding exercises/platforms]

        Make the response self-contained so users can learn directly from it, while also providing specific links for deeper learning.
        """
        
        response = self.chat_interface.get_ai_response(prompt)
        return response

    def render(self):
        st.title("Resource Finder")
        
        # Get current user
        username = st.session_state.username
        
        # Initialize session state for resources if not exists
        if 'resource_content' not in st.session_state:
            st.session_state.resource_content = None
        
        # Create tabs for search and saved resources
        tab1, tab2 = st.tabs(["Find Resources", "Saved Resources"])
        
        with tab1:
            # Input at the top, just below the title
            if prompt := st.chat_input("What would you like to learn about?"):
                with st.spinner("Generating personalized learning resources..."):
                    resources = self.generate_resources(prompt)
                    st.session_state.resource_content = resources
                    st.session_state.last_query = prompt
                    st.rerun()
            
            # Display content below the input
            if st.session_state.resource_content:
                st.markdown(st.session_state.resource_content)
                
                # Save button
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("Save Resource", key="save_current_resource"):
                        query = st.session_state.get('last_query', 'Saved Resource')
                        self.auth.save_resource(username, query, st.session_state.resource_content)
                        st.success("Resource saved successfully!")
                with col2:
                    if st.button("New Search", key="clear_resource"):
                        st.session_state.resource_content = None
                        st.rerun()
        
        with tab2:
            # Display saved resources
            saved_resources = self.auth.get_user_resources(username)
            
            if not saved_resources:
                st.info("You haven't saved any resources yet.")
            else:
                st.subheader("Your Saved Resources")
                
                # Display resources in a scrollable area
                for resource in saved_resources:
                    # Truncate title if needed
                    display_title = resource["query"]
                    if len(display_title) > 40:
                        display_title = display_title[:40] + "..."
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if st.button(
                            display_title, 
                            key=f"resource_{resource['id']}", 
                            use_container_width=True
                        ):
                            content = self.auth.get_resource_content(resource["id"])
                            if content:
                                st.session_state.selected_resource_content = content
                                st.session_state.selected_resource_id = resource["id"]
                                st.rerun()
                    
                    with col2:
                        if st.button("🗑️", key=f"delete_resource_{resource['id']}"):
                            self.auth.delete_resource(resource["id"])
                            if "selected_resource_id" in st.session_state and st.session_state.selected_resource_id == resource["id"]:
                                st.session_state.selected_resource_content = None
                                st.session_state.selected_resource_id = None
                            st.rerun()
                
                # Display selected resource
                if "selected_resource_content" in st.session_state and st.session_state.selected_resource_content:
                    st.markdown("---")
                    st.markdown(st.session_state.selected_resource_content)

    def _display_resources(self, resources):
        if not resources:
            st.warning("No resources found matching your criteria.")
            return
        
        for resource in resources:
            with st.expander(resource["title"]):
                st.write(f"**Type:** {resource['type'].title()}")
                st.write(f"**Difficulty:** {resource['difficulty'].title()}")
                st.write(f"**Topics:** {', '.join(resource['topics'])}")
                st.write(f"**URL:** [{resource['url']}]({resource['url']})") 
# AI Coding Tutor

## Overview

The AI Coding Tutor is a Streamlit web application designed to assist users in their coding journey. It provides various tools and features to help users learn, practice, and get answers to their coding-related questions. The application leverages AI capabilities for generating responses, quizzes, and learning roadmaps.

## Features

- **Chat Assistant:** Allows users to interact with an AI tutor to ask coding questions, get explanations, and receive guidance on programming concepts.
- **Quiz System:** Offers pre-made quizzes on various topics and allows users to generate custom quizzes to test their knowledge.
- **Resource Finder:** Helps users discover relevant learning resources, such as documentation, tutorials, and articles, based on their queries.
- **Learning Roadmap:** Generates personalized learning roadmaps for different programming languages, technologies, or concepts.

## Setup

### Prerequisites

- Python 3.7+
- Pip (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory of the project and add the following environment variable:
    ```
    HF_API_TOKEN="your_hugging_face_api_token"
    ```
    Replace `"your_hugging_face_api_token"` with your actual Hugging Face API token. You can obtain a token from the [Hugging Face website](https://huggingface.co/settings/tokens).

5.  **Initialize the database:**
    Run the following command to create and initialize the database:
    ```bash
    python src/init_db.py
    ```

## Running the Application

Once the setup is complete, you can run the Streamlit application using the following command:

```bash
streamlit run src/app.py
```

This will start the application, and you can access it in your web browser at the URL provided in the terminal (usually `http://localhost:8501`).

## Project Structure

```
.
├── .gitignore
├── ai_tutor_db/
│   └── ai_tutor.db       # SQLite database file
├── assets/
│   └── images/
│       └── logo.png
├── config/
│   ├── __init__.py
│   └── config.py         # Configuration for API keys
├── requirements.txt      # Project dependencies
├── src/
│   ├── __init__.py
│   ├── app.py            # Main Streamlit application
│   ├── auth.py           # Authentication and user management
│   ├── chat_interface.py # Handles interaction with the Hugging Face API
│   ├── database.py       # Database interaction logic
│   ├── init_db.py        # Script to initialize the database
│   ├── quiz_system.py    # Logic for the quiz feature
│   ├── resource_finder.py # Logic for the resource finding feature
│   └── roadmap_generator.py # Logic for generating learning roadmaps
└── README.md             # This file
```

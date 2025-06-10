# Project Documentation: AI Coding Tutor

## 1. Introduction

This document provides a detailed overview of the AI Coding Tutor project, including its architecture, components, database schema, and AI integration. The AI Coding Tutor is a web application built with Streamlit that aims to help users learn programming concepts and improve their coding skills through various interactive features.

## 2. Architecture

The application follows a component-based architecture where different functionalities are encapsulated within separate Python modules. Streamlit is used for the front-end interface, and a SQLite database stores user data and application content. The AI capabilities are provided by integrating with the Hugging Face API.

### Core Components:

-   **`src/app.py`**: The main entry point of the Streamlit application. It handles page navigation, session management, and orchestrates the interaction between different modules.
-   **`src/auth.py`**: Manages user authentication (login, logout, user accounts) and authorization. It also handles the storage and retrieval of user-specific data like chats, quizzes, and roadmaps.
-   **`src/database.py`**: Provides an abstraction layer for interacting with the SQLite database. It includes methods for creating tables, inserting data, and querying data.
-   **`src/init_db.py`**: A script to initialize the database schema. It creates the necessary tables when the application is set up for the first time.
-   **`src/chat_interface.py`**: Responsible for communication with the Hugging Face API. It formats prompts, sends requests, and processes the AI-generated responses.
-   **`config/config.py`**: Loads and manages configuration settings, primarily the Hugging Face API token from an environment variable.

### Feature Modules:

-   **`src/quiz_system.py`**: Implements the quiz functionality. This includes generating quiz questions (both pre-made and AI-generated), displaying quizzes to the user, and scoring.
-   **`src/resource_finder.py`**: Implements the resource finding feature. It takes user queries, uses the AI to find relevant learning resources, and displays them.
-   **`src/roadmap_generator.py`**: Implements the learning roadmap generation. It takes a topic from the user and generates a structured learning plan, potentially using pre-defined templates or AI generation for custom topics.

## 3. Database Schema

The application uses an SQLite database named `ai_tutor.db` located in the `ai_tutor_db/` directory. The schema consists of the following tables:

-   **`users`**: Stores user information.
    -   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    -   `username` (TEXT UNIQUE NOT NULL)
    -   `password_hash` (TEXT NOT NULL)

-   **`chats`**: Stores chat sessions.
    -   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    -   `user_id` (INTEGER, FOREIGN KEY to `users.id`)
    -   `title` (TEXT NOT NULL DEFAULT 'New Chat')
    -   `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

-   **`chat_messages`**: Stores individual messages within a chat.
    -   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    -   `chat_id` (INTEGER, FOREIGN KEY to `chats.id`)
    -   `role` (TEXT NOT NULL) -- 'user' or 'assistant'
    -   `content` (TEXT NOT NULL)
    -   `timestamp` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

-   **`quizzes`**: Stores quiz information.
    -   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    -   `user_id` (INTEGER, FOREIGN KEY to `users.id`)
    -   `topic` (TEXT NOT NULL)
    -   `questions` (TEXT NOT NULL) -- JSON string of questions and answers
    -   `score` (INTEGER)
    -   `submitted` (BOOLEAN DEFAULT FALSE)
    -   `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

-   **`roadmaps`**: Stores generated learning roadmaps.
    -   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    -   `user_id` (INTEGER, FOREIGN KEY to `users.id`)
    -   `topic` (TEXT NOT NULL)
    -   `content` (TEXT NOT NULL) -- Markdown content of the roadmap
    -   `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

-   **`resources`**: Stores saved learning resources by users.
    -   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    -   `user_id` (INTEGER, FOREIGN KEY to `users.id`)
    -   `query` (TEXT NOT NULL) -- The search query that led to this resource
    -   `content` (TEXT NOT NULL) -- The AI-generated resource content
    -   `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

## 4. AI Integration (Hugging Face API)

The AI Coding Tutor integrates with the Hugging Face API to provide intelligent responses and content generation.

-   **API Endpoint:** The application uses a specific model endpoint defined in `config/config.py` (HF_API_URL).
-   **Authentication:** API requests are authenticated using a Bearer token (HF_API_TOKEN) stored as an environment variable and accessed via `config/config.py`.
-   **`ChatInterface` Module (`src/chat_interface.py`):**
    -   This module is the central point for all interactions with the Hugging Face API.
    -   The `get_ai_response` method takes a user prompt and optional conversation history.
    -   It formats the input into a prompt suitable for the AI model, including context from previous messages.
    -   It sends a POST request to the HF_API_URL with the prompt and parameters (e.g., `max_new_tokens`, `temperature`).
    -   It handles API responses, including error handling for various status codes (e.g., 503 for service unavailable, 429 for rate limiting).
    -   It includes a retry mechanism for transient errors.
    -   The response from the API (generated text) is then returned to the calling module (e.g., `app.py` for the chat, `quiz_system.py` for quiz generation).

### AI Usage in Features:

-   **Chat Assistant:** Directly uses `ChatInterface` to get responses to user's coding questions.
-   **Quiz System:** Uses `ChatInterface` to generate custom quiz questions based on topic, number of questions, and difficulty level. The prompt is carefully constructed to request questions in a specific format.
-   **Resource Finder:** Uses `ChatInterface` to generate a structured explanation and list of resources based on the user's learning query.
-   **Roadmap Generator:** While it has some pre-defined templates, it can potentially use `ChatInterface` to generate roadmaps for topics not covered by templates (though the current implementation primarily uses templates).

## 5. Data Flow Example (Chat Assistant)

1.  **User Input:** The user types a message in the Streamlit chat interface in `src/app.py`.
2.  **Message Handling (`src/app.py`):**
    -   The user's message is captured.
    -   It's saved to the database via `src/auth.py` which calls methods in `src/database.py`.
    -   The conversation history is retrieved from the database.
3.  **AI Request (`src/chat_interface.py`):**
    -   `app.py` calls `chat_interface.get_ai_response()`, passing the user's prompt and formatted conversation history.
    -   `chat_interface.py` constructs the full prompt and sends it to the Hugging Face API.
4.  **AI Processing (Hugging Face):**
    -   The Hugging Face model processes the prompt and generates a response.
5.  **AI Response (`src/chat_interface.py`):**
    -   `chat_interface.py` receives the response.
    -   It performs basic cleanup of the response text.
6.  **Display Response (`src/app.py`):**
    -   The AI's response is returned to `app.py`.
    -   The response is saved to the database.
    -   The response is displayed in the Streamlit chat interface.

## 6. Future Enhancements / Considerations

-   **Error Handling:** More robust error handling throughout the application.
-   **Security:** Enhance security, especially around user authentication and input sanitization.
-   **Scalability:** For a larger user base, consider moving from SQLite to a more scalable database solution (e.g., PostgreSQL).
-   **AI Model Choice:** Experiment with different Hugging Face models or other LLM providers for potentially better or more cost-effective results.
-   **Frontend Enhancements:** Improve UI/UX with more interactive elements or custom Streamlit components.
-   **Testing:** Implement a comprehensive suite of unit and integration tests.

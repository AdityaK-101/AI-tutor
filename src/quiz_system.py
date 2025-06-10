import json
import streamlit as st

class QuizSystem:
    """
    Manages quiz generation, display, and scoring within the application.

    This class handles both pre-made and AI-generated quizzes. It interacts
    with the database to save and retrieve quiz data and uses the chat interface
    to generate custom quiz questions.
    """
    def __init__(self, db, chat_interface):
        """
        Initializes the QuizSystem.

        Args:
            db: An instance of the Database class for database interactions.
            chat_interface: An instance of the ChatInterface class for generating
                            custom quiz questions.
        """
        self.db = db
        self.chat_interface = chat_interface
        self.debug = False  # Set to True to see AI prompt and response in Streamlit

    def _get_default_questions(self, topic):
        """
        Retrieves pre-made questions for a given topic.

        Args:
            topic: The topic for which to retrieve questions (e.g., "Python Basics").

        Returns:
            A list of question dictionaries for the specified topic, or an empty list
            if the topic is not found.
        """
        default_questions = {
            "Python Basics": [
                {
                    "question": "What is the output of print(type(5))?",
                    "options": ["<class 'int'>", "<class 'str'>", "<class 'float'>", "<class 'number'>"],
                    "correct_answer": "<class 'int'>"
                },
                {
                    "question": "Which of these is not a Python built-in data type?",
                    "options": ["list", "array", "tuple", "dict"],
                    "correct_answer": "array"
                },
                {
                    "question": "What does len([1, 2, 3]) return?",
                    "options": ["3", "2", "4", "Error"],
                    "correct_answer": "3"
                }
            ],
            "Data Structures": [
                {
                    "question": "Which data structure follows LIFO principle?",
                    "options": ["Stack", "Queue", "List", "Tree"],
                    "correct_answer": "Stack"
                },
                {
                    "question": "What is the time complexity of accessing an element in a hash table?",
                    "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
                    "correct_answer": "O(1)"
                }
            ],
            "Algorithms": [
                {
                    "question": "What is the worst-case time complexity of QuickSort?",
                    "options": ["O(n log n)", "O(n)", "O(n^2)", "O(2^n)"],
                    "correct_answer": "O(n^2)"
                }
            ],
            "Object-Oriented Programming": [
                {
                    "question": "What is encapsulation?",
                    "options": [
                        "Bundling data and methods that operate on that data within a single unit",
                        "Creating multiple instances of a class",
                        "Inheriting properties from another class",
                        "Breaking down complex problems into smaller parts"
                    ],
                    "correct_answer": "Bundling data and methods that operate on that data within a single unit"
                }
            ]
        }
        return default_questions.get(topic, [])

    def _parse_text_response(self, response):
        """
        Parses quiz questions from a text-based AI response.

        The AI is prompted to return questions in a specific format. This method
        extracts the question, options, correct answer, and explanation from that format.

        Args:
            response: The text response from the AI containing quiz questions.

        Returns:
            A list of question dictionaries parsed from the response.
        """
        questions = []
        current_question = None
        current_options = []
        current_answer = None
        current_explanation = None # Stores explanation if provided
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip empty or non-relevant lines
            if not line:
                continue
            
            # Heuristic to identify the start of a new question (e.g., "1. Question text")
            if line[0].isdigit() and '.' in line and len(line.split('.', 1)) > 1:
                # If a previous question's data is populated, save it
                if current_question and current_options and current_answer:
                    questions.append({
                        "question": current_question,
                        "options": current_options,
                        "correct_answer": current_answer,
                        "explanation": current_explanation or "No explanation provided." # Default explanation
                    })
                
                # Reset variables for the new question
                current_question = line.split('.', 1)[1].strip()
                current_options = []
                current_answer = None
                current_explanation = None # Reset explanation for new question
            
            # Heuristic to identify options (e.g., "a) Option text")
            elif line.startswith(('a)', 'b)', 'c)', 'd)', 'A)', 'B)', 'C)', 'D)')) and len(line) > 2:
                option = line[2:].strip()
                current_options.append(option)
            
            # Heuristic to identify the correct answer line
            elif line.startswith(('Answer:', 'Correct answer:')) and len(line.split(':', 1)) > 1:
                answer_text = line.split(':', 1)[1].strip()
                # The answer might be prefixed with "a)", "b)", etc. or just be the text
                if answer_text.startswith(('a)', 'b)', 'c)', 'd)', 'A)', 'B)', 'C)', 'D)')) and len(answer_text) > 2:
                    current_answer = answer_text[2:].strip() # Extract text after "a) "
                else:
                    current_answer = answer_text # Assume the text itself is the answer
            
            # Heuristic to identify the explanation line
            elif line.startswith('Explanation:') and len(line.split(':', 1)) > 1:
                current_explanation = line.split(':', 1)[1].strip()
        
        # Add the last parsed question after the loop finishes
        if current_question and current_options and current_answer:
            questions.append({
                "question": current_question,
                "options": current_options,
                "correct_answer": current_answer,
                "explanation": current_explanation or "No explanation provided."
            })
        
        return questions

    def _generate_quiz_questions(self, topic, num_questions, difficulty):
        """
        Generates custom quiz questions using the chat interface (AI).

        It constructs a detailed prompt for the AI based on the topic, number of questions,
        and difficulty level, then parses the AI's response.

        Args:
            topic: The topic for the quiz.
            num_questions: The number of questions to generate.
            difficulty: The difficulty level of the quiz (e.g., "Basic", "Intermediate").

        Returns:
            A list of generated question dictionaries. Falls back to simpler questions
            if AI generation or parsing fails.
        """
        try:
        try:
            # Detailed specifications for different difficulty levels to guide the AI
            difficulty_specs = {
                "Basic": {
                    "description": "Focus on fundamental concepts and simple syntax",
                    "requirements": [
                        "Test basic terminology and definitions",
                        "Use simple, straightforward questions",
                        "Focus on core concepts only",
                        "Avoid complex scenarios",
                        "Questions should be suitable for complete beginners"
                    ],
                    "example": """
1. What is machine learning?
a) A type of artificial intelligence that learns from data
b) A programming language
c) A type of computer hardware
d) A database management system

Answer: a) A type of artificial intelligence that learns from data
Explanation: Machine learning is a fundamental concept in AI that allows systems to learn and improve from experience."""
                },
                "Beginner": {
                    "description": "Test understanding of core concepts with slight complexity",
                    "requirements": [
                        "Include basic problem-solving scenarios",
                        "Test practical applications",
                        "Use real-world examples",
                        "Cover common use cases",
                        "Questions should be suitable for those with basic knowledge"
                    ],
                    "example": """
1. Which type of machine learning is used for spam detection?
a) Supervised learning
b) Quantum learning
c) Manual learning
d) Physical learning

Answer: a) Supervised learning
Explanation: Spam detection uses supervised learning where the model is trained on labeled examples of spam and non-spam emails."""
                },
                "Intermediate": {
                    "description": "Include problem-solving and practical applications",
                    "requirements": [
                        "Focus on implementation details",
                        "Include technical specifics",
                        "Test practical knowledge",
                        "Cover common challenges",
                        "Questions should require hands-on experience"
                    ],
                    "example": """
1. What problem might arise when using gradient descent with a learning rate that's too high?
a) Overshooting the optimal solution
b) Memory overflow
c) CPU overheating
d) Network timeout

Answer: a) Overshooting the optimal solution
Explanation: A high learning rate can cause the algorithm to overshoot the optimal solution, leading to poor convergence or divergence."""
                },
                "Advanced": {
                    "description": "Focus on complex concepts and edge cases",
                    "requirements": [
                        "Include advanced technical concepts",
                        "Cover optimization techniques",
                        "Address edge cases and limitations",
                        "Test deep understanding",
                        "Questions should challenge experienced practitioners"
                    ],
                    "example": """
1. What potential issue could arise in a distributed machine learning system using asynchronous SGD?
a) Stale gradient updates affecting convergence
b) Network latency improving accuracy
c) Memory usage decreasing
d) Training speed slowing down

Answer: a) Stale gradient updates affecting convergence
Explanation: In asynchronous distributed SGD, some workers might compute gradients using outdated parameters, leading to stale updates that can affect convergence."""
                }
            }

            # Constructing a very specific prompt for the AI to generate questions in a parsable format.
            prompt = f"""Generate {num_questions} multiple-choice questions about {topic} at {difficulty} level.

Difficulty Level: {difficulty}
Description: {difficulty_specs[difficulty]['description']}

Requirements for {difficulty} level questions:
{chr(10).join('- ' + req for req in difficulty_specs[difficulty]['requirements'])}

Example question at this difficulty level:
{difficulty_specs[difficulty]['example']}

Format each question exactly like the example above:
1. Question text
a) Correct answer
b) Wrong answer
c) Wrong answer
d) Wrong answer

Answer: a) Correct answer
Explanation: Clear technical explanation

Important:
1. Questions MUST match the {difficulty} level requirements
2. All questions must be about {topic}
3. Each question must have exactly 4 options
4. Include detailed technical explanations
5. Wrong answers should be plausible but clearly incorrect
6. Questions should increase in complexity within this difficulty level"""

            # Get response from the AI
            response = self.chat_interface.get_ai_response(prompt)
            
            # If debugging is enabled, show the raw AI response
            if self.debug:
                st.code(response, language="text")
            
            # Parse the AI's text response into a list of question dictionaries
            questions = self._parse_text_response(response)
            
            # Validate the parsed questions to ensure they meet basic criteria
            validated_questions = []
            for q in questions:
                # Check if options list exists and has 4 options, question and answer are strings,
                # and the correct answer is one of the options.
                if (isinstance(q.get("options"), list) and 
                    len(q.get("options", [])) == 4 and 
                    isinstance(q.get("question"), str) and 
                    isinstance(q.get("correct_answer"), str) and 
                    q.get("correct_answer") in q.get("options", [])):
                    validated_questions.append(q)
                
                # Stop if we have enough validated questions
                if len(validated_questions) == num_questions:
                    break
            
            if validated_questions:
                return validated_questions # Return successfully validated questions
            
            # If validation fails or not enough questions are generated, use fallback
            print(f"AI question generation/validation failed for topic '{topic}'. Using fallback questions.")
            return self._get_fallback_questions(topic, num_questions, difficulty)

        except Exception as e:
            # Catch any other exceptions during generation and resort to fallback
            print(f"Error in question generation for topic '{topic}': {e}")
            return self._get_fallback_questions(topic, num_questions, difficulty)

    def _create_basic_questions(self, topic, num_questions):
        """
        Creates a set of basic, template-based questions about a given topic.

        This is used as a fallback if more sophisticated question generation fails.

        Args:
            topic: The topic for the questions.
            num_questions: The number of basic questions to create.

        Returns:
            A list of basic question dictionaries.
        """
        question_templates = [
            {
                "question": f"What is the primary purpose of {topic}?",
                "options": [
                    f"To solve complex problems in {topic}",
                    f"To create documentation for {topic}",
                    f"To debug {topic} applications",
                    f"To optimize {topic} performance"
                ]
            },
            {
                "question": f"Which tool is commonly used in {topic}?",
                "options": [
                    "Python",
                    "JavaScript",
                    "Java",
                    "C++"
                ]
            },
            {
                "question": f"What is a key principle of {topic}?",
                "options": [
                    "Problem solving",
                    "Documentation",
                    "Testing",
                    "Deployment"
                ]
            }
        ]
        
        questions = []
        # Create as many questions as requested, cycling through templates if needed
        for i in range(min(num_questions, len(question_templates))): # Ensure we don't go out of bounds
            q = question_templates[i].copy() # Use a copy to avoid modifying the original template
            q["correct_answer"] = q["options"][0] # Assume first option is correct for these basic qs
            questions.append(q)
        
        return questions

    def _get_fallback_questions(self, topic, num_questions, difficulty):
        """
        Generates simple fallback questions based on the topic and difficulty level.

        This method provides a safety net if AI-based question generation fails,
        ensuring that some questions are always available.

        Args:
            topic: The topic of the quiz.
            num_questions: The number of questions to generate.
            difficulty: The difficulty level.

        Returns:
            A list of fallback question dictionaries.
        """
        questions = []
        
        difficulty_templates = {
            "Basic": [
                {
                    "question": f"What is the most fundamental concept in {topic}?",
                    "options": [
                        f"Basic {topic} principles",
                        f"Advanced {topic} concepts",
                        f"Complex {topic} patterns",
                        f"{topic} optimization"
                    ],
                    "correct_answer": f"Basic {topic} principles",
                    "explanation": f"Understanding the basic principles is essential for learning {topic}."
                }
            ],
            "Beginner": [
                {
                    "question": f"Which of these is a common application of {topic}?",
                    "options": [
                        f"Solving simple {topic} problems",
                        f"Building complex systems",
                        f"Optimizing performance",
                        f"Managing distributed systems"
                    ],
                    "correct_answer": f"Solving simple {topic} problems",
                    "explanation": f"At the beginner level, focus is on applying {topic} to solve basic problems."
                }
            ],
            "Intermediate": [
                {
                    "question": f"What is an important consideration when implementing {topic}?",
                    "options": [
                        f"Code efficiency and organization",
                        f"Basic syntax",
                        f"Simple loops",
                        f"Print statements"
                    ],
                    "correct_answer": f"Code efficiency and organization",
                    "explanation": f"At the intermediate level, code quality and efficiency become important in {topic}."
                }
            ],
            "Advanced": [
                {
                    "question": f"What is a critical factor when optimizing {topic} for scale?",
                    "options": [
                        f"Performance and resource management",
                        f"Basic functionality",
                        f"Simple error handling",
                        f"Console output"
                    ],
                    "correct_answer": f"Performance and resource management",
                    "explanation": f"At an advanced level, understanding performance implications and resource management is crucial in {topic}."
                }
            ]
        }
        
        # Get templates for the specified difficulty, or default to "Basic"
        templates = difficulty_templates.get(difficulty, difficulty_templates["Basic"])
        for i in range(num_questions):
            # Cycle through available templates if num_questions > len(templates)
            template = templates[i % len(templates)]
            questions.append(template.copy()) # Use a copy
        
        return questions

    def _display_quiz(self):
        """
        Displays the current quiz interface in Streamlit.

        This method handles rendering the quiz questions, options, and capturing user answers.
        It also manages the submission process and displays results.
        It relies on Streamlit session state to maintain the quiz state.
        """
        quiz = st.session_state.current_quiz
        
        # Check if quiz exists and has questions
        if not quiz or not quiz.get("questions"):
            st.warning("No quiz available. Please select a topic and start a quiz.")
            return
        
        # Initialize score in the quiz dictionary if it's not already there
        if "score" not in quiz:
            quiz["score"] = 0

        # Determine if the quiz has been submitted based on data from DB or current session
        st.session_state.quiz_submitted = quiz.get("submitted", False)
        
        # Iterate through each question in the quiz
        for i, question_data in enumerate(quiz["questions"]):
            st.write(f"\n### Question {i + 1}:") # Display question number
            st.write(question_data["question"])   # Display question text
            
            # Unique key for Streamlit radio button widget for this question
            radio_key = f"quiz_answer_{i}"
            
            # Display multiple choice options as radio buttons
            # `index=None` ensures no option is pre-selected.
            # Radio buttons are disabled if the quiz has already been submitted.
            user_choice = st.radio(
                "Choose your answer:",
                options=question_data["options"],
                key=radio_key,
                index=None, # No default selection
                disabled=st.session_state.quiz_submitted # Disable if quiz is already submitted
            )

            # If the quiz has been submitted, display feedback for this question
            if st.session_state.quiz_submitted:
                # Retrieve the user's answer for this question from session state
                # (st.radio stores its state in st.session_state)
                submitted_answer = st.session_state.get(radio_key)

                if submitted_answer is None:
                    st.warning("Question not answered")
                elif submitted_answer == question_data["correct_answer"]:
                    st.success("Correct!")
                    # Display explanation if available
                    if "explanation" in question_data and question_data["explanation"]:
                        st.info(f"Explanation: {question_data['explanation']}")
                else:
                    st.error(f"Incorrect. The correct answer was: {question_data['correct_answer']}")
                    # Display explanation if available
                    if "explanation" in question_data and question_data["explanation"]:
                        st.info(f"Explanation: {question_data['explanation']}")
            
            st.divider() # Visual separator between questions
        
        # Display the "Submit Quiz" button only if the quiz hasn't been submitted yet
        if not st.session_state.quiz_submitted:
            col1, col2 = st.columns([1, 5]) # Layout columns for button
            with col1:
                if st.button("Submit Quiz", type="primary"):
                    st.session_state.quiz_submitted = True # Mark quiz as submitted in session
                    
                    # Calculate the score
                    current_score = 0
                    total_questions_count = len(quiz["questions"])
                    
                    for idx in range(total_questions_count):
                        user_ans = st.session_state.get(f"quiz_answer_{idx}")
                        correct_ans = quiz["questions"][idx]["correct_answer"]
                        if user_ans == correct_ans:
                            current_score += 1
                    
                    quiz["score"] = current_score # Update score in the local quiz dict
                    
                    # Update the quiz score and submitted status in the database
                    if "current_quiz_id" in st.session_state and st.session_state.current_quiz_id:
                        self.db.auth.update_quiz_score(st.session_state.current_quiz_id, current_score)
                    
                    # Update the quiz object in session state to reflect submission and score
                    quiz["submitted"] = True
                    st.session_state.current_quiz = quiz # Save updated quiz back to session state
                    
                    st.rerun() # Rerun the page to display results and disable options
        
        # If the quiz is submitted, show the final score and other relevant info
        if st.session_state.quiz_submitted:
            total_questions_count = len(quiz["questions"])
            final_score = quiz["score"] # Get score from the quiz dict
            
            # This DB update might be redundant if already done above, but ensures consistency
            if "current_quiz_id" in st.session_state and st.session_state.current_quiz_id:
                self.db.auth.update_quiz_score(st.session_state.current_quiz_id, final_score)
            
            st.success(f"Quiz completed! Your final score: {final_score}/{total_questions_count} ({(final_score/total_questions_count*100):.1f}%)")
            
            # Show how many questions were answered (useful if skipping is allowed)
            answered_count = sum(1 for i in range(total_questions_count)
                                   if st.session_state.get(f"quiz_answer_{i}") is not None)
            st.write(f"Questions answered: {answered_count}/{total_questions_count}")
            
            # Option to start a new quiz, which clears the current quiz state
            if st.button("Start New Quiz"):
                # Clean up all session state variables related to the current quiz
                for key_to_delete in list(st.session_state.keys()):
                    if key_to_delete.startswith(("quiz_answer_", "answered_", "quiz_submitted")):
                        del st.session_state[key_to_delete]
                if 'current_quiz' in st.session_state:
                    del st.session_state.current_quiz
                # Consider also clearing current_quiz_id and setting creating_quiz = True
                # st.session_state.creating_quiz = True
                # st.session_state.current_quiz_id = None
                st.rerun() # Rerun to go back to quiz creation/selection
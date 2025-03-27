import json
import streamlit as st

class QuizSystem:
    def __init__(self, db, chat_interface):
        self.db = db
        self.chat_interface = chat_interface
        self.debug = False  # Just set debug to False by default

    def _get_default_questions(self, topic):
        """Get pre-made questions for a given topic."""
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
        """Parse questions from text format response."""
        questions = []
        current_question = None
        current_options = []
        current_answer = None
        current_explanation = None
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for question number and question text
            if line[0].isdigit() and '.' in line:
                # Save previous question if exists
                if current_question and current_options and current_answer:
                    questions.append({
                        "question": current_question,
                        "options": current_options,
                        "correct_answer": current_answer,
                        "explanation": current_explanation or "No explanation provided."
                    })
                
                # Start new question
                current_question = line.split('.', 1)[1].strip()
                current_options = []
                current_answer = None
                current_explanation = None
            
            # Check for options
            elif line.startswith(('a)', 'b)', 'c)', 'd)', 'A)', 'B)', 'C)', 'D)')):
                option = line[2:].strip()
                current_options.append(option)
            
            # Check for answer
            elif line.startswith(('Answer:', 'Correct answer:')):
                answer_text = line.split(':', 1)[1].strip()
                # Handle different answer formats
                if answer_text.startswith(('a)', 'b)', 'c)', 'd)', 'A)', 'B)', 'C)', 'D)')):
                    current_answer = answer_text[2:].strip()
                else:
                    current_answer = answer_text
            
            # Check for explanation
            elif line.startswith('Explanation:'):
                current_explanation = line.split(':', 1)[1].strip()
        
        # Add the last question
        if current_question and current_options and current_answer:
            questions.append({
                "question": current_question,
                "options": current_options,
                "correct_answer": current_answer,
                "explanation": current_explanation or "No explanation provided."
            })
        
        return questions

    def _generate_quiz_questions(self, topic, num_questions, difficulty):
        """Generate custom quiz questions using the chat interface."""
        try:
            # Define difficulty-specific requirements
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

            response = self.chat_interface.get_ai_response(prompt)
            
            if self.debug:
                st.code(response, language="text")
            
            # Parse the response
            questions = self._parse_text_response(response)
            
            # Validate questions
            validated_questions = []
            for q in questions:
                if (isinstance(q.get("options"), list) and 
                    len(q.get("options", [])) == 4 and 
                    isinstance(q.get("question"), str) and 
                    isinstance(q.get("correct_answer"), str) and 
                    q.get("correct_answer") in q.get("options", [])):
                    validated_questions.append(q)
                
                if len(validated_questions) == num_questions:
                    break
            
            if validated_questions:
                return validated_questions
            
            # If we get here, something went wrong
            print("Using fallback questions")
            return self._get_fallback_questions(topic, num_questions, difficulty)

        except Exception as e:
            print(f"Error in question generation: {e}")
            return self._get_fallback_questions(topic, num_questions, difficulty)

    def _create_basic_questions(self, topic, num_questions):
        """Create basic but relevant questions about the topic."""
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
        for i in range(min(num_questions, len(question_templates))):
            q = question_templates[i].copy()
            q["correct_answer"] = q["options"][0]
            questions.append(q)
        
        return questions

    def _get_fallback_questions(self, topic, num_questions, difficulty):
        """Generate fallback questions based on difficulty level."""
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
        
        templates = difficulty_templates.get(difficulty, difficulty_templates["Basic"])
        for i in range(num_questions):
            template = templates[i % len(templates)]
            questions.append(template.copy())
        
        return questions

    def _display_quiz(self):
        """Display the current quiz"""
        quiz = st.session_state.current_quiz
        
        # Check if quiz exists and has questions
        if not quiz or not quiz.get("questions"):
            st.warning("No quiz available. Please select a topic and start a quiz.")
            return
        
        # Initialize score if not present
        if "score" not in quiz:
            quiz["score"] = 0

        # Set quiz_submitted based on the quiz's submitted state from database
        st.session_state.quiz_submitted = quiz.get("submitted", False)
        
        # Display all questions
        for i, question in enumerate(quiz["questions"]):
            st.write(f"\n### Question {i + 1}:")
            st.write(question["question"])
            
            # Generate a unique key for each question's radio button
            radio_key = f"quiz_answer_{i}"
            
            # Display radio buttons with no default selection
            answer = st.radio(
                "Choose your answer:",
                options=question["options"],
                key=radio_key,
                index=None,
                disabled=st.session_state.quiz_submitted
            )

            # If quiz is submitted, show the results for this question
            if st.session_state.quiz_submitted:
                user_answer = st.session_state.get(radio_key)
                if user_answer is None:
                    st.warning("Question not answered")
                elif user_answer == question["correct_answer"]:
                    st.success("Correct!")
                    if "explanation" in question:
                        st.info(f"Explanation: {question['explanation']}")
                else:
                    st.error(f"Incorrect. The correct answer was: {question['correct_answer']}")
                    if "explanation" in question:
                        st.info(f"Explanation: {question['explanation']}")
            
            st.divider()
        
        # Add submit button only if quiz hasn't been submitted
        if not st.session_state.quiz_submitted:
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Submit Quiz", type="primary"):
                    st.session_state.quiz_submitted = True
                    
                    # Calculate score
                    score = 0
                    total_questions = len(quiz["questions"])
                    
                    for i in range(total_questions):
                        user_answer = st.session_state.get(f"quiz_answer_{i}")
                        correct_answer = quiz["questions"][i]["correct_answer"]
                        if user_answer == correct_answer:
                            score += 1
                    
                    quiz["score"] = score
                    
                    # Update quiz in database
                    if "current_quiz_id" in st.session_state:
                        self.db.auth.update_quiz_score(st.session_state.current_quiz_id, score)
                    
                    # Update session state quiz
                    quiz["submitted"] = True
                    st.session_state.current_quiz = quiz
                    
                    st.rerun()
        
        # Show final score and options after submission
        if st.session_state.quiz_submitted:
            total_questions = len(quiz["questions"])
            score = quiz["score"]
            
            # Update quiz in database
            if "current_quiz_id" in st.session_state:
                self.db.auth.update_quiz_score(st.session_state.current_quiz_id, score)
            
            st.success(f"Quiz completed! Your final score: {score}/{total_questions} ({(score/total_questions*100):.1f}%)")
            
            # Show statistics
            answered_questions = sum(1 for i in range(total_questions) 
                                   if st.session_state.get(f"quiz_answer_{i}") is not None)
            st.write(f"Questions answered: {answered_questions}/{total_questions}")
            
            # Option to start a new quiz
            if st.button("Start New Quiz"):
                # Clear all quiz-related session state
                for key in list(st.session_state.keys()):
                    if key.startswith(("quiz_answer_", "answered_", "quiz_submitted")):
                        del st.session_state[key]
                del st.session_state.current_quiz 
import streamlit as st
from typing import Optional

class RoadmapGenerator:
    def __init__(self, db):
        self.db = db

    def generate_roadmap(self, topic: str) -> str:
        """
        Generate a detailed and specific learning roadmap based on the user's topic.
        Returns formatted markdown string with the roadmap.
        """
        # Convert topic to lowercase for easier matching
        topic_lower = topic.lower()
        
        if "python" in topic_lower:
            if "web" in topic_lower:
                return self._python_web_roadmap()
            elif "data science" in topic_lower or "machine learning" in topic_lower:
                return self._python_data_science_roadmap()
            else:
                return self._python_basics_roadmap()
        elif "javascript" in topic_lower or "js" in topic_lower:
            return self._javascript_roadmap()
        elif "web" in topic_lower:
            return self._web_development_roadmap()
        else:
            # For topics we don't have a specific template for,
            # we should still provide a structured response
            return f"""
## Learning Roadmap for {topic}

### 1. Understanding the Fundamentals
- Research and understand the basic concepts of {topic}
- Set up the necessary development environment
- Learn the core terminology and principles

### 2. Building Blocks
- Master the essential components
- Practice with basic exercises
- Build small projects to reinforce learning

### 3. Advanced Concepts
- Dive into complex topics
- Study best practices and design patterns
- Work on more challenging projects

### 4. Real-world Application
- Build portfolio projects
- Contribute to open source
- Practice with real-world scenarios

### 5. Next Steps
- Join relevant communities
- Follow industry experts
- Keep up with latest trends
"""

    def _python_basics_roadmap(self) -> str:
        return """
## Python Programming Roadmap

### 1. Python Fundamentals (2-3 weeks)
- Install Python and set up your IDE (VS Code/PyCharm)
- Learn basic syntax and data types
  - Variables and numbers
  - Strings and string manipulation
  - Lists, tuples, and dictionaries
  - Sets and boolean operations
- Control structures
  - if/else statements
  - for and while loops
  - break and continue

### 2. Functions and Modules (2 weeks)
- Function definition and parameters
- Return values and scope
- Lambda functions
- Built-in functions
- Creating and importing modules
- Working with pip and virtual environments

### 3. Object-Oriented Programming (2-3 weeks)
- Classes and objects
- Inheritance and polymorphism
- Encapsulation and abstraction
- Magic methods
- Property decorators

### 4. File Operations and Error Handling (1-2 weeks)
- Reading and writing files
- Working with CSV and JSON
- Exception handling (try/except)
- Context managers (with statement)

### 5. Advanced Python Concepts (2-3 weeks)
- List comprehensions
- Generators and iterators
- Decorators
- Regular expressions
- Type hints
- Unit testing with pytest

### 6. Python Standard Library (2 weeks)
- datetime and time
- collections
- os and sys
- argparse
- logging

### Recommended Projects:
1. Command-line todo application
2. File organizer script
3. Simple text-based game
4. Data processing tool
5. API wrapper library

### Learning Resources:
- Python.org official tutorial
- Real Python website
- "Automate the Boring Stuff with Python" book
- Python Crash Course book
- LeetCode/HackerRank for practice

### Best Practices:
- Write clean, PEP 8 compliant code
- Document your code with docstrings
- Use version control (Git)
- Write unit tests
- Join Python communities (Reddit, Discord)
"""

    def _python_web_roadmap(self) -> str:
        return """
## Python Web Development Roadmap

### 1. Prerequisites (1-2 weeks)
- Solid Python fundamentals
- Basic HTML/CSS
- Understanding of HTTP protocol
- Basic command line usage

### 2. Web Frameworks (4-6 weeks)
#### Flask (Start here)
- Basic routing and templates
- Jinja2 templating engine
- Forms and validation
- Database integration with SQLAlchemy
- RESTful API development
- Authentication and authorization

#### Django (After Flask)
- Django MTV architecture
- URL routing and views
- Django ORM
- Django admin interface
- Forms and model forms
- Class-based views
- Django REST framework

### 3. Databases (3-4 weeks)
- SQL fundamentals
- PostgreSQL
- SQLAlchemy ORM
- Database design and normalization
- Migration management
- Caching with Redis

### 4. API Development (2-3 weeks)
- REST principles
- API authentication
- JWT tokens
- API versioning
- Documentation (Swagger/OpenAPI)
- Testing APIs

### 5. Advanced Topics (4-5 weeks)
- Asynchronous Python (asyncio)
- WebSockets
- Celery for background tasks
- Docker containerization
- CI/CD pipelines
- Deployment (Heroku, AWS)
- Performance optimization
- Security best practices

### Recommended Projects:
1. Personal blog with Flask
2. E-commerce site with Django
3. RESTful API service
4. Real-time chat application
5. Social media clone

### Essential Tools:
- Git for version control
- Docker for containerization
- Postman for API testing
- pgAdmin for database management
- Redis for caching
- Nginx for reverse proxy

### Learning Resources:
- Flask documentation
- Django documentation
- Real Python tutorials
- TestDriven.io
- Miguel Grinberg's Flask Mega-Tutorial
"""

    def _python_data_science_roadmap(self) -> str:
        return """
## Python Data Science Roadmap

### 1. Python for Data Science (2-3 weeks)
- NumPy fundamentals
  - Arrays and operations
  - Broadcasting
  - Linear algebra
- Pandas basics
  - DataFrames and Series
  - Data cleaning
  - Data manipulation
- Data visualization
  - Matplotlib
  - Seaborn
  - Plotly

### 2. Statistics and Mathematics (4 weeks)
- Descriptive statistics
- Probability theory
- Inferential statistics
- Linear algebra basics
- Calculus fundamentals
- Hypothesis testing

### 3. Machine Learning (8-10 weeks)
#### Scikit-learn
- Supervised Learning
  - Linear regression
  - Logistic regression
  - Decision trees
  - Random forests
  - Support vector machines
- Unsupervised Learning
  - K-means clustering
  - PCA
  - Dimensionality reduction
- Model evaluation
  - Cross-validation
  - Metrics
  - Hyperparameter tuning

### 4. Deep Learning (6-8 weeks)
- Neural Networks basics
- TensorFlow/Keras
- PyTorch
- CNN for computer vision
- RNN for sequence data
- Transfer learning

### 5. Big Data Tools (4 weeks)
- SQL for data analysis
- PySpark basics
- Dask for parallel computing
- Data pipelines
- ETL processes

### 6. MLOps and Deployment (3-4 weeks)
- Model versioning
- Model deployment
- API development
- Docker containerization
- Model monitoring
- ML pipelines

### Recommended Projects:
1. Exploratory data analysis project
2. Machine learning classification project
3. Time series prediction
4. Computer vision application
5. Natural language processing project

### Essential Tools:
- Jupyter Notebooks
- Git for version control
- Docker
- MLflow for experiment tracking
- DVC for data versioning

### Learning Resources:
- Coursera Machine Learning courses
- Fast.ai
- Kaggle competitions
- DataCamp
- Stanford CS229
"""

    def _javascript_roadmap(self) -> str:
        # Add detailed JavaScript roadmap here
        pass

    def _web_development_roadmap(self) -> str:
        # Add detailed web development roadmap here
        pass
    
    def render(self):
        """
        This method is kept for compatibility but now just shows a welcome message
        The main interaction happens through the chat interface
        """
        st.markdown("""
        # Learning Roadmap Generator
        
        Use the chat input below to get a personalized learning roadmap. 
        
        Example prompts:
        - "Create a roadmap for learning Python from scratch"
        - "How to become a full-stack developer"
        - "Learning path for data science"
        """)
    
    def _generate_roadmap(self, path, experience):
        steps = self.learning_paths[path]
        
        st.subheader(f"Your {path} Learning Roadmap")
        st.write(f"Based on your {experience.lower()} experience level")
        
        for i, step in enumerate(steps, 1):
            with st.expander(f"Step {i}: {step}"):
                # Get relevant resources from database
                resources = self.db.get_resources({"topics": step.lower()})
                
                st.write("**Key Concepts to Learn:**")
                st.write("- Concept 1")
                st.write("- Concept 2")
                st.write("- Concept 3")
                
                if resources:
                    st.write("**Recommended Resources:**")
                    for resource in resources:
                        st.write(f"- [{resource['title']}]({resource['url']})") 
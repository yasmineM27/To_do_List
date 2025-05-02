# TaskFlow Technical Documentation

This document provides technical details about the TaskFlow application for developers who want to understand the codebase, make modifications, or extend the functionality.

## Project Overview

TaskFlow is a Django-based productivity application that helps users organize tasks, create to-do lists, and track their progress. The application follows Django's Model-View-Template (MVT) architecture.

## Project Structure

\`\`\`
taskflow/
├── taskflow/              # Main project folder
│   ├── __init__.py
│   ├── settings.py        # Project settings
│   ├── urls.py            # Main URL routing
│   ├── asgi.py
│   └── wsgi.py
├── core/                  # Core app (authentication, common views)
│   ├── admin.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
├── tasks/                 # Tasks app (todo lists, tasks, tags)
│   ├── admin.py
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/
├── static/                # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── templates/             # Global templates
│   └── base.html
├── manage.py
└── requirements.txt
\`\`\`

## Installation and Setup

### Requirements

- Python 3.8+
- Django 4.2+
- Other dependencies in requirements.txt

### Installation Steps

1. Clone the repository
2. Create a virtual environment:
   \`\`\`
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   \`\`\`
3. Install dependencies:
   \`\`\`
   pip install -r requirements.txt
   \`\`\`
4. Apply migrations:
   \`\`\`
   python manage.py migrate
   \`\`\`
5. Create a superuser:
   \`\`\`
   python manage.py createsuperuser
   \`\`\`
6. Run the development server:
   \`\`\`
   python manage.py runserver
   \`\`\`

## Data Models

### Core App

The core app handles user authentication using Django's built-in User model.

### Tasks App

#### ToDoList Model

```python
class ToDoList(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todo_lists')
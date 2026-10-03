from app.context.engine import ContextEngine
from evaluation.retrieval.lexical_baseline import recall_at_k


CASES = [
    {
        "task": "Find the URL configuration",
        "query": "urlpatterns",
        "expected_files": [
            "demo-django/demo_django/urls.py",
        ],
    },
    {

        "task": "Find where Django routes incoming URLs.",
        "query": "urlpatterns",
        "expected_files": [
            "demo-django/demo_django/urls.py",
        ],
    },

    {
        "task": "Find where the Django database configuration is defined.",
        "query": "DATABASES",
        "expected_files": [
            "demo-django/demo_django/settings.py",
        ],
    },

    {
        "task": "Find where the Django applications installed in this project are configured.",
        "query": "INSTALLED_APPS",
        "expected_files": [
            "demo-django/demo_django/settings.py",
        ],
    },

    {
        "task": "Find the command-line entry point for the Django application.",
        "query": "execute_from_command_line",
        "expected_files": [
            "demo-django/manage.py",
        ],
    },

]


SEMANTIC_CASES = [
    {
        "task": "Where is the database setup for this Django project?",
        "query": "database setup",
        "expected_files": [
            "demo-django/demo_django/settings.py",
        ],
    },

    {
        "task": "Where are the Django applications registered for this project?",
        "query": "application registration",
        "expected_files": [
            "demo-django/demo_django/settings.py",
        ],
    },

    {
        "task": "Where are installed Django applications configured?",
        "query": "installed Django applications",
        "expected_files": [
            "demo-django/demo_django/settings.py"
        ],
},
]


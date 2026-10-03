from app.tools.execution import run_tests
from app.tools.filesystem import (
    create_file,
    edit_file,
    read_file,
)
from app.tools.search import search_code


TOOLS = {
    "search_code": search_code,
    "read_file": read_file,
    "edit_file": edit_file,
    "create_file": create_file,
    "run_tests": run_tests,
}
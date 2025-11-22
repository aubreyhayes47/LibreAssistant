import datetime
import math

class Tool:
    def __init__(self, name: str, description: str, func: callable):
        self.name = name
        self.description = description
        self.func = func

    def run(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def to_string(self):
        return f"{self.name}: {self.description}"


def get_current_time(*args, **kwargs):
    """Returns the current local time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(expression: str):
    """Evaluates a mathematical expression."""
    try:
        # Safety: Limit available names to math module
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        return str(eval(expression, {"__builtins__": {}}, allowed_names))
    except Exception as e:
        return f"Error: {e}"

# Registry of available tools
TOOLS = [
    Tool("get_current_time", "Returns the current local time. No arguments needed.", get_current_time),
    Tool("calculate", "Evaluates a mathematical expression (e.g., '2 + 2', 'sqrt(16)'). Input is a string expression.", calculate),
]

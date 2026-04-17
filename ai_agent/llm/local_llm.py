import subprocess
import shutil


def ask_llm(prompt):
    # Check if ollama is available
    if not shutil.which("ollama"):
        return "Sorry, Ollama is not installed or not in PATH. Please install Ollama to use AI responses for non-CRM questions."

    try:
        result = subprocess.run(
            ["ollama", "run", "mistral", prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30  # Add timeout to prevent hanging
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "AI response timed out. Please try again."
    except Exception as e:
        return f"Error running AI: {str(e)}"
import os

ROOT = "ai_agent"

folders = [
    "agent",
    "llm",
    "voice",
    "tools",
    "input",
    "config",
    "utils"
]

files = [
    "main.py",

    "agent/agent.py",
    "agent/planner.py",
    "agent/memory.py",
    "agent/executor.py",

    "llm/local_llm.py",

    "voice/speech_to_text.py",
    "voice/text_to_speech.py",
    "voice/recorder.py",

    "tools/crm_tools.py",
    "tools/system_tools.py",
    "tools/tool_registry.py",

    "input/input_router.py",

    "config/settings.py",

    "utils/language.py"
]


def create():
    print("Creating AI Agent Structure...\n")

    os.makedirs(ROOT, exist_ok=True)

    for folder in folders:
        os.makedirs(os.path.join(ROOT, folder), exist_ok=True)

    for file in files:
        path = os.path.join(ROOT, file)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w") as f:
            f.write("")

        print("Created:", path)

    print("\n✅ AI Agent folder created successfully")


if __name__ == "__main__":
    create()
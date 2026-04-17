from agent.planner import decide
from agent.executor import execute


def run_agent(user_input):

    action = decide(user_input)

    result = execute(action, user_input)

    return result
from agent.agent import run_agent


def format_response(reply):
    """Format the agent response for better readability"""
    if isinstance(reply, list):
        # CRM data - list of dictionaries
        if not reply:
            return "No data found."

        formatted = []
        for item in reply:
            if isinstance(item, dict):
                # Format each dict as key: value pairs
                formatted_item = ", ".join(f"{k}: {v}" for k, v in item.items())
                formatted.append(formatted_item)
            else:
                formatted.append(str(item))

        return "\n".join(formatted)

    elif isinstance(reply, dict):
        # Service documents - dictionary
        formatted = []
        for service, docs in reply.items():
            formatted.append(f"\n{service.upper()}:")
            if isinstance(docs, list):
                for i, doc in enumerate(docs, 1):
                    formatted.append(f"  {i}. {doc}")
            else:
                formatted.append(f"  {docs}")
        return "\n".join(formatted)

    else:
        # LLM response or other string
        return str(reply)


def main():
    while True:
        user = input("You: ")

        if user.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        reply = run_agent(user)
        print("AI:", format_response(reply))


if __name__ == "__main__":
    main()

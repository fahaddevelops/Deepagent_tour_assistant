import os
from typing import Literal
from dotenv import load_dotenv
from tavily import TavilyClient
from deepagents import create_deep_agent

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not OPENAI_API_KEY or not TAVILY_API_KEY:
    raise ValueError("API keys not found. Check your .env file.")

# --------------------------------------------------
# Tavily Search Tool
# --------------------------------------------------
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """
    Run a web search using Tavily
    """
    return tavily_client.search(
        query=query,
        max_results=max_results,
        topic=topic,
        include_raw_content=include_raw_content,
    )

# --------------------------------------------------
# System Instructions (Extreme Context Engineering)
# --------------------------------------------------
research_instructions = """
You are an expert research agent.

Your responsibilities:
- Plan before acting
- Use internet_search for up-to-date information
- Write clear and structured responses
- Use files if information becomes large
- Delegate subtasks when needed

Always prioritize accuracy and clarity.
"""

# --------------------------------------------------
# Create Deep Agent
# --------------------------------------------------
agent = create_deep_agent(
    tools=[internet_search],
    system_prompt=research_instructions,
)

# --------------------------------------------------
# Run Agent
# --------------------------------------------------
if __name__ == "__main__":
    user_query = "What is LangGraph and why is it used in deep agents?"

    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": user_query}
            ]
        }
    )

    # Print final answer
    print("\n--- AGENT RESPONSE ---\n")
    print(result["messages"][-1].content)

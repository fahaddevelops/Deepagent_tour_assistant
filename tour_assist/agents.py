
from typing import List, Optional
import os
from dotenv import load_dotenv
from deepagents import create_deep_agent
from deepagents.middleware.subagents import SubAgent
from tour_assist.tools import internet_search
from langchain_openai import ChatOpenAI

load_dotenv()

# ----------------------------------------------------------------------
# Prompts
# ----------------------------------------------------------------------

RESEARCH_PROMPT = """
You are a specialist Research Agent for travel and tours.
Your goal is to find accurate, up-to-date information about:
- Tourist attractions (opening hours, ticket prices).
- Hotels and accommodation (prices, ratings, locations).
- Transport options (flights, trains, local transit).

Always provide specific details (prices in USD or local currency, exact names).
Output your findings clearly for the Planner Agent to use.
"""

PLANNER_PROMPT = """
You are a specialist Planner Agent.
Your goal is to create a logical, day-by-day itinerary based on research data.
- Ensure the flow makes sense geographically.
- Balance activity time vs. rest time.
- Group nearby attractions together.

Input: Research data about a destination.
Output: A detailed itinerary with "Day 1", "Day 2", etc.
"""

BUDGET_PROMPT = """
You are a specialist Budget Agent.
Your goal is to estimate the total cost of the trip and suggest optimizations.
- Tally up flight, hotel, food, and activity costs.
- Compare against the user's budget (Low, Medium, High).
- If over budget, suggest cheaper alternatives.
"""

# ----------------------------------------------------------------------
# Agent Factory
# ----------------------------------------------------------------------

def get_tour_agent(model_name: str = "gpt-4.1-mini"):
    """
    Creates the main Tour Planning Deep Agent with subagents.
    Uses OpenAI (gpt-4o-mini) by default.
    """
    
    # Ensure key is present
    if not os.getenv("OPENAI_API_KEY"):
         raise ValueError("OPENAI_API_KEY not found in environment.")

    env_model = os.getenv("MODEL_NAME") or os.getenv("model")
    effective_model = env_model or model_name
    llm = ChatOpenAI(model=effective_model, temperature=0.7)

    # Subagents
    subagents: List[SubAgent] = [
        {
            "name": "researcher",
            "description": "Conducts detailed web research on destinations, hotels, and prices.",
            "system_prompt": RESEARCH_PROMPT,
            "tools": [internet_search],
            "model": llm,
        },
        {
            "name": "planner",
            "description": "Constructs the day-by-day itinerary based on research.",
            "system_prompt": PLANNER_PROMPT,
            "tools": [], 
            "model": llm,
        },
        {
            "name": "budget_calculator",
            "description": "Calculates total costs and checks against budget constraints.",
            "system_prompt": BUDGET_PROMPT,
            "tools": [],
            "model": llm,
        },
    ]

    # Main Agent
    agent = create_deep_agent(
        model=llm, 
        tools=[internet_search], 
        subagents=subagents,
        system_prompt="""
        You are the Lead Tour Planning Agent.
        
        # INTERACTION PROTOCOL (STRICT)
        1. **Phase 1: Research & Propose**: 
           - Do NOT write a final itinerary yet.
           - Research options using your subagents.
           - Present the user with **3 distinct options/plans** based on their request.
           - Ask the user: "Which option would you like to proceed with?" due to the Human-in-the-Loop requirement.
        
        2. **Phase 2: Finalize**:
           - ONLY AFTER the user has replied with a choice.
           - Generate the detailed day-by-day itinerary for that specific choice using the 'planner'.
           - Verify with 'budget_calculator'.
           - End the conversation with: "Thank you for your selection! Here is your plan."

        ## CONCURRENCY RULES
        - Do NOT call more than one `task` in the same assistant turn.
        - In Phase 2, run subagents SEQUENTIALLY: first `planner`, then `budget_calculator`.
        - Never spawn `planner` and `budget_calculator` at the same time.
        
        Note: If the user message is just the initial query, you are in Phase 1. If the user message is a selection, you are in Phase 2.
        """,
    )
    
    return agent

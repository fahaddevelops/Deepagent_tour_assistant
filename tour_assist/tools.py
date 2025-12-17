
import os
from typing import Literal
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_core.tools import tool

# Load environment variables
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    # Fallback or error - for now we let it fail if not found, 
    # but in a real app better handling is needed
    pass

_tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

@tool
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict:
    """
    Run a web search using Tavily. use this for finding hotels, flights, tour spots, and updated prices.
    Returns a dictionary with search results.
    """
    if not _tavily_client:
        return {"error": "TAVILY_API_KEY not found in environment variables."}
    
    try:
        return _tavily_client.search(
            query=query,
            max_results=max_results,
            topic=topic,
            include_raw_content=include_raw_content,
        )
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

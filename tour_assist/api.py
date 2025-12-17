
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from tour_assist.agents import get_tour_agent
from langchain_core.messages import HumanMessage, AIMessage
import uvicorn
import json
import asyncio
import logging

app = FastAPI()

logger = logging.getLogger("deepagent")
logger.setLevel(logging.INFO)
_fh = logging.FileHandler("deepagent.logs", encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
if not logger.handlers:
    logger.addHandler(_fh)

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})

@app.post("/plan")
async def plan_trip(request: Request):
    """
    Streaming endpoint.
    Recieves JSON: {"messages": [{"role": "user", "content": "..."}, ...]}
    Yields JSON chunks.
    """
    body = await request.json()
    
    # robustly handle either 'query' (legacy) or 'messages' (new)
    messages_data = body.get("messages", [])
    if not messages_data and "query" in body:
         messages_data = [{"role": "user", "content": body["query"]}]
         
    # Convert to LangChain format
    lc_messages = []
    for m in messages_data:
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_messages.append(AIMessage(content=m["content"]))
            
    # If the last message is not user, we might be in trouble, but assume client sends correct order.
    # Actually, let's just create a fresh list of Human/AI messages.
    inputs = {"messages": []}
    for m in messages_data:
        if m["role"] == "user":
            inputs["messages"].append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            inputs["messages"].append(AIMessage(content=m["content"]))
    
    async def event_generator():
        try:
            agent = get_tour_agent()
            logger.info("start plan")
            
            # Using astream_events (v2) for granular observability
            async for event in agent.astream_events(inputs, version="v1"):
                event_type = event["event"]
                
                # Observability Logic
                if event_type == "on_tool_start":
                    tool_name = event["name"]
                    if tool_name == "task":
                        # Subagent Spawning
                        try:
                            # Arg parsing depends on if it's dict or str
                            args = event["data"].get("input", {})
                            sub_type = args.get("subagent_type", "unknown")
                            description = args.get("description", "")
                            
                            log_msg = f"🚀 **SubTask**: `{sub_type}`\n> _{description}_"
                            yield json.dumps({"type": "log", "message": log_msg}) + "\n"
                            logger.info(f"subtask {sub_type} {description}")
                        except:
                            yield json.dumps({"type": "log", "message": "🚀 Spawning a SubAgent..."}) + "\n"
                            logger.info("subagent spawn")
                    
                    elif tool_name == "internet_search":
                        q = event["data"].get("input", {}).get("query", "")
                        yield json.dumps({"type": "log", "message": f"🔍 **Researching**: {q}"}) + "\n"
                        logger.info(f"internet_search {q}")

                elif event_type == "on_chain_end":
                    pass

            # Final answer
            final_state = await agent.ainvoke(inputs)
            final_content = final_state["messages"][-1].content
            yield json.dumps({"type": "answer", "content": final_content}) + "\n"
            logger.info("final_answer")

        except Exception as e:
            logger.error(str(e))
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)

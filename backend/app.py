from fastapi import FastAPI
from agent.graph import graph

app = FastAPI()

@app.post("/chat")
async def chat(user_message: str):
    response = await graph.ainvoke({"changeme": user_message})
    return {"response": response}

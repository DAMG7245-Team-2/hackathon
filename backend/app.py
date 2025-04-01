from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.exceptions import HTTPException
from agent.graph import graph
from pydantic import BaseModel

class ChatInput(BaseModel):
    user_message: str


app = FastAPI()

@app.post("/chat")
async def chat(chat_input: ChatInput):
    try:
        response = await graph.ainvoke({"topic": chat_input.user_message})
        print("response:", response)
        with open("final_report.md", "w") as f:
            f.write(response["final_report"])
        return FileResponse("final_report.md", media_type="text/markdown")
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))

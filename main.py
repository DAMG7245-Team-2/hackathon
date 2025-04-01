# main.py
import asyncio
from agent.graph import graph
from agent.state import State
import os

job_description = """
    We are looking for a Data Scientist with experience in machine learning,
    Python, cloud platforms (AWS/GCP), SQL, and data visualization.
    The role involves working with large datasets, building ML models,
    and communicating insights to stakeholders.
    """
'''
if __name__ == "__main__":
    
    os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    os.environ["PINECONE_API_KEY"]=os.getenv("PINECONE_API_KEY")
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    result = graph.invoke(State(changeme=job_description))
    print(result["changeme"])
job_description = "..."
'''
async def run():
    result = await graph.ainvoke(
        State(input=job_description),
        config={"recursion_limit": 20}  
    )
    print(result["input"])

asyncio.run(run())
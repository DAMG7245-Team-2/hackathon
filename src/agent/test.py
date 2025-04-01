from pinecone import PineconeAsyncio
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
async def main():
    pc = PineconeAsyncio(api_key=os.getenv("PINECONE_API_KEY"))
    print(await pc.describe_index("resourcebooks"))

if __name__ == "__main__":
    asyncio.run(main())
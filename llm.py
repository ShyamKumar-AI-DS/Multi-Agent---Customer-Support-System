import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llms = ChatGroq(
    model="groq/openai/gpt-oss-20b",   # or llama3-70b-8192
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,
    max_tokens=1000,
)

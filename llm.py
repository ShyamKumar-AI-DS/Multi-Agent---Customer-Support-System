import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

llms = LLM(
    model= "groq/openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,
    max_tokens = 1000,
)

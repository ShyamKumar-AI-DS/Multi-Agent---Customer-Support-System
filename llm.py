from crewai import LLM
from dotenv import load_dotenv
import os

load_dotenv()

llm = LLM(
    model="groq/openai/gpt-oss-20b",  # replace with the actual Groq model slug
    api_key=os.environ["GROQ_API_KEY"],
    max_tokens=512,
    temperature=0.3,
    n = 1,
)

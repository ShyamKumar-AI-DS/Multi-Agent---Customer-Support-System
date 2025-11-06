# from crewai import LLM
# from dotenv import load_dotenv
# import os

# load_dotenv()

# llm = LLM(
#     model="groq/openai/gpt-oss-20b",  # replace with the actual Groq model slug
#     api_key=os.environ["GROQ_API_KEY"],
#     max_tokens=512,
#     temperature=0.3,
#     n = 1,
# )


import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

# instantiate the LangChain model
groq_llm = ChatGroq(
    model="gpt-oss-120b",
    api_key=GROQ_API_KEY,
    temperature=0.3,
    max_tokens=512,
)

# wrap it in a simple callable CrewAI can use
def llm(prompt: str):
    """CrewAI-compatible callable that returns LLM output text."""
    response = groq_llm.invoke(prompt)
    return response.content if hasattr(response, "content") else str(response)

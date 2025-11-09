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
def llms():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.3,
        max_tokens=512,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )


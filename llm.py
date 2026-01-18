import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

from langchain_groq import ChatGroq

<<<<<<< HEAD
llms = LLM(
    model= "groq/openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,
    max_tokens = 1000,
)
=======
# instantiate the LangChain model
def llms():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.3,
        max_tokens=512,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

>>>>>>> 92a26d881a969db236ec41a7bdd0aa2d402f526b

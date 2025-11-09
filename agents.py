from autogen import AssistantAgent, UserProxyAgent
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from pydantic import BaseModel
from vectordb import search_chroma
import os
import asyncio

# ------------------------------------------------------------------
# 1. Load environment variables
# ------------------------------------------------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Please set it in your .env file.")

# ------------------------------------------------------------------
# 2. Define Ticket model
# ------------------------------------------------------------------
class TicketIn(BaseModel):
    Customer_ID: Optional[str] = None
    Customer_Name: str
    Product_Purchased: Optional[str] = None
    Ticket_Type: str
    Ticket_Subject: str
    Ticket_Description: str
    Ticket_Priority: str
    Ticket_Channel: str


# ------------------------------------------------------------------
# 3. Configure Autogen LLM backend (Groq via OpenAI-compatible endpoint)
# ------------------------------------------------------------------
llm_config = {
    "model": "gpt-oss-120b",  # or whichever Groq model slug you use
    "api_key": GROQ_API_KEY,
    "base_url": "https://api.groq.com/openai/v1",
    "temperature": 0.3,
    "max_tokens": 512,
}

# ------------------------------------------------------------------
# 4. Define Agents
# ------------------------------------------------------------------
kb_agent = AssistantAgent(
    name="KnowledgeBaseRAG",
    system_message=(
        "You are an internal FAQ and knowledge base assistant. "
        "You use ChromaDB search results to answer support tickets. "
        "Return a JSON with: answer_short, sources, confidence, resolution_suggested, explainers."
    ),
    llm_config=llm_config,
)

tech_agent = AssistantAgent(
    name="TechSupportSpecialist",
    system_message=(
        "You are a technical support expert. Diagnose the issue based on KB agent output. "
        "Return JSON: diagnosis, steps, risk, should_escalate_to_human, human_context_note."
    ),
    llm_config=llm_config,
)

comm_agent = AssistantAgent(
    name="EmpatheticCommunicator",
    system_message=(
        "You write empathetic customer-facing replies. "
        "Return JSON: customer_message and optional internal_note."
    ),
    llm_config=llm_config,
)

# This acts as the orchestrator (replaces Crew)
user_proxy = UserProxyAgent(
    name="Coordinator",
    human_input_mode="NEVER",
)


# ------------------------------------------------------------------
# 5. Define the orchestration logic
# ------------------------------------------------------------------
async def process_ticket_with_autogen(ticket: TicketIn):
    query = f"{ticket.Ticket_Subject}\n{ticket.Ticket_Description}"
    kb_hits = search_chroma(query)

    # Step 1: KB Agent retrieves knowledge-based insights
    kb_prompt = (
        f"Customer ticket:\n{ticket.dict()}\n\n"
        f"Relevant knowledge base hits:\n{kb_hits}\n\n"
        f"Generate JSON output as described in your system message."
    )
    kb_response = await kb_agent.achat(kb_prompt)
    
    # Step 2: Technical agent analyzes the KB response
    tech_prompt = (
        f"Use the following KB analysis to diagnose the issue:\n{kb_response}\n\n"
        "Generate your JSON as described."
    )
    tech_response = await tech_agent.achat(tech_prompt)
    
    # Step 3: Empathetic communicator crafts final message
    comm_prompt = (
        f"Based on the following technical diagnosis:\n{tech_response}\n\n"
        f"Write a customer-facing empathetic message and optional internal note in JSON."
    )
    comm_response = await comm_agent.achat(comm_prompt)

    # Return final structured output
    return {
        "kb_agent_output": kb_response,
        "tech_agent_output": tech_response,
        "comm_agent_output": comm_response
    }



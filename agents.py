from crewai import Agent, Task, Crew
import asyncio
from llm import llms
from typing import List, Optional, Dict, Any,Literal
from pydantic import BaseModel
from vectordb import search_chroma
TICKET_DB: Dict[str, Dict[str, Any]] = {}

class TicketIn(BaseModel):
    Customer_ID: Optional[str] = None              # generated automatically if not provided
    Customer_Name: str
    Product_Purchased: Optional[str] = None
    Ticket_Type: str  # was Literal["bug", ...], now freeform
    Ticket_Subject: str
    Ticket_Description: str
    Ticket_Priority: str   # was Literal["low", ...]
    Ticket_Channel: str    # was Literal["email", ...]
    # date_created: Optional[datetime] = None      # auto-populated in system


agent1 = Agent(
    role="Knowledge Base RAG",
    goal="Retrieve KB answers for customer support tickets",
    backstory="Internal FAQ assistant using ChromaDB",
    verbose=True,
    llm=llm,
    
)

agent2 = Agent(
    role="Technical Support Specialist",
    goal="Diagnose technical issues, suggest steps, escalate if needed",
    backstory="Conservative, safe instructions for remediation",
    verbose=True,
    llm=llm
)

agent3 = Agent(
    role="Empathetic Customer Communicator",
    goal="Craft friendly customer-facing replies with empathy",
    backstory="Writes warm, concise, SLA-bound responses",
    verbose=True,
    llm=llm
)

async def process_ticket_with_crew(ticket: TicketIn):
    query = f"{ticket.Ticket_Subject}\n{ticket.Ticket_Description}"
    kb_hits = search_chroma(query)

    t1 = Task(
        description=f"Answer customer query using KB.\nTicket: {ticket.dict()}\nEvidence: {kb_hits}",
        agent=agent1,
        expected_output=(
            "A JSON object with the following fields:\n"
            "- answer_short: string\n"
            "- sources: list of objects (each with doc metadata)\n"
            "- confidence: float between 0 and 1\n"
            "- resolution_suggested: boolean\n"
            "- explainers: optional list of strings"
        ),
    )

    t2 = Task(
        description=f"Diagnose and suggest steps based on Agent1 output.",
        agent=agent2,
        expected_output=(
            "A JSON object with the following fields:\n"
            "- diagnosis: string\n"
            "- steps: list of strings\n"
            "- risk: string (one of 'low', 'medium', 'high')\n"
            "- should_escalate_to_human: boolean\n"
            "- human_context_note: optional string"
        ),
    )

    t3 = Task(
        description=f"Write customer-facing empathetic message and internal note.",
        agent=agent3,
        expected_output=(
            "A JSON object with the following fields:\n"
            "- customer_message: string\n"
            "- internal_note: optional string"
        ),
    )


    crew = Crew(agents=[agent1, agent2, agent3], tasks=[t1, t2, t3])
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, crew.kickoff)
    return result

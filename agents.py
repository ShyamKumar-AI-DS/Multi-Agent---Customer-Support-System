# import json
# from llm import llms  # Your LangChain LLM (e.g., ChatGroq, ChatOpenAI)
# from typing import List, Optional, Dict, Any, Literal
# from pydantic import BaseModel
# from vectordb import search_chroma

# # --- LangChain Imports ---
# from langchain_core.prompts import ChatPromptTemplate
# # This is the direct LangChain equivalent of agno's `@client.prompt(model=...)`
# from langchain.chains.structured_output import create_structured_output_runnable

# # --- 1. Define Output Models (Copied from your code) ---

# class TicketIn(BaseModel):
#     Customer_ID: Optional[str] = None
#     Customer_Name: str
#     Product_Purchased: Optional[str] = None
#     Ticket_Type: str
#     Ticket_Subject: str
#     Ticket_Description: str
#     Ticket_Priority: str
#     Ticket_Channel: str

# class RagOutput(BaseModel):
#     """Output model for the RAG agent."""
#     answer_short: str
#     sources: List[Dict[str, Any]]
#     confidence: float
#     resolution_suggested: bool
#     explainers: Optional[List[str]] = None

# class TechOutput(BaseModel):
#     """Output model for the Technical agent."""
#     diagnosis: str
#     steps: List[str]
#     risk: Literal["low", "medium", "high"]
#     should_escalate_to_human: bool
#     human_context_note: Optional[str] = None

# class CommOutput(BaseModel):
#     """Output model for the Communications agent."""
#     customer_message: str
#     internal_note: Optional[str] = None

# # --- 2. Define LangChain Prompts (from your agno docstrings) ---

# RAG_PROMPT_TEMPLATE = """
# **Role:** Knowledge Base RAG
# **Goal:** Retrieve KB answers for customer support tickets.
# **Backstory:** Internal FAQ assistant using ChromaDB.

# **Task:** Answer the customer query using the provided Knowledge Base evidence.
# Analyze the ticket and the evidence to provide a concise answer,
# confidence score, and suggest if the resolution is found.

# **Ticket:**
# {ticket_json}

# **Evidence:**
# {kb_hits_json}
# """
# rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)


# TECH_PROMPT_TEMPLATE = """
# **Role:** Technical Support Specialist
# **Goal:** Diagnose technical issues, suggest steps, escalate if needed.
# **Backstory:** Conservative, safe instructions for remediation.

# **Task:** Diagnose and suggest remediation steps based on the RAG agent's output.
# Provide a clear diagnosis, safe steps, assess risk, and decide if escalation is needed.

# **RAG Agent Output:**
# {rag_output_json}
# """
# tech_prompt = ChatPromptTemplate.from_template(TECH_PROMPT_TEMPLATE)


# COMM_PROMPT_TEMPLATE = """
# **Role:** Empathetic Customer Communicator
# **Goal:** Craft friendly customer-facing replies with empathy.
# **Backstory:** Writes warm, concise, SLA-bound responses.

# **Task:** Write a customer-facing empathetic message and an internal note.
# Use the ticket details, RAG analysis, and technical diagnosis to craft the final response.

# **Original Ticket:**
# {ticket_json}

# **RAG Analysis:**
# {rag_output_json}

# **Technical Diagnosis & Steps:**
# {tech_output_json}
# """
# comm_prompt = ChatPromptTemplate.from_template(COMM_PROMPT_TEMPLATE)


# # --- 3. Create LangChain Structured Output Chains ---
# # This replaces the @client.prompt decorators.
# # We create "runnables" that combine the prompt, LLM, and Pydantic output model.

# rag_chain = create_structured_output_runnable(
#     output_schema=RagOutput, 
#     llm=llms, 
#     prompt=rag_prompt
# )

# tech_chain = create_structured_output_runnable(
#     output_schema=TechOutput, 
#     llm=llms, 
#     prompt=tech_prompt
# )

# comm_chain = create_structured_output_runnable(
#     output_schema=CommOutput, 
#     llm=llms, 
#     prompt=comm_prompt
# )

# # --- 4. Define the LangChain Orchestrator (replaces Crew.kickoff) ---

# async def process_ticket_with_langchain(ticket: TicketIn):
#     """
#     Orchestrates the agent flow using async/await and LangChain runnables.
#     This logic is identical to your 'process_ticket_with_agno' function.
#     """
    
#     # 1. RAG Search (same as before)
#     query = f"{ticket.Ticket_Subject}\n{ticket.Ticket_Description}"
#     # Note: For a true async implementation, search_chroma should be an async function
#     kb_hits = search_chroma(query)

#     # 2. Serialize inputs for the prompts
#     ticket_json = ticket.model_dump_json(indent=2)
#     kb_hits_json = json.dumps(kb_hits, indent=2)

#     # 3. Run Chain 1 (RAG)
#     rag_output = await rag_chain.ainvoke({
#         "ticket_json": ticket_json, 
#         "kb_hits_json": kb_hits_json
#     })
#     rag_output_json = rag_output.model_dump_json(indent=2)

#     # 4. Run Chain 2 (Technical)
#     tech_output = await tech_chain.ainvoke({
#         "rag_output_json": rag_output_json
#     })
#     tech_output_json = tech_output.model_dump_json(indent=2)

#     # 5. Run Chain 3 (Communicator)
#     final_output = await comm_chain.ainvoke({
#         "ticket_json": ticket_json,
#         "rag_output_json": rag_output_json,
#         "tech_output_json": tech_output_json
#     })

#     # 6. Return all structured outputs
#     return {
#         "rag_analysis": rag_output.model_dump(),
#         "technical_plan": tech_output.model_dump(),
#         "final_communication": final_output.model_dump()
#     }

from crewai import Agent, Task, Crew
import asyncio
from llm import llms
from typing import Optional, Dict, Any
from pydantic import BaseModel
from vectordb import search_chroma

# ------------------------------------------------------------------
# In-memory ticket store
# ------------------------------------------------------------------
TICKET_DB: Dict[str, Dict[str, Any]] = {}

# ------------------------------------------------------------------
# Ticket model
# ------------------------------------------------------------------
class TicketIn(BaseModel):
    Customer_ID: Optional[str] = None  # generated automatically if not provided
    Customer_Name: str
    Product_Purchased: Optional[str] = None
    Ticket_Type: str
    Ticket_Subject: str
    Ticket_Description: str
    Ticket_Priority: str
    Ticket_Channel: str
    # date_created: Optional[datetime] = None  # auto-populated in system


# ------------------------------------------------------------------
# Agents
# ------------------------------------------------------------------
agent1 = Agent(
    role="Knowledge Base RAG",
    goal="Retrieve KB answers for customer support tickets",
    backstory="Internal FAQ assistant using ChromaDB",
    verbose=True,
    llm=llms,
)

agent2 = Agent(
    role="Technical Support Specialist",
    goal="Diagnose technical issues, suggest steps, escalate if needed",
    backstory="Conservative, safe instructions for remediation",
    verbose=True,
    llm=llms,
)

agent3 = Agent(
    role="Empathetic Customer Communicator",
    goal="Craft friendly customer-facing replies with empathy",
    backstory="Writes warm, concise, SLA-bound responses",
    verbose=True,
    llm=llms,
)

# ------------------------------------------------------------------
# Crew workflow
# ------------------------------------------------------------------
async def process_ticket_with_crew(ticket: TicketIn):
    query = f"{ticket.Ticket_Subject}\n{ticket.Ticket_Description}"
    kb_hits = search_chroma(query)

    t1 = Task(
        description=(
            f"Answer customer query using KB.\n"
            f"Ticket: {ticket.dict()}\n"
            f"Evidence: {kb_hits}"
        ),
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
        description="Diagnose and suggest steps based on Agent1 output.",
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
        description="Write customer-facing empathetic message and internal note.",
        agent=agent3,
        expected_output=(
            "A JSON object with the following fields:\n"
            "- customer_message: string\n"
            "- internal_note: optional string"
        ),
    )

    crew = Crew(
        agents=[agent1, agent2, agent3],
        tasks=[t1, t2, t3],
    )

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, crew.kickoff)

    return result

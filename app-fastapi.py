from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import pandas as pd
import io,json,os
from typing import List, Optional, Dict, Any
from utils import now_iso,generate_id,log
from agents import TicketIn
from vectordb import add_documents_chroma,kb_collection
from agents import process_ticket_with_crew
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os

# create directories if not exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app = FastAPI(title="Multi-Agent Customer Support (CrewAI + ChromaDB + Groq)")

# mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



TICKET_DB: Dict[str, Dict[str, Any]] = {}

@app.post("/tickets")
async def create_ticket(payload: TicketIn):
    tid = generate_id("t")
    TICKET_DB[tid] = {
            "id": tid,
            "payload": payload.dict(),
        "created_at": now_iso(),
        "history": [],
        "sla": "48 hours"
    }
    log("Ticket created", ticket_id=tid, subject=payload.subject)
    return {"ticket_id": tid}


# app.py (inside /tickets/bulk_upload)
import io

@app.post("/tickets/bulk_upload")
async def upload_tickets(file: UploadFile = File(...)):
    # expect a CSV with customer_id,subject,body
    content = await file.read()
    df = pd.read_csv(pd.compat.StringIO(content.decode()))
    created = []
    for _, row in df.iterrows():
        payload = TicketIn(
            Customer_ID = row["ticket_id"],
            Customer_Name=row["customer_name"],
            Customer_Email=row["customer_email"],
            Product_Purchased=row.get("product_purchased", None),
            Ticket_Type=row["ticket_type"],
            Ticket_Subject=row["ticket_subject"],
            Ticket_Description=row["ticket_description"],
            Ticket_Priority=row.get("ticket_priority", "medium"),
            Ticket_Channel=row.get("ticket_channel", "email")
        )
        tid = generate_id("t")
        TICKET_DB[tid] = {
            "id": tid,
            "payload": payload.dict(),
            "created_at": now_iso(),
            "history": [],
            "sla": "48 hours"
        }
        created.append(tid)
    return {"created": created}





@app.post("/kb/upload")
async def upload_kb(file: UploadFile = File(...), source: Optional[str] = Form(None)):
    content = await file.read()
    text = content.decode()
    # naive chunker: split paragraphs
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    docs = []
    for i, p in enumerate(paras):
        docs.append({
            "id": generate_id('doc'),
            "text": p,
            "source": source or file.filename,
            "chunk_index": i
        })
    add_documents_chroma(docs)
    log("KB uploaded", file=file.filename, chunks=len(docs))
    return {"ingested_chunks": len(docs)}


@app.get("/tickets/{ticket_id}/process")
async def process_ticket(ticket_id: str):
    if ticket_id not in TICKET_DB:
        raise HTTPException(status_code=404, detail="Ticket not found")
    try:
        ticket = TicketIn(**TICKET_DB[ticket_id]["payload"])
        res = await process_ticket_with_crew(ticket)
        return res
    except Exception as e:
        log("Processing error", ticket_id=ticket_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    rec = TICKET_DB.get(ticket_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    return rec


# lightweight health endpoint
@app.get("/health")
async def health():
    kb_count = kb_collection.count()  # Chroma collection count
    return {"status": "ok", "tickets": len(TICKET_DB), "kb_chunks": kb_count}

@app.on_event("startup")
def preload_tickets():
    csv_path = "./dummy_tickets.csv"
    if not os.path.exists(csv_path):
        return
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        payload = TicketIn(
            customer_id=row.get("customer_id", "unknown"),
            subject=row["ticket_subject"],
            body=row["ticket_description"],
            channel=row.get("ticket_channel", "email"),
            priority=row.get("ticket_priority", "normal"),
        )
        tid = generate_id("t")
        TICKET_DB[tid] = {
            "id": tid,
            "payload": payload.dict(),
            "created_at": now_iso(),
            "history": [],
            "sla": "48 hours"
        }
    print(f"✅ Preloaded {len(df)} dummy tickets")

# def preload_tickets():
#     df = pd.read_csv("dummy_tickets.csv")
#     for _, row in df.iterrows():
#         payload = TicketIn(
#             Customer_Name=row["customer_name"],
#             customer_email=row["customer_email"],
#             product_purchased=row.get("product_purchased"),
#             ticket_type=row["ticket_type"],
#             ticket_subject=row["ticket_subject"],
#             ticket_description=row["ticket_description"],
#             ticket_priority=row.get("ticket_priority", "medium"),
#             ticket_channel=row.get("ticket_channel", "email")
#         )
#         tid = generate_id("t")
#         TICKET_DB[tid] = {
#             "id": tid,
#             "payload": payload.dict(),
#             "created_at": now_iso(),
#             "history": [],
#             "sla": "48 hours"
#         }
# -----------------------------
# Example: load dummy KB and tickets (optional convenience)
# -----------------------------
if __name__ == "__main__":
    import asyncio
    async def demo():
        # load example KB into Chroma
        docs = [
            {
                "id": "doc_faq_1",
                "text": "We limit uploads to 2MB by default. To increase the limit, change the upload_max_size in config.",
                "source": "faq"
            },
            {
                "id": "doc_faq_2",
                "text": "If you see HTTP 500 on image uploads, first check server logs for memory errors and ensure image processing library versions match.",
                "source": "runbook"
            },
        ]
        add_documents_chroma(docs)

        # create a ticket
        payload = TicketIn(
            customer_id="cust_123",
            subject="App crashes when uploading image",
            body="Whenever I upload a 5MB image, I get Error 500"
        )
        tid = generate_id('t')
        TICKET_DB[tid] = {
            "id": tid,
            "payload": payload.dict(),
            "created_at": now_iso(),
            "history": [],
            "sla": "24 hours"
        }
        print("Created ticket", tid)
        res = await process_ticket_with_crew(payload)
        print(json.dumps(res.dict(), indent=2))
        # print(res.final_output)

    asyncio.run(demo())

import gradio as gr
import pandas as pd
import asyncio
import json
from agents import process_ticket_with_crew, TicketIn  # Your CrewAI functions
from utils import generate_id, now_iso

# ------------------------
# Global state (instead of Streamlit session_state)
# ------------------------
tickets = {}
kb = []

# ------------------------
# Load CSV for dropdown suggestions
# ------------------------
try:
    df = pd.read_csv("dummy_tickets.csv")
except FileNotFoundError:
    df = pd.DataFrame(columns=[
        "ticket_type", "ticket_subject", "ticket_priority", "ticket_channel"
    ])

df.columns = df.columns.str.strip().str.lower()

ticket_type_options = df["ticket_type"].dropna().unique().tolist() or ["bug", "feature_request", "billing", "technical", "general"]
ticket_subject_options = df["ticket_subject"].dropna().unique().tolist() or ["No subject"]
ticket_priority_options = df["ticket_priority"].dropna().unique().tolist() or ["low", "medium", "high", "urgent"]
ticket_channel_options = df["ticket_channel"].dropna().unique().tolist() or ["email", "chat", "phone", "web"]

# ------------------------
# Functions
# ------------------------
def create_ticket(customer_id, customer_name, customer_email, product_purchased,
                  ticket_type, ticket_subject, ticket_description, ticket_priority, ticket_channel):
    tid = generate_id("t")
    tickets[tid] = {
        "id": tid,
        "Customer_ID": customer_id,
        "Customer_Name": customer_name,
        "Customer_Email": customer_email,
        "Product_Purchased": product_purchased if product_purchased else None,
        "Ticket_Type": ticket_type,
        "Ticket_Subject": ticket_subject,
        "Ticket_Description": ticket_description,
        "Ticket_Priority": ticket_priority,
        "Ticket_Channel": ticket_channel,
        "created_at": now_iso(),
        "history": [],
        "sla": "48 hours"
    }
    return f"✅ Ticket created with ID: {tid}", json.dumps(tickets[tid], indent=2)

def bulk_upload(file_obj):
    if file_obj is None:
        return "❌ No file uploaded", None

    df_bulk = pd.read_csv(file_obj.name)
    df_bulk.columns = df_bulk.columns.str.strip().str.lower()
    created = []
    for _, row in df_bulk.iterrows():
        tid = generate_id("t")
        tickets[tid] = {
            "id": tid,
            "Customer_ID": row.get("customer_id", "unknown"),
            "Customer_Name": row.get("customer_name", "unknown"),
            "Customer_Email": row.get("customer_email", "unknown@example.com"),
            "Product_Purchased": row.get("product_purchased"),
            "Ticket_Type": row.get("ticket_type", "general"),
            "Ticket_Subject": row.get("ticket_subject", "No subject"),
            "Ticket_Description": row.get("ticket_description", "No description"),
            "Ticket_Priority": row.get("ticket_priority", "medium"),
            "Ticket_Channel": row.get("ticket_channel", "email"),
            "created_at": now_iso(),
            "history": [],
            "sla": "48 hours"
        }
        created.append(tid)
    return f"✅ Uploaded {len(created)} tickets", json.dumps({"created": created}, indent=2)

def process_ticket(ticket_id):
    if ticket_id not in tickets:
        return "❌ Ticket ID not found", None, None

    ticket_data = tickets[ticket_id]
    ticket = TicketIn(**ticket_data)

    async def run_process():
        return await process_ticket_with_crew(ticket)

    result = asyncio.run(run_process())
    try:
        for task in result.tasks_output:
            if task.agent == "Empathetic Customer Communicator":
                parsed = json.loads(task.raw)
                customer_message = parsed.get("customer_message", "")
                internal_note = parsed.get("internal_note", "")
                return "✅ Ticket processed with CrewAI agents", customer_message, internal_note
    except Exception as e:
        return f"⚠️ Error extracting customer message: {e}", None, json.dumps(result.dict() if hasattr(result, "dict") else str(result), indent=2)

    return "⚠️ No valid customer message found", None, None

def check_health():
    return json.dumps({
        "status": "ok",
        "tickets": len(tickets),
        "kb_chunks": len(kb)
    }, indent=2)

# ------------------------
# Gradio UI
# ------------------------
with gr.Blocks(title="Multi-Agent Customer Support (CrewAI)") as demo:
    gr.Markdown("# 🎧 Multi-Agent Customer Support System (CrewAI)")

    with gr.Tab("📌 Create Single Ticket"):
        with gr.Row():
            customer_id = gr.Textbox(label="Customer ID", value="1")
            customer_name = gr.Textbox(label="Customer Name", value="Marisa Obrien")
            customer_email = gr.Textbox(label="Customer Email", value="carrollallison@example.com")
            product_purchased = gr.Textbox(label="Product Purchased (optional)", value="GoPro Hero")
        ticket_type = gr.Dropdown(choices=ticket_type_options, label="Ticket Type", value=ticket_type_options[0])
        ticket_subject = gr.Dropdown(choices=ticket_subject_options, label="Ticket Subject", value=ticket_subject_options[0])
        ticket_description = gr.Textbox(label="Ticket Description",value=("I'm having an issue with the Gopro Hero"),lines=4)
        ticket_priority = gr.Dropdown(choices=ticket_priority_options, label="Priority", value=ticket_priority_options[0])
        ticket_channel = gr.Dropdown(choices=ticket_channel_options, label="Channel", value=ticket_channel_options[0])

        create_btn = gr.Button("Create Ticket")
        create_status = gr.Textbox(label="Status")
        create_output = gr.JSON(label="Ticket Data")

        create_btn.click(
            create_ticket,
            inputs=[customer_id, customer_name, customer_email, product_purchased,
                    ticket_type, ticket_subject, ticket_description, ticket_priority, ticket_channel],
            outputs=[create_status, create_output]
        )

    with gr.Tab("📂 Bulk Upload Tickets"):
        csv_file = gr.File(label="Upload CSV file", file_types=[".csv"])
        bulk_btn = gr.Button("Upload Tickets")
        bulk_status = gr.Textbox(label="Status")
        bulk_output = gr.JSON(label="Created Ticket IDs")

        bulk_btn.click(bulk_upload, inputs=[csv_file], outputs=[bulk_status, bulk_output])

    with gr.Tab("⚡ Process Ticket"):
        ticket_id = gr.Textbox(label="Enter Ticket ID")
        process_btn = gr.Button("Process Ticket")
        process_status = gr.Textbox(label="Status")
        customer_reply = gr.Textbox(label="📩 Customer Reply")
        internal_note = gr.Textbox(label="🔒 Internal Note (for support team)")

        process_btn.click(process_ticket, inputs=[ticket_id], outputs=[process_status, customer_reply, internal_note])

    with gr.Tab("💡 Health Check"):
        health_btn = gr.Button("Check System Health")
        health_output = gr.JSON(label="System Health")

        health_btn.click(check_health, outputs=[health_output])
        
    with gr.Column(scale=1):
            # Sidebar-like info panel
            gr.Markdown("## 🤖 Multi-Agent Customer Support Assistant")
            gr.Markdown(
                """
                This system combines:
                - **CrewAI Multi-Agent Orchestration** for ticket handling  
                - **CSV → Knowledge Base ingestion** for contextual replies  
                - **Async Processing (asyncio)** for fast ticket workflows  
                - **Gradio UI** for interaction (Hugging Face Spaces ready)
                """
            )
            gr.Markdown("### Example Workflows")
            gr.Markdown("- Upload tickets from CSV → auto-ingest into KB")
            gr.Markdown("- Create a single ticket → process with CrewAI agents")
            gr.Markdown("- Get customer-facing replies + internal notes")
            gr.Markdown("---")
            gr.Markdown("**Developed By Shyam Kumar**")

            download_btn = gr.Button("Download My Custom File")
            download_file = gr.File(label="Download File", interactive=False)

            # Function that returns your custom file
            def get_custom_file():
                return "dummy_tickets.csv"   # Replace with your actual file path (csv, pdf, etc.)

            # Connect button to file output
            download_btn.click(fn=get_custom_file, inputs=None, outputs=download_file)
# ------------------------
# Launch
# ------------------------
if __name__ == "__main__":
    demo.launch()

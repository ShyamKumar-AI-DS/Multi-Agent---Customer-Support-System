import streamlit as st
import pandas as pd
import asyncio,re,json
from agents import process_ticket_with_crew, TicketIn  # Your CrewAI functions
from utils import generate_id, now_iso
# from typing import Dict, Any


# ------------------------
# Initialize session state
# ------------------------
if "tickets" not in st.session_state:
    st.session_state["tickets"] = {}
if "kb" not in st.session_state:
    st.session_state["kb"] = []

st.set_page_config(page_title="Multi-Agent Customer Support", layout="wide")
st.title("🎧 Multi-Agent Customer Support System (CrewAI)")

# ------------------------
# Load CSV for dropdown suggestions
# ------------------------
try:
    df = pd.read_csv("dummy_tickets.csv")
except FileNotFoundError:
    df = pd.DataFrame(columns=[
        "ticket_type", "ticket_subject", "ticket_priority", "ticket_channel"
    ])

# Normalize column names
df.columns = df.columns.str.strip().str.lower()

# ------------------------
# Bulk Upload Tickets + Auto KB Ingestion
# ------------------------
st.header("📂 Bulk Upload CSV Tickets")
csv_file_bulk = st.file_uploader(
    "Upload CSV file", type=["csv"], key="bulk_csv_uploader"
)

if csv_file_bulk:
    if st.button("Upload Tickets & Create KB"):
        df_bulk = pd.read_csv(csv_file_bulk)
        df_bulk.columns = df_bulk.columns.str.strip().str.lower()

        created = []
        kb_chunks = []

        for i, row in df_bulk.iterrows():
            tid = generate_id("t")
            ticket_dict = {
                # "id": tid,
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

            # Save ticket
            # st.session_state["tickets"][tid] = ticket_dict
            # created.append(tid)

            # Convert ticket into KB chunk
            kb_text = (
                f"Ticket Subject: {ticket_dict['Ticket_Subject']}\n"
                f"Description: {ticket_dict['Ticket_Description']}\n"
                f"Priority: {ticket_dict['Ticket_Priority']}, "
                f"Channel: {ticket_dict['Ticket_Channel']}"
            )
            kb_chunks.append({
                "id": generate_id("doc"),
                "text": kb_text,
                "source": csv_file_bulk.name,
                "chunk_index": i
            })

        # Store KB
        st.session_state["kb"].extend(kb_chunks)

        st.success(f"✅ Uploaded {len(created)} tickets and {len(kb_chunks)} KB chunks")
        # st.json({"created_tickets": created, "ingested_kb_chunks": len(kb_chunks)})

# ------------------------
# Create Single Ticket
# ------------------------
# st.header("📌 Create Single Ticket")
with st.form("create_ticket_form"):
    customer_id = st.text_input("Customer ID", "1")
    customer_name = st.text_input("Customer Name", "Marisa Obrien")
    customer_email = st.text_input("Customer Email", "carrollallison@example.com")
    product_purchased = st.text_input("Product Purchased (optional)", "GoPro Hero")

    ticket_type = st.selectbox(
        "Ticket Type",
        options=df["ticket_type"].dropna().unique().tolist() or ["bug", "feature_request", "billing", "technical", "general"]
    )
    ticket_subject = st.selectbox(
        "Ticket Subject",
        options=df["ticket_subject"].dropna().unique().tolist() or ["No subject"]
    )
    ticket_description = st.text_area(
        "Ticket Description",
        "I'm having an issue with my GoPro Hero..."
    )
    ticket_priority = st.selectbox(
        "Priority",
        options=df["ticket_priority"].dropna().unique().tolist() or ["low", "medium", "high", "urgent"],
        index=1
    )
    ticket_channel = st.selectbox(
        "Channel",
        options=df["ticket_channel"].dropna().unique().tolist() or ["email", "chat", "phone", "web"]
    )

    submitted = st.form_submit_button("Create Ticket")

    if submitted:
        tid = generate_id("t")
        st.session_state["tickets"][tid] = {
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
        st.success(f"✅ Ticket created with ID: {tid}")
        st.json(st.session_state["tickets"][tid])


# ------------------------
# Process Ticket
# ------------------------

st.header("⚡ Process Ticket")

# Dropdown instead of manual input
if st.session_state["tickets"]:
    ticket_id = st.selectbox(
        "Select Ticket ID to Process",
        options=list(st.session_state["tickets"].keys())
    )

    if st.button("Process Ticket"):
        ticket_data = st.session_state["tickets"][ticket_id]
        ticket = TicketIn(**ticket_data)

        async def run_process():
            return await process_ticket_with_crew(ticket)

        result = asyncio.run(run_process())
        st.success(f"✅ Ticket {ticket_id} processed with CrewAI agents")

        # Display only the final customer message (Agent3)
        try:
            for task in result.tasks_output:
                if task.agent == "Empathetic Customer Communicator":
                    raw_text = task.raw.strip()

                    # ✅ Extract only the JSON block between ```json ... ```
                    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                    if match:
                        clean_json = match.group(0)
                        parsed = json.loads(clean_json)

                        customer_message = parsed.get("customer_message", "")
                        internal_note = parsed.get("internal_note", "")

                        st.subheader("📩 Customer Reply")
                        st.write(customer_message)

                        if internal_note:
                            with st.expander("🔒 Internal Note (for support team)"):
                                st.write(internal_note)
                    else:
                        st.warning("⚠️ Could not extract JSON from agent output.")
                    break
        except Exception as e:
            st.error(f"⚠️ Error extracting customer message: {e}")
            if hasattr(result, "dict"):
                st.json(result.dict())
            else:
                st.write(result)
else:
    st.warning("⚠️ No tickets available. Please create or upload one first.")


# ------------------------
# Health Check
# ------------------------
st.header("💡 Health Check")
if st.button("Check System Health"):
    st.json({
        "status": "ok",
        "tickets": len(st.session_state["tickets"]),
        "kb_chunks": len(st.session_state.get("kb", []))
    })


# ------------------------
# Sidebar
# ------------------------
with st.sidebar:
    st.subheader("🤖 Multi-Agent Customer Support Assistant")
    st.info("""
    This system combines:
    - **CrewAI Multi-Agent Orchestration** for ticket handling
    - **CSV → Knowledge Base ingestion** for contextual replies
    - **Async Processing (asyncio)** for fast ticket workflows
    - **Streamlit UI** for interaction
    """)

    # Example usage
    st.markdown("💡 **Example Workflows:**")
    st.markdown("- Upload tickets from CSV → auto-ingest into KB")
    st.markdown("- Create a single ticket → process with CrewAI agents")
    st.markdown("- Get customer-facing replies + internal notes")
    
    pdf_path1 = "./dummy_tickets.csv"

    try:
        with open(pdf_path1, "rb") as file:
            st.download_button(
                label="📄 Download Sample Tickets Data",
                data=file,
                file_name="Dummy_Tickets_Data.csv",
                mime="application/pdf"
            )
    except Exception:
        pass
    st.markdown("---")
    st.markdown("🧠 **Powered by**")
    st.markdown("- Python + Streamlit")
    st.markdown("- Pandas (CSV handling)")
    st.markdown("- CrewAI Agents")
    st.markdown("- Custom Knowledge Base Builder")

    st.markdown("---")
    st.caption("📂 Upload tickets → 🧠 Build KB → ⚡ Process with AI Agents")
    st.caption("Developed By Shyam Kumar")

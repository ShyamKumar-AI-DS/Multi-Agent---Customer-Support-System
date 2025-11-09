import streamlit as st
import pandas as pd
import asyncio
import json
from agents import process_ticket_with_autogen, TicketIn  # Your CrewAI functions
from utils import generate_id, now_iso

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
# Create Single Ticket
# ------------------------
st.header("📌 Create Single Ticket")
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
# Bulk Upload Tickets
# ------------------------
st.header("📂 Bulk Upload CSV Tickets")
csv_file_bulk = st.file_uploader(
    "Upload CSV file", type=["csv"], key="bulk_csv_uploader"
)

if csv_file_bulk:
    if st.button("Upload Tickets"):
        df_bulk = pd.read_csv(csv_file_bulk)
        df_bulk.columns = df_bulk.columns.str.strip().str.lower()
        created = []
        for _, row in df_bulk.iterrows():
            tid = generate_id("t")
            st.session_state["tickets"][tid] = {
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
        st.success(f"✅ Uploaded {len(created)} tickets")
        st.json({"created": created})

st.header("⚡ Process Ticket")
ticket_id = st.text_input("Enter Ticket ID to Process")

if st.button("Process Ticket"):
    if ticket_id in st.session_state["tickets"]:
        ticket_data = st.session_state["tickets"][ticket_id]
        ticket = TicketIn(**ticket_data)

        async def run_process():
            return await process_ticket_with_autogen(ticket)

        result = asyncio.run(run_process())
        st.success("✅ Ticket processed with CrewAI agents")

        # Display only the final customer message (Agent3)
        # Extract only the final customer message (Agent3 output)
        try:
            for task in result.tasks_output:
                if task.agent == "Empathetic Customer Communicator":
                    import json
                    parsed = json.loads(task.raw)

                    customer_message = parsed.get("customer_message", "")
                    internal_note = parsed.get("internal_note", "")

                    st.subheader("📩 Customer Reply")
                    st.write(customer_message)

                    if internal_note:
                        with st.expander("🔒 Internal Note (for support team)"):
                            st.write(internal_note)
                    break
        except Exception as e:
            st.error(f"⚠️ Error extracting customer message: {e}")
            if hasattr(result, "dict"):
                st.json(result.dict())
            else:
                st.write(result)
    else:
        st.error("❌ Ticket ID not found")

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

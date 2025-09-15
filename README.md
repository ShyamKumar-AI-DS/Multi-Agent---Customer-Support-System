# 🎧 Multi-Agent Customer Support System (CrewAI + Streamlit)

This project is an **AI-powered customer support system** that leverages **CrewAI multi-agent orchestration** to process customer tickets, generate empathetic replies, and assist support teams with internal notes.

It provides an interactive **Streamlit UI** for:

- 📂 Bulk uploading tickets from CSV  
- 🧠 Converting tickets into a Knowledge Base (KB)  
- 📌 Creating single tickets dynamically  
- ⚡ Processing tickets with AI agents (customer replies + internal notes)  
- 💡 Performing system health checks  

---

## 🚀 Features

### 📂 Bulk Ticket Upload
Upload CSV files containing customer tickets. The system auto-ingests them into a knowledge base for contextual replies.

### 📌 Single Ticket Creation
Create a new support ticket manually through a simple form.

### ⚡ AI-Powered Ticket Processing
Uses **CrewAI multi-agent system** to analyze tickets and generate:  
- 📩 A **customer-facing empathetic reply**  
- 🔒 An **internal note for support agents**  

### 🧠 Knowledge Base (KB)
Ticket descriptions are automatically converted into KB chunks, enabling more context-aware AI responses.

### 💡 Health Check
Quick system status: number of tickets + KB chunks available.

### 📊 Streamlit Sidebar
Provides instructions, sample data download, and system details.

---

## 📦 Future Improvements

- ✅ Database integration (SQLite/Postgres) for persistence  
- ✅ Vector DB for semantic ticket retrieval (RAG)  
- ✅ Multi-user authentication  
- ✅ Dashboard for analytics  

---

## 👨‍💻 Developer

- **Author**: Shyam Kumar  
- **Department**: Artificial Intelligence & Data Science  
- **Focus**: Generative AI & Multi-Agent Systems  

---

## 🧠 Powered By

- Python + Streamlit  
- Pandas  
- CrewAI Agents  
- AsyncIO  

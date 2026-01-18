# 🎧 Multi-Agent Customer Support System (CrewAI)

This project is an **AI-powered customer support system** that leverages **CrewAI multi-agent orchestration** to process customer tickets, generate empathetic replies, and assist support teams with internal notes.

It provides an interactive **Gradio UI** for:

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

### 📊 Architecture Diagram

  <img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/145a6ef0-5f76-4d35-bd7e-509af06627d0" />

---

### 📊 Outputs

<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/7cf12e88-a385-424a-888e-70b333398ea4" />


<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/c3db4296-c85b-4f38-b980-3d29de90be2d" />


## 🧠 Powered By

- Python + Pandas    
- CrewAI Agents  
- AsyncIO + Streamlit
- Groq API Inference (OPENAI 20B OSS)

## 📦 Future Improvements

- ✅ Database integration (SQLite/Postgres) for persistence  
- ✅ Vector DB for semantic ticket retrieval (RAG)  
- ✅ Multi-user authentication  
- ✅ Dashboard for analytics  

---

## 👨‍💻 Developer

- **Author**: Shyam Kumar A

--- 

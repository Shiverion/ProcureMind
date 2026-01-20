import streamlit as st
import sys
import os

st.set_page_config(
    page_title="ProcureMind - Procurement Intelligence",
    page_icon="🧠",
    layout="wide"
)

# --- DATABASE INIT ---
# Ensure tables exist (crucial for Cloud deployment)
from logic.database import engine, Base
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    # This might fail if pgvector extension isn't installed on fresh Postgres
    st.error(f"Database Init Error: {e}")

st.title("🧠 ProcureMind")
st.markdown("### Transform messy RFQs into structured, comparable data.")

st.sidebar.success("Select a tool above.")

st.markdown("""
Welcome to **ProcureMind**, your personal procurement assistant.

### 🚀 Get Started
1.  **Parse RFQ**: Go to the **RFQ Parser** to convert an email into a structured list.
2.  **Manage Catalog**: Add **Suppliers** and **Products** to build your knowledge base.
3.  **Log Quotes**: Record price quotes from suppliers for specific products.
4.  **Compare**: Use the **Comparison Dashboard** to make data-driven decisions.

### 📂 How it works
ProcureMind uses **Gemini 2.0 Flash** to understand search intents and extract information from unstructured text. Your data is stored locally in **PostgreSQL**, allowing for fast, semantic search across your entire procurement history.
""")

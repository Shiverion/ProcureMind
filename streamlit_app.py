import streamlit as st
import sys
import os

st.set_page_config(
    page_title="ProcureMind - Procurement Intelligence",
    page_icon="🧠",
    layout="wide"
)

st.sidebar.success("Select a tool above.")

st.markdown("""
Welcome to **ProcureMind**, your personal procurement assistant.

### 🚀 Get Started
1.  **Parse RFQ**: Go to the **RFQ Parser** to convert an email into a structured list.
2.  **Manage Catalog**: Add **Suppliers** and **Products** to build your knowledge base.
3.  **Log Quotes**: Record price quotes from suppliers for specific products.
4.  **Compare**: Use the **Comparison Dashboard** to make data-driven decisions.

### 📂 How it works
ProcureMind uses **Gemini 2.0 Flash** to extract information from unstructured text. Your data is stored in **Supabase**, leveraging its RESTful API and **pgvector** support for fast, semantic search across your entire procurement history.
""")

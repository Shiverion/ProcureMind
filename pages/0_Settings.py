import streamlit as st
import os

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings")

st.write("Configure your AI API key here. This allows the app to process your RFQs using your own quota.")

# --- API KEY MANAGEMENT ---
st.subheader("🔑 Google Gemini API Key")

# Check if key exists in session state or env
current_key = st.session_state.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", ""))

# Mask the key for display if it exists
display_value = current_key
if current_key and len(current_key) > 5:
   # If it's loaded from env, maybe we don't show it at all, or just mask it. 
   # But for a wrapper, usually we want the user to paste theirs.
   pass 

api_key_input = st.text_input(
    "Enter your Google Gemini API Key", 
    value=current_key if current_key else "",
    type="password",
    help="Get your key from https://aistudio.google.com/app/apikey"
)

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("Save Key", type="primary"):
        if api_key_input.startswith("AIza"):
            st.session_state["GOOGLE_API_KEY"] = api_key_input
            st.success("API Key saved for this session!")
            st.rerun()
        else:
            st.error("Invalid Key format. Should start with 'AIza'.")

with col2:
    if st.button("Clear Key"):
        if "GOOGLE_API_KEY" in st.session_state:
            del st.session_state["GOOGLE_API_KEY"]
            st.rerun()

st.divider()

# --- DATABASE CONNECTION ---
st.subheader("🗄️ Database Connection")
st.write("Connect to your own PostgreSQL database (Cloud or Local).")

current_db = st.session_state.get("DATABASE_URL", "")

# Masking logic could be added here, but usually DB URLs are long and complex.
# We'll keep it as a password field to be safe.

db_url_input = st.text_input(
    "Enter Database Connection String (URI)",
    value=current_db,
    type="password",
    placeholder="postgresql://user:password@host:port/dbname",
    help="Example: postgresql://postgres:password@db.supabase.co:5432/postgres"
)

col_db1, col_db2 = st.columns([1, 4])
with col_db1:
    if st.button("Connect DB", type="primary"):
        if db_url_input.startswith("postgres"):
            st.session_state["DATABASE_URL"] = db_url_input
            # Clear cached engine to force reconnection
            st.cache_resource.clear()
            st.success("Database URL saved! Reconnecting...")
            st.rerun()
        else:
            st.error("Invalid URL. Must start with 'postgres://' or 'postgresql://'")

with col_db2:
    if st.button("Reset DB"):
        if "DATABASE_URL" in st.session_state:
            del st.session_state["DATABASE_URL"]
            st.cache_resource.clear()
            st.rerun()

st.divider()

# --- STATUS INDICATOR ---
col_stat1, col_stat2 = st.columns(2)

with col_stat1:
    if "GOOGLE_API_KEY" in st.session_state:
        st.success("✅ AI Service: Ready (Session)")
    elif os.getenv("GOOGLE_API_KEY") or (st.secrets.get("GOOGLE_API_KEY")):
        st.info("✅ AI Service: Ready (System)")
    else:
        st.warning("⚠️ AI Service: Not Configured")

with col_stat2:
    if "DATABASE_URL" in st.session_state:
        st.success("✅ Database: Ready (Session)")
    elif os.getenv("DATABASE_URL") or (st.secrets.get("postgres")):
        st.info("✅ Database: Ready (System)")
    else:
        st.warning("⚠️ Database: Using Temporary Local SQLite")

st.info("""
**Note:** Start fresh by clearing these settings. Your secrets are stored temporarily in your browser session.
""")

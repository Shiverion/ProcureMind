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

# --- SUPABASE CONNECTION ---
st.subheader("☁️ Supabase Connection (REST API)")
st.write("Connect to your Supabase project using the API URL and Anon Key.")

current_url = st.session_state.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
current_key = st.session_state.get("SUPABASE_ANON_KEY", os.getenv("SUPABASE_ANON_KEY", ""))

supa_url_input = st.text_input(
    "Supabase Project URL",
    value=current_url,
    placeholder="https://your-project.supabase.co",
    help="Find this in Project Settings -> API"
)

supa_key_input = st.text_input(
    "Supabase Anon Key",
    value=current_key,
    type="password",
    placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    help="Find this in Project Settings -> API"
)

col_db1, col_db2 = st.columns([1, 4])
with col_db1:
    if st.button("Connect Supabase", type="primary"):
        if supa_url_input.startswith("https://") and len(supa_key_input) > 20:
            st.session_state["SUPABASE_URL"] = supa_url_input
            st.session_state["SUPABASE_ANON_KEY"] = supa_key_input
            # Clear cached client to force reconnection
            st.cache_resource.clear()
            st.success("Supabase credentials saved!")
            st.rerun()
        else:
            st.error("Invalid URL or Key format.")

with col_db2:
    if st.button("Reset Connection"):
        if "SUPABASE_URL" in st.session_state:
            del st.session_state["SUPABASE_URL"]
        if "SUPABASE_ANON_KEY" in st.session_state:
            del st.session_state["SUPABASE_ANON_KEY"]
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
    if "SUPABASE_URL" in st.session_state and "SUPABASE_ANON_KEY" in st.session_state:
        st.success("✅ Supabase: Ready (Session)")
    elif os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
        st.info("✅ Supabase: Ready (Environment)")
    elif "SUPABASE_URL" in st.secrets and "SUPABASE_ANON_KEY" in st.secrets:
        st.info("✅ Supabase: Ready (Secrets)")
    else:
        st.warning("⚠️ Supabase: Not Configured")

st.info("""
**Note:** Start fresh by clearing these settings. Your secrets are stored temporarily in your browser session.
""")

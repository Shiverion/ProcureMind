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

# --- STATUS INDICATOR ---
if "GOOGLE_API_KEY" in st.session_state:
    st.success("✅ AI Service is Ready (Using Session Key)")
elif os.getenv("GOOGLE_API_KEY"):
    st.info("✅ AI Service is Ready (Using Environment Variable)")
else:
    st.warning("⚠️ AI Service is NOT Configured. Please enter a key.")

st.info("""
**Note:** Your API key is stored only in your browser's temporary session. 
It is not saved to our database. If you refresh the page, you may need to enter it again.
""")

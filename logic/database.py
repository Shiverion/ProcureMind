import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# --- SUPABASE CONFIGURATION ---

def get_supabase_credentials():
    """
    Retrieves Supabase URL and Anon Key with priority: Session > Secrets > Env.
    """
    # 1. Check Session State (Dynamic Client-Side)
    session_url = st.session_state.get("SUPABASE_URL")
    session_key = st.session_state.get("SUPABASE_ANON_KEY")
    
    if session_url and session_key:
        return session_url, session_key

    # 2. Check Streamlit Secrets
    try:
        if "SUPABASE_URL" in st.secrets and "SUPABASE_ANON_KEY" in st.secrets:
            return st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"]
    except Exception:
        pass

    # 3. Check Environment Variables
    env_url = os.getenv("SUPABASE_URL")
    env_key = os.getenv("SUPABASE_ANON_KEY")
    
    if env_url and env_key:
        return env_url, env_key
        
    return None, None

@st.cache_resource
def get_supabase() -> Client:
    """
    Creates and caches the Supabase client.
    Clearing cache (st.cache_resource.clear()) forces re-initialization.
    """
    url, key = get_supabase_credentials()
    
    if not url or not key:
        # If credentials are missing, we might still want to return a dummy or raise warning
        # For now, let's return None and handle it in pages
        return None
        
    return create_client(url, key)

# --- UTILS / MODELS REPRESENTATION ---
# While we don't use SQLAlchemy ORM for REST, these names help maintain alignment
TABLE_SUPPLIERS = "suppliers"
TABLE_PRODUCTS = "products"
TABLE_QUOTES = "quotes"
TABLE_RFQS = "rfqs"

def get_db():
    """
    Compatibility helper for pages that used 'with get_db() as db'.
    Since Supabase client is persistent and doesn't use sessions in the same way,
    we just return the client.
    """
    client = get_supabase()
    if client:
        yield client
    else:
        # Fallback for pages to handle None
        yield None

# --- LEGACY / FALLBACK (Optional) ---
# If the user still wants local SQLite, we'd need to keep SQLAlchemy code here.
# But since the goal is to use RESTful API, we prioritize the Supabase client.

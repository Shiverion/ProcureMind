import os
from dotenv import load_dotenv
import streamlit as st
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Date, TIMESTAMP, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

load_dotenv()

# --- DATABASE CONNECTION LOGIC ---
def get_database_url():
    """
    Retrieves DB URL with priority: Session > Secrets > Env > Fallback.
    """
    # 1. Check Session State (Dynamic Client-Side)
    if st.session_state.get("DATABASE_URL"):
        return st.session_state["DATABASE_URL"]

    # 2. Check Streamlit Secrets
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
        if "postgres" in st.secrets and "url" in st.secrets["postgres"]:
            return st.secrets["postgres"]["url"]
    except Exception:
        pass 

    # 3. Check Environment Variable
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
        
    # 4. Fallback (Local)
    return "sqlite:///./procuremind.db"

@st.cache_resource
def get_engine(url_override=None):
    """
    Creates and caches the SQLAlchemy engine. 
    Clearing cache (st.cache_resource.clear()) forces reconnection.
    """
    db_url = url_override if url_override else get_database_url()
    
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    return create_engine(db_url)

# Legacy global Base for models
Base = declarative_base()

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_info = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    specs = Column(Text)
    embedding = Column(Vector(768)) # Gemini embedding size
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer) # Linked to Product.id
    supplier_id = Column(Integer) # Linked to Supplier.id
    price = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String, default="USD")
    uom = Column(Text)
    source_url = Column(Text)
    note = Column(Text)
    quote_date = Column(Date, server_default=func.current_date())
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class RFQ(Base):
    __tablename__ = "rfqs"
    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(String, nullable=False)
    parsed_json = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

# --- DYNAMIC SESSION MANAGEMENT ---
# To support dynamic engines, we must not rely on a global SessionLocal factory (which binds to one engine).
# Instead, we create the session factory on the fly or scope it to the current cached engine.

def get_db():
    engine = get_engine()
    # Create tables if not exist (Lazy Init)
    # Ideally should be done once, but declarative_base metadata binding needs engine
    # We can try/except this or rely on st.cache_resource side-effects
    # For MVP safety, we just bind and make session
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Helper for non-generator usage (e.g. init script)
engine = get_engine() # This initiates the default/cached engine globally for imports
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

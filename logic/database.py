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
# Prioritize Streamlit Secrets (Cloud), fallback to .env (Local)
def get_database_url():
    # 1. Check Streamlit Secrets
    try:
        # Most cloud providers use "DATABASE_URL" or "postgres" as key
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
        if "postgres" in st.secrets and "url" in st.secrets["postgres"]:
            return st.secrets["postgres"]["url"]
    except FileNotFoundError:
        pass # No secrets file found
    except Exception:
        pass # Secrets accessed outside streamlit context
        
    # 2. Check Environment Variable
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
        
    return None

DATABASE_URL = get_database_url()

if not DATABASE_URL:
    # Fail-safe: Use local SQLite so app doesn't crash on Cloud without secrets
    # Note: On Streamlit Cloud without persistence, this will reset on reboot.
    DATABASE_URL = "sqlite:///./procuremind.db"
    
# Handle Postgres 'postgres://' vs 'postgresql://' for SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

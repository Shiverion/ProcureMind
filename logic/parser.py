import os
import json
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Use gemini-2.5-flash (Available per list_models)
PARSER_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "models/text-embedding-004"

def get_api_key():
    """
    Retrieves API Key from Session State (User provided) or Environment (Local dev).
    Raises generic error if missing.
    """
    # 1. Check Session State (User Input)
    if "GOOGLE_API_KEY" in st.session_state and st.session_state["GOOGLE_API_KEY"]:
        return st.session_state["GOOGLE_API_KEY"]
    
    # 2. Check Streamlit Secrets (Cloud Deployment)
    try:
        if st.secrets.get("GOOGLE_API_KEY"):
            return st.secrets["GOOGLE_API_KEY"]
    except:
        pass # Not running in Streamlit cloud or secrets file not found
        
    # 3. Check Environment Variable (Local Dev)
    env_key = os.getenv("GOOGLE_API_KEY")
    if env_key:
        return env_key
        
    st.error("⚠️ Google Gemini API Key is missing. Please go to **Settings** page and enter your key.")
    st.stop()
    return None

def parse_rfq_text(text: str):
    """
    Parses RFQ text into structured JSON using Gemini 2.0 Flash.
    """
    api_key = get_api_key()
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(PARSER_MODEL)
    
    prompt = f"""
    Act as a procurement expert. Parse the following RFQ email text into a structured JSON format.
    1. Generate a short, descriptive TITLE for this RFQ (e.g., "RFQ from [Company] - [Date]" or "Request for [Item Categories]").
    2. Extract each item with ALL available details, including Item Code, Quantity, Unit of Measure (UOM), Name/Description, Brand, and Specs.
    
    RFQ TEXT:
    {text}
    
    RESPONSE FORMAT (JSON ONLY):
    {{
        "title": "string",
        "items": [
            {{
                "item_code": "string (or null if missing)",
                "description": "string (full description)",
                "quantity": "number (or null)",
                "uom": "string (e.g., Each, Pail, Box)",
                "name": "string (short name)",
                "brand": "string",
                "specs": "string"
            }}
        ]
    }}
    """
    
    response = model.generate_content(prompt)
    
    # Extract JSON from response text (handling potential markdown formatting)
    content = response.text
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    try:
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {{"items": [], "error": str(e)}}

def generate_embedding(text: str):
    """
    Generates a 768-dimension embedding using Gemini's embedding model.
    """
    api_key = get_api_key()
    genai.configure(api_key=api_key)

    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']

def generate_email_response(original_text: str, quote_data: str, user_instructions: str = ""):
    """
    Generates a response email based on the original RFQ and the constructed quote.
    """
    api_key = get_api_key()
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(PARSER_MODEL)
    
    prompt = f"""
    Act as a Professional Procurement Officer. Write a reply to the email below, attaching the following commercial quote/proposal.
    
    ORIGINAL EMAIL:
    {original_text}
    
    OUR QUOTE DATA:
    {quote_data}
    
    USER SPECIFIC INSTRUCTIONS:
    {user_instructions}
    
    INSTRUCTIONS:
    1. Be polite and professional.
    2. Acknowledge the original request.
    3. Structure the email body clearly with these headers/sections:
       - 1. Commercial Offer: Summarize the proposal/total and refer to the attachment.
       - 2. Scope & Terms: Outline delivery, payment, or validity terms (use standard defaults or user context).
       - 3. Remarks (Optional): Any extra notes.
    4. Do NOT include the full quote table.
    5. Write in PLAIN TEXT (No Markdown tables).
    """
    
    response = model.generate_content(prompt)
    return response.text

def refine_email_response(current_draft: str, feedback: str):
    """
    Refines an existing email draft based on user feedback.
    """
    api_key = get_api_key()
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(PARSER_MODEL)
    
    prompt = f"""
    Act as a Professional Procurement Officer. 
    Refine the following email draft based strictly on the user's feedback.
    
    CURRENT DRAFT:
    {current_draft}
    
    USER FEEDBACK / INSTRUCTIONS:
    {feedback}
    
    INSTRUCTIONS:
    1. Rewrite the email incorporating the feedback.
    2. Maintain the structure: Commercial Offer, Scope & Terms, Remarks.
    3. Output ONLY the new email body (Plain Text).
    """
    
    response = model.generate_content(prompt)
    return response.text

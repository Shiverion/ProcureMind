import streamlit as st
import pandas as pd
import json
from logic.parser import parse_rfq_text
from logic.database import SessionLocal, RFQ
from sqlalchemy.orm.attributes import flag_modified

st.set_page_config(page_title="RFQ Parser", page_icon="📝", layout="wide")

st.title("📝 RFQ Manager")
st.write("Import RFQs via AI parsing or define them manually.")

tab1, tab2, tab3 = st.tabs(["🤖 AI Parser", "✍️ Manual Input", "✏️ Edit Saved"])

# --- TAB 1: AI PARSER ---
with tab1:
    st.write("Paste the raw text of an RFQ email below to extract structured items.")
    # Input area
    rfq_text = st.text_area("RFQ Email Content", height=300, placeholder="Dear Admin, we need the following items...")

    if st.button("Parse RFQ", type="primary"):
        if rfq_text:
            with st.spinner("Gemini is analyzing the RFQ..."):
                parsed_data = parse_rfq_text(rfq_text)
                
                if "items" in parsed_data and parsed_data["items"]:
                    st.session_state['parsed_rfq'] = parsed_data
                    st.session_state['rfq_text'] = rfq_text
                    st.success(f"Successfully extracted {len(parsed_data['items'])} items!")
                else:
                    st.error("Failed to parse RFQ. Please try again or check your API key.")
        else:
            st.warning("Please paste some text first.")
            
    # Display parsed data if available in session state
    if 'parsed_rfq' in st.session_state:
        st.divider()
        st.subheader("Extracted Data")
        
        # Title logic
        current_title = st.session_state['parsed_rfq'].get("title", f"RFQ - {pd.Timestamp.now().strftime('%Y-%m-%d')}")
        rfq_title = st.text_input("RFQ Title", value=current_title)
        
        df = pd.DataFrame(st.session_state['parsed_rfq']["items"])
        st.dataframe(df, use_container_width=True)
        
        # Save to History
        if st.button("Save to History"):
            db = SessionLocal()
            
            # Update title in parsed_json before saving
            final_data = st.session_state['parsed_rfq']
            final_data['title'] = rfq_title
            
            new_rfq = RFQ(raw_text=st.session_state['rfq_text'], parsed_json=final_data)
            db.add(new_rfq)
            db.commit()
            st.success("RFQ saved to history successfully!")
            db.close()
            # Clear state after save
            del st.session_state['parsed_rfq']
            del st.session_state['rfq_text']

# --- TAB 2: MANUAL INPUT ---
with tab2:
    st.write("Define your RFQ items manually.")
    
    manual_title = st.text_input("RFQ Title / Reference", placeholder="Manual RFQ - Jan 20")
    
    # Initialize empty DF structure
    if "manual_df" not in st.session_state:
        st.session_state.manual_df = pd.DataFrame(columns=[
            "item_code", "description", "quantity", "uom", "name", "brand", "specs"
        ])

    # --- Column & Row Management ---
    col_man1, col_man2, col_man3, col_man4 = st.columns([1.5, 0.5, 1.5, 0.5])
    
    with col_man1:
        new_col_name = st.text_input("Add New Column", placeholder="e.g. Color", label_visibility="collapsed")
    with col_man2:
        if st.button("➕ Add"):
            if new_col_name and new_col_name not in st.session_state.manual_df.columns:
                st.session_state.manual_df[new_col_name] = ""
                st.rerun()
                
    with col_man3:
        if not st.session_state.manual_df.columns.empty:
            col_to_rename = st.selectbox("Select Col to Rename", st.session_state.manual_df.columns, label_visibility="collapsed")
            rename_val = st.text_input("New Name", placeholder="New Name", label_visibility="collapsed")
    with col_man4:
        if st.button("✏️ Rename"):
            if col_to_rename and rename_val and rename_val not in st.session_state.manual_df.columns:
                 st.session_state.manual_df = st.session_state.manual_df.rename(columns={col_to_rename: rename_val})
                 st.rerun()
    
    if st.button("🗑️ Clear All Rows"):
        st.session_state.manual_df = st.session_state.manual_df.iloc[0:0] # Keep columns, empty rows
        st.rerun()

    st.caption("💡 Tip: Select a row and press 'Delete' key or use the trash icon when hovering to remove rows.")

    edited_df = st.data_editor(
        st.session_state.manual_df,
        num_rows="dynamic",
        column_config={
            "item_code": "Item Code",
            "description": "Description",
            "quantity": st.column_config.NumberColumn("Qty", min_value=0),
            "uom": "UOM",
            "name": "Short Name",
            "brand": "Brand",
            "specs": "Specs"
        },
        use_container_width=True
    )
    
    # Sync edits back to session state
    if not edited_df.equals(st.session_state.manual_df):
        st.session_state.manual_df = edited_df
    
    if st.button("Save Manual RFQ", type="primary"):
        if not edited_df.empty:
            # Convert NaN to None/Empty
            clean_data = edited_df.where(pd.notnull(edited_df), None).to_dict(orient="records")
            
            parsed_json = {"items": clean_data}
            
            db = SessionLocal()
            # Use title as raw_text for reference
            new_rfq = RFQ(raw_text=f"MANUAL ENTRY: {manual_title}", parsed_json=parsed_json)
            db.add(new_rfq)
            db.commit()
            st.success(f"Saved manual RFQ with {len(clean_data)} items!")
            db.close()
        else:
            st.warning("Please add at least one item.")

# --- TAB 3: EDIT SAVED RFQ ---
with tab3:
    st.write("Edit an existing RFQ from your database.")
    
    db = SessionLocal()
    all_rfqs = db.query(RFQ).order_by(RFQ.created_at.desc()).all()
    
    if not all_rfqs:
        st.info("No saved RFQs found.")
    else:
        # Select RFQ to edit
        rfq_to_edit = st.selectbox(
            "Select RFQ to Edit", 
            options=all_rfqs, 
            format_func=lambda x: f"{x.parsed_json.get('title', 'RFQ')} (#{x.id} - {x.created_at.strftime('%Y-%m-%d')})" if x.parsed_json and 'title' in x.parsed_json else f"RFQ #{x.id} - {x.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        
        if rfq_to_edit and rfq_to_edit.parsed_json and "items" in rfq_to_edit.parsed_json:
            # Load items into Session State for editing distinct from Manual Tab
            current_items = rfq_to_edit.parsed_json["items"]
            
            # --- Title Editor ---
            new_title = st.text_input("Edit RFQ Title", value=rfq_to_edit.parsed_json.get('title', ''))
            
            # --- Table Editor ---
            edit_df = pd.DataFrame(current_items)
            
            edited_saved_df = st.data_editor(
                edit_df,
                num_rows="dynamic",
                use_container_width=True,
                key=f"editor_{rfq_to_edit.id}" # Unique key
            )
            
            if st.button("💾 Update RFQ", type="primary"):
                # logic to update
                updated_items = edited_saved_df.where(pd.notnull(edited_saved_df), None).to_dict(orient="records")
                
                # Update JSON blob
                rfq_to_edit.parsed_json["items"] = updated_items
                rfq_to_edit.parsed_json["title"] = new_title
                
                flag_modified(rfq_to_edit, "parsed_json")
                
                db.commit()
                st.success("RFQ updated successfully!")
                st.rerun()
                
    db.close()

# --- RECENT RFQS ---
st.divider()
st.subheader("📜 Recent RFQs")
db = SessionLocal()
recent_rfqs = db.query(RFQ).order_by(RFQ.created_at.desc()).limit(5).all()
for r in recent_rfqs:
    with st.expander(f"RFQ from {r.created_at.strftime('%Y-%m-%d %H:%M')}"):
        st.text(r.raw_text[:200] + "...")
        if r.parsed_json:
            st.json(r.parsed_json)
db.close()

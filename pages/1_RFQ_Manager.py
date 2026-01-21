import streamlit as st
import pandas as pd
from logic.parser import parse_rfq_text
from logic.database import get_supabase

st.set_page_config(page_title="RFQ Parser", page_icon="📝", layout="wide")

st.title("📝 RFQ Manager")
st.write("Import RFQs via AI parsing or define them manually.")

# Initialize client
supabase = get_supabase()

if not supabase:
    st.warning("⚠️ Supabase is not configured. Please go to Settings.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["🤖 AI Parser", "✍️ Manual Input", "✏️ Edit Saved"])

# --- TAB 1: AI PARSER ---
with tab1:
    st.write("Paste the raw text of an RFQ email below to extract structured items.")
    rfq_text = st.text_area("RFQ Email Content", height=300, placeholder="Dear Admin, we need the following items...", key="rfq_input_area")

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
            
    if 'parsed_rfq' in st.session_state:
        st.divider()
        st.subheader("Extracted Data")
        
        current_title = st.session_state['parsed_rfq'].get("title", f"RFQ - {pd.Timestamp.now().strftime('%Y-%m-%d')}")
        rfq_title = st.text_input("RFQ Title", value=current_title, key="ai_rfq_title")
        
        df = pd.DataFrame(st.session_state['parsed_rfq']["items"])
        st.dataframe(df, use_container_width=True)
        
        if st.button("Save to History", key="save_ai_rfq"):
            try:
                final_data = st.session_state['parsed_rfq']
                final_data['title'] = rfq_title
                
                supabase.table('rfqs').insert({
                    "raw_text": st.session_state['rfq_text'], 
                    "parsed_json": final_data
                }).execute()
                
                st.success("RFQ saved to history successfully!")
                del st.session_state['parsed_rfq']
                del st.session_state['rfq_text']
                st.rerun()
            except Exception as e:
                st.error(f"Error saving RFQ: {e}")

# --- TAB 2: MANUAL INPUT ---
with tab2:
    st.write("Define your RFQ items manually.")
    manual_title = st.text_input("RFQ Title / Reference", placeholder="Manual RFQ - Jan 20", key="manual_rfq_title")
    
    if "manual_df" not in st.session_state:
        st.session_state.manual_df = pd.DataFrame(columns=[
            "item_code", "description", "quantity", "uom", "name", "brand", "specs"
        ])

    col_man1, col_man2, col_man3, col_man4 = st.columns([1.5, 0.5, 1.5, 0.5])
    
    with col_man1:
        new_col_name = st.text_input("Add New Column", placeholder="e.g. Color", label_visibility="collapsed", key="add_col_input")
    with col_man2:
        if st.button("➕ Add", key="add_col_btn"):
            if new_col_name and new_col_name not in st.session_state.manual_df.columns:
                st.session_state.manual_df[new_col_name] = ""
                st.rerun()
                
    with col_man3:
        if not st.session_state.manual_df.columns.empty:
            col_to_rename = st.selectbox("Select Col to Rename", st.session_state.manual_df.columns, label_visibility="collapsed", key="rename_col_sel")
            rename_val = st.text_input("New Name", placeholder="New Name", label_visibility="collapsed", key="rename_col_input")
    with col_man4:
        if st.button("✏️ Rename", key="rename_col_btn"):
            if col_to_rename and rename_val and rename_val not in st.session_state.manual_df.columns:
                 st.session_state.manual_df = st.session_state.manual_df.rename(columns={col_to_rename: rename_val})
                 st.rerun()
    
    if st.button("🗑️ Clear All Rows", key="clear_rows_btn"):
        st.session_state.manual_df = st.session_state.manual_df.iloc[0:0]
        st.rerun()

    edited_df = st.data_editor(
        st.session_state.manual_df,
        num_rows="dynamic",
        column_config={
            "quantity": st.column_config.NumberColumn("Qty", min_value=0),
        },
        use_container_width=True,
        key="manual_rfq_editor"
    )
    
    if not edited_df.equals(st.session_state.manual_df):
        st.session_state.manual_df = edited_df
    
    if st.button("Save Manual RFQ", type="primary", key="save_manual_btn"):
        if not edited_df.empty:
            try:
                clean_data = edited_df.where(pd.notnull(edited_df), None).to_dict(orient="records")
                parsed_json = {"items": clean_data, "title": manual_title}
                
                supabase.table('rfqs').insert({
                    "raw_text": f"MANUAL ENTRY: {manual_title}", 
                    "parsed_json": parsed_json
                }).execute()
                
                st.success(f"Saved manual RFQ with {len(clean_data)} items!")
                st.session_state.manual_df = st.session_state.manual_df.iloc[0:0]
                st.rerun()
            except Exception as e:
                st.error(f"Error saving manual RFQ: {e}")
        else:
            st.warning("Please add at least one item.")

# --- TAB 3: EDIT SAVED RFQ ---
with tab3:
    st.write("Edit an existing RFQ from your database.")
    
    try:
        all_rfqs = supabase.table('rfqs').select('*').order('created_at', desc=True).limit(100).execute().data
        
        if not all_rfqs:
            st.info("No saved RFQs found.")
        else:
            rfq_to_edit = st.selectbox(
                "Select RFQ to Edit", 
                options=all_rfqs, 
                format_func=lambda x: f"{x['parsed_json'].get('title', 'RFQ')} (#{x['id']} - {x['created_at'][:10]})" if x.get('parsed_json') and 'title' in x['parsed_json'] else f"RFQ #{x['id']} - {x['created_at'][:16]}"
            )
            
            if rfq_to_edit and rfq_to_edit.get('parsed_json') and "items" in rfq_to_edit['parsed_json']:
                current_items = rfq_to_edit['parsed_json']["items"]
                new_title = st.text_input("Edit RFQ Title", value=rfq_to_edit['parsed_json'].get('title', ''), key=f"edit_title_{rfq_to_edit['id']}")
                
                edit_df = pd.DataFrame(current_items)
                edited_saved_df = st.data_editor(
                    edit_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"editor_saved_{rfq_to_edit['id']}"
                )
                
                col_up1, col_up2 = st.columns([1, 4])
                with col_up1:
                    if st.button("💾 Update", type="primary", key=f"upd_btn_{rfq_to_edit['id']}"):
                        try:
                            updated_items = edited_saved_df.where(pd.notnull(edited_saved_df), None).to_dict(orient="records")
                            new_json = rfq_to_edit['parsed_json']
                            new_json["items"] = updated_items
                            new_json["title"] = new_title
                            
                            supabase.table('rfqs').update({"parsed_json": new_json}).eq('id', rfq_to_edit['id']).execute()
                            st.success("RFQ updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating RFQ: {e}")
                with col_up2:
                    if st.button("🗑️ Delete RFQ", key=f"del_btn_{rfq_to_edit['id']}"):
                        try:
                            supabase.table('rfqs').delete().eq('id', rfq_to_edit['id']).execute()
                            st.warning("RFQ deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting RFQ: {e}")
    except Exception as e:
        st.error(f"Error loading RFQs: {e}")

# --- RECENT RFQS ---
st.divider()
st.subheader("📜 Recent RFQs")
try:
    recent_rfqs = supabase.table('rfqs').select('*').order('created_at', desc=True).limit(5).execute().data
    for r in recent_rfqs:
        title = r['parsed_json'].get('title', 'Untitled RFQ') if r.get('parsed_json') else 'Untitled RFQ'
        with st.expander(f"{title} - {r['created_at'][:16]}"):
            st.text(r['raw_text'][:200] + "...")
            if r.get('parsed_json'):
                st.json(r['parsed_json'])
except Exception as e:
    st.error(f"Error loading recent RFQs: {e}")

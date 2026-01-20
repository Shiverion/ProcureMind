import streamlit as st
import pandas as pd
from logic.database import SessionLocal, RFQ, Product, Quote, Supplier
from sqlalchemy import text

st.set_page_config(page_title="Finalization", page_icon="🏁", layout="wide")

st.title("🏁 Finalization & Proposal Generator")
st.write("Select winning bids to generate a final proposal/PO.")

db = SessionLocal()

# 1. SELECT RFQ
rfqs = db.query(RFQ).order_by(RFQ.created_at.desc()).all()

if not rfqs:
    st.warning("No RFQs found.")
    st.stop()

rfq_choice = st.selectbox(
    "Select RFQ to Finalize", 
    options=rfqs, 
    format_func=lambda x: f"{x.parsed_json.get('title', 'RFQ')} (#{x.id} - {x.created_at.strftime('%Y-%m-%d')})" if x.parsed_json and 'title' in x.parsed_json else f"RFQ #{x.id} - {x.created_at.strftime('%Y-%m-%d %H:%M')}"
)

if rfq_choice and rfq_choice.parsed_json and "items" in rfq_choice.parsed_json:
    items = rfq_choice.parsed_json["items"]
    
    st.divider()
    st.subheader("🏆 Select Winning Bids")
    
    final_table_data = []
    grand_total = 0.0
    
    # Iterate through items and let user pick a quote
    for idx, item in enumerate(items):
        with st.container():
            col1, col2 = st.columns([1, 2])
            
            # Item Details
            qty = float(item.get('quantity', 1) or 1)
            desc = f"{item.get('description', '')}"
            name = item.get('name', 'Unknown')
            
            with col1:
                st.markdown(f"**Item {idx+1}: {name}**")
                st.caption(f"Qty: {qty} | {desc[:100]}...")
            
            with col2:
                # Find quotes (Exact Match)
                target_name = item.get('name', '').strip()
                sql = text("""
                    SELECT id FROM products WHERE LOWER(name) = LOWER(:name)
                """)
                matches = db.execute(sql, {"name": target_name}).fetchall()
                p_ids = [r.id for r in matches]
                
                quotes = []
                if p_ids:
                    quotes = db.query(Quote, Supplier)\
                        .join(Supplier, Quote.supplier_id == Supplier.id)\
                        .filter(Quote.product_id.in_(p_ids))\
                        .order_by(Quote.price.asc())\
                        .all()
                
                # Selection Dropdown
                if quotes:
                    # Create a mapping for lookup
                    quote_map = {f"{q.id}": (q, s) for q, s in quotes}
                    
                    # Options are IDs
                    option_ids = ["None"] + list(quote_map.keys())
                    
                    def format_func(opt_id):
                        if opt_id == "None":
                            return "Select a Quote..."
                        q, s = quote_map[opt_id]
                        return f"{s.name} - {q.currency} {q.price:,.0f}"

                    selected_id = st.selectbox(f"Choose Supplier for #{idx+1}", options=option_ids, format_func=format_func, key=f"q_sel_{idx}")
                    
                    if selected_id != "None":
                        selected_quote, selected_supplier = quote_map[selected_id]
                        
                        line_total = float(selected_quote.price) * qty
                        grand_total += line_total
                        
                        final_table_data.append({
                            "Item Code": item.get('item_code', '-'),
                            "Description": desc,
                            "Qty": qty,
                            "UOM": item.get('uom', '-'),
                            "Name": name,
                            "Brand": item.get('brand', '-'),
                            "Specs": item.get('specs', '-'),
                            "Winner": selected_supplier.name,
                            "Single Price": f"{selected_quote.currency} {selected_quote.price:,.0f}",
                            "Total Price": f"{selected_quote.currency} {line_total:,.0f}",
                            "_raw_total": line_total # Hidden for sorting/sum
                        })
                    else:
                        # Append row with blanks if skipped
                         final_table_data.append({
                            "Item Code": item.get('item_code', '-'),
                            "Description": desc,
                            "Qty": qty,
                            "UOM": item.get('uom', '-'),
                            "Name": name,
                            "Brand": item.get('brand', '-'),
                            "Specs": item.get('specs', '-'),
                            "Winner": "PENDING",
                            "Single Price": "-",
                            "Total Price": "-"
                        })
                else:
                    st.warning(f"No matching quotes found for '{name}'.")
                    final_table_data.append({
                            "Item Code": item.get('item_code', '-'),
                            "Description": desc,
                            "Qty": qty,
                            "UOM": item.get('uom', '-'),
                            "Name": name,
                            "Brand": item.get('brand', '-'),
                            "Specs": item.get('specs', '-'),
                            "Winner": "NO QUOTES",
                            "Single Price": "-",
                            "Total Price": "-"
                        })

    st.divider()
    
    # Final Table
    st.subheader("📑 Final Recapitulation")
    df_final = pd.DataFrame(final_table_data)
    
    # Enforce Column Order
    column_order = [
         "Item Code", "Name", "Qty", "UOM", "Specs", 
         "Brand", "Description", "Winner", "Single Price", "Total Price"
    ]
    
    # Ensure all columns exist, fill missing with quotes if needed (though they are built above)
    for col in column_order:
        if col not in df_final.columns:
            df_final[col] = "-"
            
    # Reorder PERMANENTLY so CSV export respects it
    df_final = df_final[column_order]

    # Display
    st.dataframe(
        df_final, 
        use_container_width=True,
        hide_index=True
    )
    
    # Grand Total
    st.markdown(f"### 💰 Grand Total: Rp {grand_total:,.0f}")
    
    st.divider()
    st.subheader("📤 Export & Communicate")
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        # CSV Download
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download as CSV",
            data=csv,
            file_name=f"Final_Quote_{rfq_choice.id}.csv",
            mime='text/csv',
        )
        
    with col_exp2:
        # AI Email Generator
        st.write("✉️ **Email Generator**")
        pre_instruction = st.text_area("Initial Context (Optional)", placeholder="e.g. Offer 5% discount if paid in 7 days", height=100)
        
        if st.button("✨ Draft Email Response", type="primary"):
            from logic.parser import generate_email_response
            
            with st.spinner("Drafting email..."):
                # Convert table to markdown for the LLM
                table_md = df_final.drop(columns=["_raw_total"] if "_raw_total" in df_final.columns else []).to_markdown(index=False)
                
                # Get original text (fallback if manual)
                original_text = rfq_choice.raw_text
                
                email_draft = generate_email_response(original_text, table_md, pre_instruction)
                
                st.session_state['email_draft'] = email_draft

    if 'email_draft' in st.session_state:
        st.success("Draft generated!")
        st.caption("📧 Copy & Paste this into your email client:")
        st.code(st.session_state['email_draft'], language=None)
        
        # Refinement Loop
        st.divider()
        st.write("✍️ **Start AI Refinement**")
        feedback = st.text_input("Enter instructions to refine the email (e.g. 'Make it more formal', 'Add a deadline of Friday')")
        
        if st.button("🔄 Refine Draft"):
            if feedback:
                from logic.parser import refine_email_response
                with st.spinner("Refining email..."):
                    new_draft = refine_email_response(st.session_state['email_draft'], feedback)
                    st.session_state['email_draft'] = new_draft
                    st.rerun()
            else:
                st.warning("Please enter some feedback instructions first.")

else:
    st.info("No items in this RFQ.")

db.close()

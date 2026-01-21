import streamlit as st
import pandas as pd
from logic.database import get_supabase
from logic.parser import generate_embedding

st.set_page_config(page_title="Log Quote", page_icon="📝", layout="wide")

st.title("📝 Log & Manage Quotes")

# Initialize client
supabase = get_supabase()

if not supabase:
    st.warning("⚠️ Supabase is not configured. Please go to Settings.")
    st.stop()

tab1, tab2 = st.tabs(["➕ Search & Log", "✏️ Edit History"])

# --- TAB 1: SEARCH & LOG ---
with tab1:
    # --- SEMANTIC SEARCH ---
    st.header("🔍 Semantic Product Search")
    query = st.text_input("Search for historical products (e.g., 'heavy duty pump')")

    if query:
        with st.spinner("Searching..."):
            embedding = generate_embedding(query)
            
            # Perform vector similarity search using Supabase RPC
            # Note: match_products must be created in Supabase SQL editor
            try:
                rpc_response = supabase.rpc('match_products', {
                    'query_embedding': embedding,
                    'match_threshold': 0.5,
                    'match_count': 5
                }).execute()
                
                results = rpc_response.data
                
                if results:
                    st.write("### Top Matches")
                    for r in results:
                        sim = r.get('similarity', 0)
                        with st.expander(f"{r['name']} (Similarity: {sim:.2%})"):
                            st.write(f"**Description:** {r.get('description', '-')}")
                            st.write(f"**Specs:** {r.get('specs', '-')}")
                            
                            # Find quotes for this product
                            q_res = supabase.table('quotes').select('*, suppliers(name)').eq('product_id', r['id']).execute()
                            quotes = q_res.data
                            
                            if quotes:
                                st.write("#### 💰 Price Comparison")
                                
                                # Prepare data for chart
                                chart_data = pd.DataFrame([
                                    {"Supplier": q['suppliers']['name'], "Price": float(q['price'])} 
                                    for q in quotes
                                ])
                                
                                if not chart_data.empty:
                                    st.bar_chart(chart_data, x="Supplier", y="Price", color="#4CAF50")

                                # Detailed Table
                                st.write("#### 📋 Quote Details")
                                t_data = []
                                for q in quotes:
                                    t_data.append({
                                        "Supplier": q['suppliers']['name'],
                                        "Price": f"{q['currency']} {float(q['price']):,.2f}",
                                        "UOM": q['uom'] if q['uom'] else "-",
                                        "Date": q['quote_date'],
                                        "Link": q['source_url'] if q['source_url'] else None
                                    })
                                
                                st.dataframe(
                                    pd.DataFrame(t_data),
                                    column_config={
                                        "Link": st.column_config.LinkColumn("Source URL", display_text="Open Link")
                                    },
                                    use_container_width=True
                                )
                            else:
                                st.info("No quotes found for this product.")
                else:
                    st.info("No matching products found. Try a different query or adjust the threshold.")
            except Exception as e:
                st.error(f"Search Error: {e}")
                st.info("💡 Tip: Make sure the 'match_products' RPC is created in Supabase (see README).")

    st.divider()

    # --- MANUAL QUOTE ENTRY ---
    st.header("➕ Log a New Quote")
    
    # Fetch lists for selects
    with st.spinner("Loading master data..."):
        all_suppliers = supabase.table('suppliers').select('id, name').order('name').execute().data
        all_products = supabase.table('products').select('id, name').order('name').execute().data

    st.subheader("1. Product Details")
    product_mode = st.radio("Product Source", ["Existing Product", "New Product", "From RFQ History"], horizontal=True)
    
    selected_product_id = None
    new_p_name = None
    new_p_desc = None
    new_p_specs = None
    
    if product_mode == "Existing Product":
        if all_products:
            p_choice = st.selectbox("Select Product", options=[(p['id'], p['name']) for p in all_products], format_func=lambda x: x[1])
            selected_product_id = p_choice[0]
        else:
            st.warning("No existing products found. Please switch to 'New Product'.")
            
    elif product_mode == "From RFQ History":
        rfq_res = supabase.table('rfqs').select('*').order('created_at', desc=True).limit(50).execute()
        rfqs = rfq_res.data
        if rfqs:
            rfq_choice = st.selectbox(
                "Select RFQ", 
                options=rfqs, 
                format_func=lambda x: f"{x['parsed_json'].get('title', 'RFQ')} (#{x['id']} - {x['created_at'][:10]})" if x.get('parsed_json') and 'title' in x['parsed_json'] else f"RFQ #{x['id']} - {x['created_at'][:16]}"
            )
            
            if rfq_choice and rfq_choice.get('parsed_json') and "items" in rfq_choice['parsed_json']:
                items = rfq_choice['parsed_json']["items"]
                item_options = [(i, item) for i, item in enumerate(items)]
                
                selected_item_idx = st.selectbox(
                    "Select Item from RFQ", 
                    options=item_options, 
                    format_func=lambda x: f"{x[1].get('name', 'Unknown')} (Qty: {x[1].get('quantity', '-')})"
                )
                
                if selected_item_idx:
                    item_data = selected_item_idx[1]
                    new_p_name = st.text_input("Product Name", value=item_data.get('name', ''))
                    new_p_desc = st.text_input("Description", value=item_data.get('description', item_data.get('requirements', '')))
                    new_p_specs = st.text_area("Specs", value=item_data.get('specs', ''))
            else:
                st.info("Selected RFQ has no parsed items.")
        else:
            st.warning("No RFQ history found.")
            
    else: # New Product Manual
        new_p_name = st.text_input("New Product Name")
        new_p_desc = st.text_input("Description (e.g. Heavy Duty Pump)")
        new_p_specs = st.text_area("Specs (e.g. 500W, Stainless Steel)")
    
    st.divider()
    st.subheader("2. Supplier Details")
    supplier_mode = st.radio("Supplier Source", ["Existing Supplier", "New Supplier"], horizontal=True)
    
    selected_supplier_id = None
    new_s_name = None
    new_s_contact = None
    
    if supplier_mode == "Existing Supplier":
        if all_suppliers:
            s_choice = st.selectbox("Select Supplier", options=[(s['id'], s['name']) for s in all_suppliers], format_func=lambda x: x[1])
            selected_supplier_id = s_choice[0]
        else:
            st.warning("No existing suppliers found. Please switch to 'New Supplier'.")
    else:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            new_s_name = st.text_input("New Supplier Name")
        with col_s2:
            new_s_contact = st.text_input("Contact Info (Phone/Email)")

    st.divider()
    st.subheader("3. Quote Details")
    
    default_uom = ""
    if 'item_data' in locals() and product_mode == "From RFQ History":
         default_uom = item_data.get('uom', '')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        price = st.number_input("Price", min_value=0.0, step=100.0, format="%f")
    with col2:
        currency = st.selectbox("Currency", ["IDR", "USD", "EUR", "GBP"])
    with col3:
        uom = st.text_input("Unit of Measure", value=default_uom, placeholder="e.g. Psc, Pail, Box")
        
    source_url = st.text_input("Source Link (optional)", placeholder="https://...")
    note = st.text_area("Note (e.g. specs reference, delivery time)")
    
    submit_q = st.button("Log Quote", type="primary")
    
    if submit_q:
        try:
            # 1. Handle Product Creation
            if (product_mode == "New Product" or product_mode == "From RFQ History") and not selected_product_id:
                if new_p_name:
                    with st.spinner("Generating product embedding..."):
                         embedding = generate_embedding(f"{new_p_name} {new_p_desc} {new_p_specs}")
                         p_ins = supabase.table('products').insert({
                             "name": new_p_name, 
                             "description": new_p_desc, 
                             "specs": new_p_specs, 
                             "embedding": embedding
                         }).execute()
                         selected_product_id = p_ins.data[0]['id']
                else:
                    st.error("Please enter a product name.")
                    st.stop()

            # 2. Handle Supplier Creation
            if supplier_mode == "New Supplier" and not selected_supplier_id:
                if new_s_name:
                    s_ins = supabase.table('suppliers').insert({
                        "name": new_s_name, 
                        "contact_info": new_s_contact
                    }).execute()
                    selected_supplier_id = s_ins.data[0]['id']
                else:
                    st.error("Please enter a supplier name.")
                    st.stop()
            
            # 3. Handle Quote Creation
            if selected_supplier_id and selected_product_id:
                supabase.table('quotes').insert({
                    "product_id": selected_product_id, 
                    "supplier_id": selected_supplier_id, 
                    "price": price, 
                    "currency": currency, 
                    "uom": uom,
                    "source_url": source_url,
                    "note": note
                }).execute()
                st.success("Quote logged successfully!")
                st.balloons()
            else:
                st.error("Missing Product or Supplier selection.")
        except Exception as e:
            st.error(f"Error logging quote: {e}")

# --- TAB 2: EDIT HISTORY ---
with tab2:
    st.header("✏️ Edit Quote History")
    
    # Query all quotes joined with Product and Supplier Names
    try:
        q_res = supabase.table('quotes').select('*, products(name), suppliers(name)').order('created_at', desc=True).execute()
        quotes = q_res.data
        
        if quotes:
            # Prepare Dataframe for Editor
            data = []
            for q in quotes:
                data.append({
                    "id": q['id'],
                    "Product": q['products']['name'],
                    "Supplier": q['suppliers']['name'],
                    "Price": float(q['price']),
                    "Currency": q['currency'],
                    "UOM": q['uom'],
                    "Source URL": q['source_url'],
                    "Note": q['note'],
                    "Date": q['quote_date']
                })
                
            df_quotes = pd.DataFrame(data)
            
            # Display Editor
            edited_quotes_df = st.data_editor(
                df_quotes,
                key="history_editor",
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "Product": st.column_config.TextColumn("Product", disabled=True),
                    "Supplier": st.column_config.TextColumn("Supplier", disabled=True),
                    "Price": st.column_config.NumberColumn("Price", min_value=0.0, format="%.2f"),
                    "Source URL": st.column_config.LinkColumn("Source URL")
                },
                hide_index=True,
                use_container_width=True,
                num_rows="fixed"
            )
            
            if st.button("💾 Save Changes", type="primary"):
                # Supabase handles updates per row easily. 
                # For efficiency, we only update if user clicked save.
                # In a real app, we might compare with original to minimize API calls.
                updated_count = 0
                with st.spinner("Saving changes..."):
                    for index, row in edited_quotes_df.iterrows():
                        q_id = row['id']
                        supabase.table('quotes').update({
                            "price": row['Price'],
                            "currency": row['Currency'],
                            "uom": row['UOM'],
                            "source_url": row['Source URL'],
                            "note": row['Note']
                        }).eq('id', q_id).execute()
                        updated_count += 1
                
                st.success(f"Updated {updated_count} quotes successfully!")
                st.rerun()
                
        else:
            st.info("No quotes found in history.")
    except Exception as e:
        st.error(f"Error loading history: {e}")

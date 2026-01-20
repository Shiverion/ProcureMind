import streamlit as st
import pandas as pd
from logic.database import SessionLocal, Product, Supplier, Quote, RFQ
from logic.parser import generate_embedding
from sqlalchemy import text

st.set_page_config(page_title="Log Quote", page_icon="📝", layout="wide")

st.title("📝 Log & Manage Quotes")

tab1, tab2 = st.tabs(["➕ Search & Log", "✏️ Edit History"])

# --- TAB 1: SEARCH & LOG ---
with tab1:
    # --- SEMANTIC SEARCH ---
    st.header("🔍 Semantic Product Search")
    query = st.text_input("Search for historical products (e.g., 'heavy duty pump')")

    if query:
        with st.spinner("Searching..."):
            embedding = generate_embedding(query)
            db = SessionLocal()
            
            # Perform vector similarity search using pgvector
            sql = text("""
                SELECT id, name, description, specs, (embedding <=> :embedding) as distance
                FROM products
                WHERE embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT 5
            """)
            results = db.execute(sql, {"embedding": str(embedding)}).fetchall()
            
            if results:
                st.write("### Top Matches")
                for r in results:
                    dist = r.distance if r.distance is not None else 1.0
                    with st.expander(f"{r.name} (Similarity: {1 - dist:.2%})"):
                        st.write(f"**Description:** {r.description}")
                        st.write(f"**Specs:** {r.specs}")
                        
                        # Find quotes for this product
                        quotes = db.query(Quote, Supplier).join(Supplier, Quote.supplier_id == Supplier.id).filter(Quote.product_id == r.id).all()
                        if quotes:
                            st.write("#### 💰 Price Comparison")
                            
                            # Prepare data for chart
                            chart_data = pd.DataFrame([
                                {"Supplier": s.name, "Price": float(q.price)} 
                                for q, s in quotes
                            ])
                            
                            if not chart_data.empty:
                                st.bar_chart(chart_data, x="Supplier", y="Price", color="#4CAF50")

                            # Detailed Table
                            st.write("#### 📋 Quote Details")
                            t_data = []
                            for q, s in quotes:
                                t_data.append({
                                    "Supplier": s.name,
                                    "Price": f"{q.currency} {q.price:,.2f}",
                                    "UOM": q.uom if q.uom else "-",
                                    "Date": q.quote_date,
                                    "Link": q.source_url if q.source_url else None
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
                st.info("No matching products found.")
            db.close()

    st.divider()

    # --- MANUAL QUOTE ENTRY ---
    st.header("➕ Log a New Quote")
    db = SessionLocal()
    all_suppliers = db.query(Supplier).all()
    all_products = db.query(Product).all()

    if True: # Always show form
        st.subheader("1. Product Details")
        product_mode = st.radio("Product Source", ["Existing Product", "New Product", "From RFQ History"], horizontal=True)
        
        selected_product_id = None
        new_p_name = None
        new_p_desc = None
        new_p_specs = None
        
        db = SessionLocal() # Keep session open for cascading selects
        
        if product_mode == "Existing Product":
            if all_products:
                p_choice = st.selectbox("Select Product", options=[(p.id, p.name) for p in all_products], format_func=lambda x: x[1])
            else:
                st.warning("No existing products found. Please switch to 'New Product'.")
                
        elif product_mode == "From RFQ History":
            rfqs = db.query(RFQ).order_by(RFQ.created_at.desc()).all()
            if rfqs:
                rfq_choice = st.selectbox(
                    "Select RFQ", 
                    options=rfqs, 
                    format_func=lambda x: f"{x.parsed_json.get('title', 'RFQ')} (#{x.id} - {x.created_at.strftime('%Y-%m-%d')})" if x.parsed_json and 'title' in x.parsed_json else f"RFQ #{x.id} - {x.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
                
                if rfq_choice and rfq_choice.parsed_json and "items" in rfq_choice.parsed_json:
                    items = rfq_choice.parsed_json["items"]
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
                s_choice = st.selectbox("Select Supplier", options=[(s.id, s.name) for s in all_suppliers], format_func=lambda x: x[1])
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
        
        default_price = 0.0
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
            if product_mode == "New Product" or product_mode == "From RFQ History":
                if new_p_name:
                    with st.spinner("Generating product embedding..."):
                         embedding = generate_embedding(f"{new_p_name} {new_p_desc} {new_p_specs}")
                         product = Product(name=new_p_name, description=new_p_desc, specs=new_p_specs, embedding=embedding)
                         db.add(product)
                         db.commit()
                         db.refresh(product)
                         selected_product_id = product.id
                else:
                    st.error("Please enter a product name.")
                    db.close()
                    st.stop()
            elif product_mode == "Existing Product" and 'p_choice' in locals():
                selected_product_id = p_choice[0]

            if supplier_mode == "New Supplier":
                if new_s_name:
                    supplier = Supplier(name=new_s_name, contact_info=new_s_contact)
                    db.add(supplier)
                    db.commit()
                    db.refresh(supplier)
                    selected_supplier_id = supplier.id
                else:
                    st.error("Please enter a supplier name.")
                    db.close()
                    st.stop()
            elif supplier_mode == "Existing Supplier" and 's_choice' in locals():
                selected_supplier_id = s_choice[0]
            
            if selected_supplier_id and selected_product_id:
                new_q = Quote(
                    product_id=selected_product_id, 
                    supplier_id=selected_supplier_id, 
                    price=price, 
                    currency=currency, 
                    uom=uom,
                    source_url=source_url,
                    note=note
                )
                db.add(new_q)
                db.commit()
                st.success(f"Quote logged successfully! Product: {new_p_name if new_p_name else 'Existing'}")
                
        db.close()

# --- TAB 2: EDIT HISTORY ---
with tab2:
    st.header("✏️ Edit Quote History")
    
    db = SessionLocal()
    
    # Query all quotes joined with Product and Supplier Names
    quotes = db.query(Quote, Product.name.label("product_name"), Supplier.name.label("supplier_name"))\
        .join(Product, Quote.product_id == Product.id)\
        .join(Supplier, Quote.supplier_id == Supplier.id)\
        .order_by(Quote.created_at.desc())\
        .all()
    
    if quotes:
        # Prepare Dataframe for Editor
        data = []
        for q, p_name, s_name in quotes:
            data.append({
                "id": q.id,
                "Product": p_name,
                "Supplier": s_name,
                "Price": float(q.price),
                "Currency": q.currency,
                "UOM": q.uom,
                "Source URL": q.source_url,
                "Note": q.note,
                "Date": q.quote_date
            })
            
        df_quotes = pd.DataFrame(data)
        
        # Display Editor
        edited_quotes_df = st.data_editor(
            df_quotes,
            key="history_editor",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True), # Prevent ID edit
                "Product": st.column_config.TextColumn("Product", disabled=True), # Prevent Foreign Key Break
                "Supplier": st.column_config.TextColumn("Supplier", disabled=True),
                "Price": st.column_config.NumberColumn("Price", min_value=0.0, format="%.2f"),
                "Source URL": st.column_config.LinkColumn("Source URL")
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed" # Deleting logic requires more complex SQL handling, keeping it simple for now
        )
        
        if st.button("💾 Save Changes", type="primary"):
            # Identify changes
            updated_count = 0
            
            for index, row in edited_quotes_df.iterrows():
                q_id = int(row['id'])
                # Find original quote
                q_obj = db.query(Quote).filter(Quote.id == q_id).first()
                if q_obj:
                    # Update fields
                    q_obj.price = row['Price']
                    q_obj.currency = row['Currency']
                    q_obj.uom = row['UOM']
                    q_obj.source_url = row['Source URL']
                    q_obj.note = row['Note']
                    updated_count += 1
            
            db.commit()
            st.success(f"Updated {updated_count} quotes successfully!")
            st.rerun()
            
    else:
        st.info("No quotes found in history.")
        
    db.close()

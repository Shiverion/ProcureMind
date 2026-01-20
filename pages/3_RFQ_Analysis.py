import streamlit as st
import pandas as pd
import altair as alt
from logic.database import SessionLocal, RFQ, Product, Quote, Supplier
from logic.parser import generate_embedding
from sqlalchemy import text

st.set_page_config(page_title="RFQ Analysis", page_icon="📈", layout="wide")

st.title("📈 RFQ Analysis & Bid Tabulation")
st.write("Compare quotes for items in your RFQ history.")

db = SessionLocal()

# 1. SELECT RFQ
st.sidebar.header("1. Select RFQ")
rfqs = db.query(RFQ).order_by(RFQ.created_at.desc()).all()

if not rfqs:
    st.warning("No RFQs found. Please import one in the RFQ Manager.")
    st.stop()

rfq_choice = st.sidebar.selectbox(
    "Choose RFQ", 
    options=rfqs, 
    format_func=lambda x: f"{x.parsed_json.get('title', 'RFQ')} (#{x.id} - {x.created_at.strftime('%Y-%m-%d')})" if x.parsed_json and 'title' in x.parsed_json else f"RFQ #{x.id} - {x.created_at.strftime('%Y-%m-%d %H:%M')}"
)

# 2. SELECT ITEM
if rfq_choice and rfq_choice.parsed_json and "items" in rfq_choice.parsed_json:
    items = rfq_choice.parsed_json["items"]
    
    # Display RFQ Summary
    # Display RFQ Summary with Filters
    st.subheader(f"📋 {rfq_choice.parsed_json.get('title', 'RFQ Summary')}")
    
    # --- Sidebar Filtering ---
    st.sidebar.divider()
    st.sidebar.header("2. Filter Items")
    
    df_items = pd.DataFrame(items)
    
    filter_col = st.sidebar.selectbox("Filter Column", options=["None", "description", "name", "item_code", "brand"], index=0)
    
    if filter_col != "None":
        # Get unique values for dropdown
        unique_values = ["All"] + sorted(df_items[filter_col].astype(str).unique().tolist())
        
        filter_val = st.sidebar.selectbox(f"Select {filter_col}", options=unique_values)
        
        if filter_val and filter_val != "All":
            df_items = df_items[df_items[filter_col].astype(str) == filter_val]
    
    st.sidebar.info(f"Showing {len(df_items)} items.")

    # --- Interactive Table ---
    st.caption("👈 **Select a row** in the table below to analyze prices.")
    
    selection = st.dataframe(
        df_items, 
        use_container_width=True, 
        on_select="rerun", 
        selection_mode="single-row"
    )
    
    selected_row_index = selection.selection["rows"]
    
    # Auto-select first row if nothing selected, so user sees analysis immediately
    if not selected_row_index and not df_items.empty:
        selected_row_index = [0]
        st.caption("ℹ️ *Auto-analyzing first item. Click another row to switch.*")
    
    if selected_row_index:
        # Get the actual data from the filtered dataframe using the selected index
        item_data = df_items.iloc[selected_row_index[0]].to_dict()
        st.divider()
        st.header(f"🔍 Analysis: {item_data.get('name', 'Unknown')}")
        st.caption(f"Specs: {item_data.get('description', '')} {item_data.get('specs', '')}")
        
        # 3. EXACT MATCH FOR COMPATIBLE PRODUCTS
        with st.spinner("Finding exact product matches..."):
            # Use exact name matching (Case Insensitive)
            target_name = item_data.get('name', '').strip()
            
            sql = text("""
                SELECT id, name, description 
                FROM products
                WHERE LOWER(name) = LOWER(:name)
            """)
            results = db.execute(sql, {"name": target_name}).fetchall()
            
            if results:
                # Get IDs of found products
                p_ids = [r.id for r in results]
                
                # Fetch quotes for these products
                quotes = db.query(Quote, Supplier, Product)\
                    .join(Supplier, Quote.supplier_id == Supplier.id)\
                    .join(Product, Quote.product_id == Product.id)\
                    .filter(Quote.product_id.in_(p_ids))\
                    .all()
                
                if quotes:
                    # Prepare comparison matrix data
                    comp_data = {}
                    list_data = []
                    rfq_qty = float(item_data.get('quantity', 1) or 1)
                    
                    # Sort quotes by price ascending (Cheapest First)
                    sorted_quotes = sorted(quotes, key=lambda x: x[0].price)
                    
                    for q, s, p in sorted_quotes:
                        price = float(q.price)
                        total = price * rfq_qty
                        
                        # Data for Matrix (Pivot)
                        col_name = f"{s.name}"
                        comp_data[col_name] = {
                            "Product Match": p.name,
                            "Unit Price": f"{q.currency} {price:,.0f}",
                            "Total Cost": f"{q.currency} {total:,.0f}",
                            "Calculation": f"({q.currency} {price:,.0f} x {rfq_qty:,.0f})",
                            "Description": p.description[:50] + "...",
                            "Date": q.quote_date.strftime('%Y-%m-%d')
                        }
                        
                        # Data for List/Chart
                        list_data.append({
                            "Supplier": s.name,
                            "Product": p.name,
                            "Price": price,
                            "Total Est. Cost": total,
                            "Calculation": f"{q.currency} {price:,.0f} x {rfq_qty:,.0f}",
                            "Currency": q.currency,
                            "UOM": q.uom,
                            "Link": q.source_url,
                            "Date": q.quote_date
                        })
                    
                    # 4. VISUALIZATION
                    st.subheader("💰 Supplier Price Comparison")
                    chart = alt.Chart(pd.DataFrame(list_data)).mark_bar().encode(
                        x=alt.X('Supplier', sort=None, axis=alt.Axis(labelAngle=0, title="Supplier")),
                        y=alt.Y('Price', title='Unit Price'),
                        color=alt.Color('Supplier', legend=None),
                        tooltip=['Supplier', 'Price', 'Total Est. Cost', 'Product']
                    ).interactive()
                    st.altair_chart(chart, use_container_width=True)
                    
                    # 5. INSIGHTS
                    st.info(f"💡 **Insight Report for {item_data.get('name')} (Qty: {rfq_qty:,.0f})**")
                    best = list_data[0]
                    st.markdown(f"""
                    **Best Offer:** {best['Supplier']} - {best['Currency']} {best['Price']:,.0f} / unit
                    **Total Estimasi Modal (Kasar):** {best['Calculation']} = **{best['Currency']} {best['Total Est. Cost']:,.0f}**
                    """)
                    
                    # 6. COMPARISON MATRIX (Side-by-Side)
                    st.subheader("📊 Side-by-Side Comparison")
                    df_pivot = pd.DataFrame(comp_data)
                    row_order = ["Unit Price", "Total Cost", "Product Match", "Description", "Date"]
                    df_pivot = df_pivot.reindex(row_order)
                    st.table(df_pivot)

                    # 7. DETAILED SOURCE LINKS
                    st.subheader("🔗 Source Links & Details")
                    st.dataframe(
                        pd.DataFrame(list_data)[["Supplier", "Price", "Total Est. Cost", "Link", "UOM"]],
                        column_config={
                            "Link": st.column_config.LinkColumn("Source URL", display_text="Open Link"),
                            "Price": st.column_config.NumberColumn(format="%.0f"),
                            "Total Est. Cost": st.column_config.NumberColumn(format="%.0f")
                        },
                        use_container_width=True
                    )
                    
                else:
                    st.warning("No quotes found for matching products.")
            else:
                st.warning("No similar products found in catalog.")

else:
    st.info("This RFQ has no parsed items.")

db.close()

from logic.database import SessionLocal, Quote, Supplier, Product
import datetime

db = SessionLocal()

# Check if columns exist by trying to insert
try:
    # Ensure dependencies exist
    s = db.query(Supplier).first()
    if not s:
        s = Supplier(name="Test Supplier")
        db.add(s)
        db.commit()
    
    p = db.query(Product).first()
    if not p:
        p = Product(name="Test Product")
        db.add(p)
        db.commit()

    # Insert Quote with new fields
    q = Quote(
        product_id=p.id,
        supplier_id=s.id,
        price=100.00,
        currency="USD",
        uom="Box",  # New Field
        source_url="http://test.com/product", # New Field
        note="Test Note"
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    
    print(f"✅ Success! Created Quote ID {q.id} with UOM: '{q.uom}' and Link: '{q.source_url}'")
    
    # Cleanup test quote
    db.delete(q)
    db.commit()
    print("✅ Cleanup complete.")

except Exception as e:
    print(f"❌ Failed: {e}")
finally:
    db.close()

-- Enable the pgvector extension to work with embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Suppliers Table
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    contact_info TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    specs TEXT,
    embedding vector(768), -- Gemini 2.0 Flash embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Quotes Table
CREATE TABLE IF NOT EXISTS quotes (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    supplier_id INTEGER REFERENCES suppliers(id),
    price DECIMAL(12, 2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    uom TEXT, -- Unit of Measure (e.g., Pail, Pcs, Box)
    source_url TEXT, -- Link to the supplier/product page
    note TEXT,
    quote_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- RFQs Table (to store history of processed emails)
CREATE TABLE IF NOT EXISTS rfqs (
    id SERIAL PRIMARY KEY,
    raw_text TEXT NOT NULL,
    parsed_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

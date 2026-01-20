# ProcureMind 🧠📦

**ProcureMind** is an AI-powered procurement assistant designed to streamline the Request for Quote (RFQ) process. It parses raw emails, manages quote history, analyzes pricing, and drafts professional responses using Google Gemini AI.

This application is designed as a **Wrapper**, meaning users can bring their own API keys and data connections.

## ✨ Features

*   **📝 RFQ Manager**:
    *   **AI Parser**: Paste raw RFQ emails and let Gemini extract structured items (Code, Qty, UOM, Specs).
    *   **Manual Entry**: Create or edit RFQs via a dynamic spreadsheet interface.
    *   **History**: Edit and update saved RFQs from the database.
*   **➕ Log & Manage Quotes**:
    *   **Semantic Search**: Find historical products similar to your needs using AI vector search.
    *   **Quote Logging**: Record new quotes from suppliers.
    *   **History Editor**: Update past quote details directly.
*   **📊 RFQ Analysis**:
    *   **Exact Match Analysis**: Automatically match RFQ items to your product database by name.
    *   **Price Comparison**: View charts and tables comparing supplier offering.
*   **🏁 Finalization**:
    *   **Winner Selection**: Choose winning bids for each item.
    *   **PO Generation**: Export final recapitulation to CSV.
    *   **AI Email Drafter**: Generate professional reply emails with "Commercial Offer", "Scope", and "Remarks" sections.

## 🚀 Quick Start (Local)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Shiverion/procuremind.git
    cd procuremind
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**:
    ```bash
    streamlit run streamlit_app.py
    ```

4.  **Configure API Key**:
    *   Open the app in your browser (usually `http://localhost:8501`).
    *   Go to the **⚙️ Settings** page.
    *   Enter your **Google Gemini API Key** (starts with `AIza...`).

## ☁️ Deployment (Streamlit Cloud)

ProcureMind is ready for 1-click deployment on Streamlit Community Cloud.

1.  **Push to GitHub**.
2.  **Deploy on Streamlit Cloud** and connect your repository.
3.  **Database Configuration**:
    *   By default, it will use a local SQLite file for testing.
    *   For production, add your PostgreSQL credentials to the **Streamlit Secrets**:
    > **Note**: Your Postgres database MUST have the `pgvector` extension enabled.
    >
    > **How to set up a free Cloud DB (Supabase):**
    > 1.  Go to [Supabase](https://supabase.com) and create a new project.
    > 2.  Go to **SQL Editor** and run: `CREATE EXTENSION IF NOT EXISTS vector;`
    > 3.  Go to **Project Settings -> Database -> Connection String (URI)**.
    > 4.  Copy the connection string (it looks like `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`).
    > 5.  Add this to your Streamlit Secrets.

    > 5.  Add this to your Streamlit Secrets.

4.  **Shared API Key (Sponsor Mode)**:
    *   If you want to allow others to use the app **without** entering their own key (using your quota), add your key to secrets:
    ```toml
    GOOGLE_API_KEY = "AIzaSy..."
    ```
    *   If this is set, the "Settings" page becomes optional for users.

## 🛠️ Tech Stack

*   **Frontend**: Streamlit
*   **Backend**: Python, SQLAlchemy
*   **Database**: PostgreSQL (pgvector) or SQLite
*   **AI**: Google Gemini 2.0 Flash (via `google-generativeai`)

## 📄 License

MIT

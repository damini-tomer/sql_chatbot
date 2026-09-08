# 💬 Database AI Chatbot (Text-to-SQL Analytics Assistant)

An interactive, production-grade **Streamlit web application** that enables non-technical users to converse with a MySQL database in plain, natural language. The system dynamically interprets user intents, writes optimized SQL queries, executes them securely, and synthesizes raw data grids into human-friendly analytical responses using advanced Large Language Models (LLMs) via **Groq**.

---

## 🚀 Key Features

* **Natural Language to SQL**: Automatically maps conversational phrases into precise, executable SQL syntax.
* **Intelligent Intent Routing**: Dynamically detects structural/meta inquiries (e.g., *"Tell me about the database"*), bypassing query execution to explain table architectures directly.
* **Polished Chat UX/UI**: Implements modern Streamlit chat interfaces (`st.chat_message`) mimicking a ChatGPT-like conversational flow.
* **Collapsible Technical Deep-Dives**: Utilizes hidden expander widgets to house generated SQL scripts and raw JSON payloads, keeping the main interface clean while remaining transparent for developers.
* **Production-Grade Security**: Strictly wraps database passwords and API tokens using the `st.secrets` standard, completely eliminating hardcoded security exposures.

---

## 🧠 System Architecture Flow

When a user submits a prompt, the system routes the data through the following pipeline:
1. **Context Aggregation**: LangChain inspects the active MySQL database and extracts live table structures and data-type mappings.
2. **SQL Generation (LCEL Chain)**: The user question + active schema are compiled into a strict prompt layout and dispatched to the Groq inference engine using the `openai/gpt-oss-120b` model.
3. **Execution Safety Layer**: The pipeline strips away markdown blocks, extracts raw SQL text strings, and submits queries via an isolated SQLAlchemy/PyMySQL driver block.
4. **Natural Language Synthesis**: The final response block receives the original question, the generated SQL code, and the raw database records to output a unified textual overview.

---

## 🛠️ Tech Stack & Dependencies

* **Frontend Framework**: [Streamlit](https://streamlit.io) (State management, Layout control, Chat components)
* **AI Engine**: [LangChain](https://langchain.com) (LangChain Expression Language, Chains, Prompts, Parser wrappers)
* **LLM Engine**: [Groq Cloud Inference](https://groq.com) running the `openai/gpt-oss-120b` model.
* **Database Management**: MySQL Server driven via `PyMySQL` and `SQLAlchemy`.

---

## 🗄️ Database Schema Reference & Sample Questions

To make testing immediate and frictionless for external reviewers, the chatbot operates over the following sample environment blueprint. 

*(Note: Update the structural descriptions below to match your live database layout if modifications are made).*

### 📋 Sample Database Layout

#### 1. `users` Table

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `id` | INT (PK) | Unique identification tracking number for the user |
| `name` | VARCHAR | Full legal name of the registered user |
| `email` | VARCHAR | User's primary communication email address |
| `balance` | DECIMAL | Total remaining monetary account capital balances |
| `created_at` | DATETIME | Timestamp tracking initial account registrations |

#### 2. `transactions` Table

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `transaction_id` | INT (PK) | Unique identification system tracking number for the transaction |
| `user_id` | INT (FK) | Relational reference linking back to `id` in the users table |
| `amount` | DECIMAL | Total value of the financial transaction ledger entry |
| `status` | VARCHAR | Current transaction state processing phase (`Success`, `Pending`, `Failed`) |

---

## 💡 Example Prompts to Try in the App

Copy and paste these sample requests straight into the user chat interface to review the dual-path execution logic:

### 🌟 Metadata Analysis (Bypasses SQL execution)
* *"Tell me about the database in detail"*
* *"What tables are currently available in this database?"*

### 📊 Data Retrieval Operations (Generates & executes SQL)
* *"Who are the top 3 users with the highest balance?"*
* *"Show me all users who signed up recently."*
* *"What is the total amount of successful transactions?"*
* *"Are there any pending transactions in the database?"*

---

## 📁 Repository Directory Structure

```text
sql_chatbot/
├── .streamlit/
│   └── secrets.toml     # LOCAL ONLY: Hidden credentials (API Keys & DB Passwords)
├── .gitignore           # Safeguards secrets.toml & venv/ from being pushed online
├── app.py               # Main application pipeline logic
├── requirements.txt     # Complete environment snapshots & package variations
└── README.md            # Comprehensive project documentation
```

---

## ⚙️ Local Installation & Setup

### 1. Clone & Access Repository
```bash
git clone https://github.com
cd sql_chatbot
```

### 2. Configure Virtual Environment & Setup Dependencies
```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Install package architecture
pip install -r requirements.txt
```

### 3. Setup Hidden Configuration Variables
Create a `.streamlit` folder at your root project directory layout, add a file named `secrets.toml` inside it, and insert your active system credentials:
```toml
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
DB_PASSWORD = "YOUR_MYSQL_ROOT_PASSWORD"
```

### 4. Fire Up the Streamlit Web Application
```bash
streamlit run app.py
```
The client browser application module will instantly boot open automatically on your local host framework environment at `http://localhost:8501`.


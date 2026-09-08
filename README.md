# Database AI Chatbot (Text-to-SQL Analytics Assistant) 🚀

An interactive, production-grade Streamlit web application that enables non-technical users to converse with a MySQL sales database in plain, natural language. The system dynamically interprets user intents, writes optimized SQL queries, executes them securely, and synthesizes raw data grids into human-friendly analytical responses using advanced Large Language Models (LLMs) via Groq.

## 🚀 Key Features
* **Natural Language to SQL:** Automatically maps conversational commercial phrases into precise, executable MySQL syntax.
* **Intelligent Intent Routing:** Dynamically detects structural/meta inquiries (e.g., "Tell me about the database layout"), bypassing query execution to explain table architectures directly.
* **Polished Chat UX/UI:** Implements a modern, clean Streamlit chat interface (`st.chat_message`) mimicking an enterprise ChatGPT-like conversational flow.
* **Collapsible Technical Deep-Dives:** Utilizes hidden expander widgets to house generated SQL scripts and raw JSON payloads, keeping the main interface pristine for business analysts while remaining fully transparent for developers.
* **Production-Grade Security:** Strictly wraps database passwords and API tokens using the `st.secrets` standard, completely eliminating hardcoded security exposures.

---

## 🧠 System Architecture Flow
When a user submits a prompt, the system routes the data through the following pipeline:
1. **Context Aggregation:** LangChain inspects the active MySQL database and extracts live table structures and data-type mappings.
2. **SQL Generation (LCEL Chain):** The user question + active 6-table schema blueprint are compiled into a strict prompt layout and dispatched to the Groq inference engine.
3. **Execution Safety Layer:** The pipeline strips away markdown blocks, extracts raw SQL text strings, and submits queries via an isolated SQLAlchemy/PyMySQL driver block.
4. **Natural Language Synthesis:** The final response block receives the original question, the generated SQL code, and the raw database records to output a unified textual executive summary.

---

## 🛠️ Tech Stack & Dependencies
* **Frontend Framework:** Streamlit (State management, Layout control, Chat components)
* **AI Engine:** LangChain (LangChain Expression Language, Chains, Prompts, Parser wrappers)
* **LLM Engine:** Groq Cloud Inference running optimized inference models.
* **Database Management:** MySQL Server driven via PyMySQL and SQLAlchemy.

---

## 🗄️ Database Schema Reference
The chatbot operates over a unified database architecture derived from **6 primary relational data spaces**:

### 📋 6-Table Relational Blueprint

#### 1. `customers` Table
* `Customer Index` (INT, PK): Unique identification index for the customer.
* `Customer Names` (VARCHAR): Full name/corporate name of the registered customer.

#### 2. `products` Table
* `Index` (INT, PK): Unique product description index.
* `Product Name` (VARCHAR): Descriptive catalog name of the product item (e.g., Product 1, Product 2).

#### 3. `budgets` Table
* `Product Name` (VARCHAR, FK): Joins with `products`.`Product Name`.
* `2017 Budgets` (DECIMAL): Financial budget target allocation value for the year 2017.

#### 4. `region` Table
* `id` (INT, PK): Region tracking identification number (maps to `sales`.`Delivery Region Index`).
* `name` (VARCHAR): Target city name (e.g., Auburn).
* `county` (VARCHAR): Local county area designation.
* `state_code` (VARCHAR): Two-letter state code layout (e.g., AL, AR).
* `state` (VARCHAR): Full US state name (e.g., Alabama, Arkansas).
* `Region` (VARCHAR): Geographic territory macro territory classification group (e.g., South, Midwest, West, Northeast).
* `type` / `latitude` / `longitude` / `area_code` / `population` / `households` / `median_income` / `land_area` / `water_area` / `time_zone`: Advanced regional demographic and geospatial metrics.

#### 5. `sales` Table
* `OrderNumber` (VARCHAR, PK): Unique alpha-numeric transaction tracking number (e.g., SO - 000225).
* `OrderDate` (DATE): Execution timestamp date of the commercial order.
* `Customer Name Index` (INT, FK): Links back to `customers`.`Customer Index`.
* `Channel` (VARCHAR): Sales pipeline acquisition channel (e.g., Wholesale, Distributor, Retail).
* `Currency Code` (VARCHAR): Transaction currency processing classification (e.g., USD).
* `Warehouse Code` (VARCHAR): Unique logistics node facility signature.
* `Delivery Region Index` (INT, FK): Links back to `region`.`id`.
* `Product Description Index` (INT, FK): Links back to `products`.`Index`.
* `Order Quantity` (INT): Total units purchased inside ledger operation entry.
* `Unit Price` (DECIMAL): Per-unit transaction trading pricing metric.
* `Line Total` (DECIMAL): Calculated cumulative financial transaction value line record (Sales revenue generated).
* `Total Unit Cost` (DECIMAL): Total financial asset allocation overhead cost marker.

---

## 💡 Example Prompts to Try in the App

### 🌟 Metadata Analysis (Bypasses SQL execution)
* "Tell me about the database in detail."
* "What tables and connections are currently available?"

### 📊 Data Retrieval & Aggregations (Generates & executes SQL)
* "Show total Line Total revenue broken down by macro Region."
* "Which product exceeded its 2017 budget target by the highest margin?"
* "What is the total sales revenue generated from Wholesale channels in Alabama?"
* "Who are the top 5 customers based on total units ordered?"

---

## 📁 Repository Directory Structure
```text
sql_chatbot/
├── .streamlit/
│   └── secrets.toml     # LOCAL ONLY: Hidden credentials (API Keys & DB Passwords)
├── .gitignore           # Safeguards secrets.toml & venv/ from version control
├── app.py               # Main application conversational chat pipeline logic
├── upload_data.py       # Data migration engine to ingest the 6 CSV files into MySQL
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
# Activate on Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Setup Hidden Configuration Variables
Create a `.streamlit` folder at your root project directory layout, add a file named `secrets.toml` inside it, and insert your active systems parameters:
```toml
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "YOUR_MYSQL_ROOT_PASSWORD"
DB_NAME = "your_database_name"
```

### 4. Populate the MySQL Database
Place your 6 source CSV data sheets (`customers.csv`, `products.csv`, `budgets.csv`, `region.csv`, `sales.csv`) into the root directory of the project and execute the data onboarding engine:
```bash
streamlit run upload_data.py
```
Click through the interface window to cleanly construct your MySQL architecture tables and transfer the contents automatically.

### 5. Fire Up the Chatbot Application
```bash
streamlit run app.py
```
The application module will instantly boot open automatically on your local host framework environment at **`http://localhost:8501`**.



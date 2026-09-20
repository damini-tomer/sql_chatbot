import os
import re
import time
import pandas as pd
import streamlit as st
from sqlalchemy import text
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
os.environ["GROQ_API_KEY"] = st.secrets.get("GROQ_API_KEY", "YOUR_API_KEY_HERE")
DB_PASSWORD = st.secrets.get("DB_PASSWORD", "YOUR_DB_PASSWORD")

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Enterprise Database Assistant", page_icon="📊", layout="wide")
st.title("📊 Enterprise Database AI Assistant")
st.caption("Production Build v5.1: Telemetry, Visualization, & Persistent Memory")

# --- High-Level Database Directory Map ---
DATABASE_DIRECTORY = """
Available Tables and Structural Descriptions:
1. customers Table: Stores corporate/individual client profiles. Key columns: [Customer Index, Customer Names].
2. products Table: Inventory item registry. Key columns: [Index, Product Name].
3. 2017_budgets Table: 2017 financial target limits mapped to specific products. Key columns: [Product Name, 2017 Budgets].
4. regions Table: Extensive regional demographics and locations. Key columns: [id, name, county, state_code, state, type, latitude, longitude, area_code, population, households, median_income, land_area, water_area, time_zone].
5. sales_order Table: The main transaction ledger. Key columns: [OrderNumber, OrderDate, Customer Name Index, Channel, Currency Code, Warehouse Code, Delivery Region Index, Product Description Index, Order Quantity, Unit Price, Line Total, Total Unit Cost].
6. state_regions Table: contains info about state and region. Key columns: [State Code, State, Region].
"""

# --- Database Connection Initialization ---
@st.cache_resource
def init_database():
    host = 'localhost'
    port = '3306'
    username = 'root'
    database_schema = 'text_to_sql1'
    mysql_uri = f"mysql+pymysql://{username}:{DB_PASSWORD}@{host}:{port}/{database_schema}"
    return SQLDatabase.from_uri(mysql_uri, sample_rows_in_table_info=2)

try:
    db = init_database()
    ALL_TABLES = db.get_usable_table_names()
    st.sidebar.success("✅ Database Connected")
    st.sidebar.write("Verified Tables:", ALL_TABLES)
except Exception as e:
    st.error(f"Critical Database Connection Failure: {e}")
    st.stop()

# --- Multi-Agent Architecture Engine ---
@st.cache_resource
def init_agents():
    # Use Llama 3.1 70B for heavy lifting, 8B for fast JSON routing

    LIGHT_MODEL = "openai/gpt-oss-20b"   # Standard Groq model format (Update if using custom)
    HEAVY_MODEL = "openai/gpt-oss-120b"  # Standard Groq model format (Update if using custom)
        
    llm_light = ChatGroq(model=LIGHT_MODEL, temperature=0)
    llm_heavy = ChatGroq(model=HEAVY_MODEL, temperature=0)
    
    # AGENT 1: The Guard Dog
    router_template = """You are a strict security classification agent.
    1. If the input asks for data, metrics, or database structure, set "is_db_query" to true.
    2. If it's a basic greeting, set "is_db_query" to false and "casual_response" to: "Hello! I am your database assistant. How can I help you analyze your data?"
    3. For all other chitchat, set "is_db_query" to false and "casual_response" to: "I am a specialized database assistant. I can only answer questions related to your database."
    Respond ONLY with JSON: {{ "is_db_query": true/false, "casual_response": "..." }}
    User: {question}
    JSON:"""
    router_chain = ChatPromptTemplate.from_template(router_template) | llm_light | JsonOutputParser()

    # AGENT 2: Table Extractor
    extractor_template = """Output which explicit tables are needed to satisfy this question. 
    CRITICAL RULES:
    - If the user asks about "orders", "transactions", or "sales", use the "sales_order" table.
    - If the user asks about "budget", use "2017_budgets".
    Directory: {db_directory}
    User Question: {question}
    Respond ONLY with JSON: {{ "relevant_tables": ["table1", "table2"] }}"""
    extractor_chain = ChatPromptTemplate.from_template(extractor_template) | llm_light | JsonOutputParser()

    # AGENT 3: SQL Engineer
    sql_template = """You are an elite MySQL Architect. Write highly accurate SQL based STRICTLY on the schemas provided.
    CRITICAL RULES FOR FULL ACCURACY & SECURITY:
    1. READ-ONLY: ONLY generate `SELECT` statements. REFUSE to generate DROP, DELETE, UPDATE.
    2. NEVER hallucinate tables. Use `sales_order` for all order/transaction data.
    3. NUMBERED TABLES: MUST wrap `2017_budgets` in backticks (e.g., FROM `2017_budgets`).
    4. SPACES IN COLUMNS: Any column name with a space MUST be enclosed in backticks.
    5. PREFIX COLUMNS: Always prefix columns with their table names when joining.
    6. GROUP BY STRICTNESS: If you use `GROUP BY`, either group by ALL non-aggregated columns in SELECT, or wrap non-aggregated columns in MAX() or MIN().
    7. Return ONLY the raw executable SQL string. No markdown.
    Schema: {schema}
    User Question: {question}
    SQL Query:"""
    sql_chain = ChatPromptTemplate.from_template(sql_template) | llm_heavy.bind(stop=["\nSQLResult:"]) | StrOutputParser()
    
    # AGENT 4: Final Synthesizer
    response_template = """You are the data analysis layer. Formulate a precise answer based on the query context.
    - If raw database results are provided, use them to answer explicitly.
    - If results are empty or error out, state clearly that no records matched.
    User Question: {question}
    SQL Query Executed: {query}
    Raw Database Result Data: {result}
    Natural Language Answer:"""
    response_chain = ChatPromptTemplate.from_template(response_template) | llm_heavy | StrOutputParser()
    
    # AGENT 5: Visualization Architect
    vis_template = """You are an expert Data Visualization Architect. Analyze the available dataframe columns and determine if a chart can be built.
    RULES:
    1. If the data is a single scalar value, set "is_visualizable" to false.
    2. If the data has categories and a numeric metric, set "is_visualizable" to true.
    3. 'x_axis' must be a categorical/descriptive column. 'y_axis' MUST be a purely numeric column.
    4. ONLY pick columns from the EXACT 'Available Columns' list below. Do not guess.
    
    Available Columns: {columns}
    Sample Data (First row): {sample_data}
    User Question: {question}
    
    Respond ONLY with JSON:
    {{
        "is_visualizable": true/false,
        "chart_type": "bar" or "line" or "scatter",
        "x_axis": "exact_column_name_for_x",
        "y_axis": "exact_column_name_for_y",
        "title": "Short title for chart"
    }}"""
    vis_chain = ChatPromptTemplate.from_template(vis_template) | llm_light | JsonOutputParser()
    
    return router_chain, extractor_chain, sql_chain, response_chain, vis_chain

router_chain, extractor_chain, sql_chain, response_chain, vis_chain = init_agents()

# --- SQL Execution via Pandas (For Visualization Support) ---
def execute_query_to_df(sql_query):
    clean_sql = sql_query.replace("```sql", "").replace("```", "").strip()
    match = re.search(r'(?i)select\s', clean_sql)
    if match:
        clean_sql = clean_sql[match.start():]
    else:
        return f"Database Execution Error: No valid SELECT statement generated."
        
    try:
        # Use SQLAlchemy text() to securely execute the string into a Pandas DataFrame
        with db._engine.connect() as conn:
            df = pd.read_sql(text(clean_sql), conn)
        return df
    except Exception as e:
        return f"Database Execution Error: {str(e)}"

# --- UI Session History Rendering (Persistent Memory) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
        # Safely redraw historical charts
        chart_config = msg.get("chart_config")
        raw_data = msg.get("raw_result")
        if chart_config and isinstance(raw_data, pd.DataFrame):
            st.divider()
            st.subheader(chart_config.get("title", "Data Visualization"))
            try:
                x_col = chart_config["x_axis"]
                y_col = chart_config["y_axis"]
                if chart_config["chart_type"] == "line":
                    st.line_chart(data=raw_data, x=x_col, y=y_col)
                elif chart_config["chart_type"] == "scatter":
                    st.scatter_chart(data=raw_data, x=x_col, y=y_col)
                else:
                    st.bar_chart(data=raw_data, x=x_col, y=y_col)
            except Exception:
                st.warning("Historical chart data format shifted.")
                
        # Safely redraw historical logs
        if msg.get("telemetry"):
            with st.expander("🛠️ System Telemetry, Logs & Execution Matrix"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### ⏱️ Performance Telemetry")
                    st.json(msg["telemetry"])
                with col2:
                    st.markdown("### 🖥️ Generated SQL Code")
                    st.code(msg.get("sql", ""), language="sql")
                    st.markdown("### 📊 Raw Database Matrix")
                    if isinstance(raw_data, pd.DataFrame):
                        st.dataframe(raw_data, use_container_width=True)
                    else:
                        st.write(raw_data)

# --- Main Application Pipeline ---
if question := st.chat_input("Query transactions, products, regions or targets..."):
    # 1. SAVE USER QUESTION TO MEMORY
    st.session_state.messages.append({"role": "user", "content": question})
    telemetry = {}
    total_start = time.time()
    
    with st.chat_message("user"):
        st.write(question)
    
    with st.chat_message("assistant"):
        try:
            t0 = time.time()
            with st.spinner("Analyzing request intent..."):
                route_decision = router_chain.invoke({"question": question})
            telemetry["1. Intent Routing (Agent 1)"] = f"{(time.time() - t0):.2f}s"
            
            # --- CASUAL CHAT PATH ---
            if not route_decision.get("is_db_query", False):
                casual_reply = route_decision.get("casual_response", "Hello! I am your database assistant.")
                st.write(casual_reply)
                # Save casual reply to memory
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": casual_reply
                })
            
            # --- DATABASE PATH ---
            else:
                t0 = time.time()
                with st.spinner("Isolating structural tables..."):
                    extraction_result = extractor_chain.invoke({
                        "question": question, 
                        "db_directory": DATABASE_DIRECTORY
                    })
                    selected_tables = extraction_result.get("relevant_tables", [])
                telemetry["2. Schema Extraction (Agent 2)"] = f"{(time.time() - t0):.2f}s"
                
                validated_tables = [t for t in ALL_TABLES if t.lower() in [st.lower() for st in selected_tables]]
                is_metadata_query = any(word in question.lower() for word in ["about database", "what tables", "schema"])
                
                generated_sql = ""
                raw_data = ""
                string_data = ""
                
                if is_metadata_query:
                    filtered_schema = DATABASE_DIRECTORY
                    string_data = "User requested metadata overview."
                else:
                    filtered_schema = db.get_table_info(table_names=validated_tables) if validated_tables else db.get_table_info() 
                
                if not is_metadata_query:
                    t0 = time.time()
                    with st.spinner("Compiling database SQL script..."):
                        generated_sql = sql_chain.invoke({
                            "schema": filtered_schema,
                            "question": question
                        })
                    telemetry["3. SQL Compilation (Agent 3)"] = f"{(time.time() - t0):.2f}s"
                    
                    t0 = time.time()
                    raw_data = execute_query_to_df(generated_sql)
                    telemetry["4. Database Execution (MySQL)"] = f"{(time.time() - t0):.2f}s"
                    
                    if isinstance(raw_data, pd.DataFrame):
                        string_data = raw_data.head(15).to_string() if not raw_data.empty else "Empty DataFrame (No records found)"
                    else:
                        string_data = raw_data
                
                t0 = time.time()
                with st.spinner("Synthesizing clear insight response..."):
                    final_answer = response_chain.invoke({
                        "question": question,
                        "query": generated_sql if generated_sql else "Metadata Structural Request",
                        "result": string_data
                    })
                    st.write(final_answer)
                telemetry["5. Insight Synthesis (Agent 4)"] = f"{(time.time() - t0):.2f}s"
                
                chart_config = None
                if isinstance(raw_data, pd.DataFrame) and not raw_data.empty and len(raw_data.columns) >= 2:
                    t0 = time.time()
                    with st.spinner("Designing data visualization..."):
                        try:
                            chart_config = vis_chain.invoke({
                                "columns": raw_data.columns.tolist(),
                                "sample_data": str(raw_data.iloc[0].to_dict()),
                                "question": question
                            })
                            telemetry["6. Visualization Design (Agent 5)"] = f"{(time.time() - t0):.2f}s"
                            
                            if chart_config.get("is_visualizable"):
                                st.divider()
                                st.subheader(chart_config.get("title", "Data Visualization"))
                                x_col = chart_config.get("x_axis")
                                y_col = chart_config.get("y_axis")
                                
                                if x_col in raw_data.columns and y_col in raw_data.columns:
                                    raw_data[y_col] = pd.to_numeric(raw_data[y_col], errors='coerce')
                                    chart_type = chart_config.get("chart_type", "bar")
                                    if chart_type == "line":
                                        st.line_chart(data=raw_data, x=x_col, y=y_col)
                                    elif chart_type == "scatter":
                                        st.scatter_chart(data=raw_data, x=x_col, y=y_col)
                                    else:
                                        st.bar_chart(data=raw_data, x=x_col, y=y_col)
                                else:
                                    st.warning("Visualization skipped: Invalid columns selected.")
                        except Exception as vis_err:
                            st.warning("Visualization layer bypassed.")

                telemetry["Total Request Time"] = f"{(time.time() - total_start):.2f}s"
                
                with st.expander("🛠️ System Telemetry, Logs & Execution Matrix"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### ⏱️ Performance Telemetry")
                        st.json(telemetry)
                        if chart_config:
                            st.markdown("### 🎨 Visualization Blueprint")
                            st.json(chart_config)
                    with col2:
                        st.markdown("### 🖥️ Generated SQL Code")
                        st.code(generated_sql, language="sql")
                        st.markdown("### 📊 Raw Database Matrix")
                        if isinstance(raw_data, pd.DataFrame):
                            st.dataframe(raw_data, use_container_width=True)
                        else:
                            st.error(raw_data)

                # 2. SAVE FULL DATABASE RESPONSE & CHART TO MEMORY
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_answer,
                    "sql": generated_sql,
                    "raw_result": raw_data,
                    "chart_config": chart_config,
                    "telemetry": telemetry
                })

        except Exception as err:
            st.error(f"Critical System Core Runtime Exception: {err}")

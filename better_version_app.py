import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

# --- Secure Credentials Retrieval ---
# Reads parameters securely from local .streamlit/secrets.toml or cloud settings
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
DB_PASSWORD = st.secrets["DB_PASSWORD"]

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Enterprise Database Assistant", page_icon="📊", layout="centered")
st.title("📊 Enterprise Database AI Assistant")
st.caption("Production Build v2.0: Strict Routing, Table Sanitation, and Deterministic Analysis")

# --- High-Level Database Directory Map ---
# Matches your 6-Table Relational Blueprint perfectly for zero-token-starvation indexing
DATABASE_DIRECTORY = """
Available Tables and Structural Descriptions:
1. customers Table: Stores corporate/individual client profiles. Key columns: [Customer Index, Customer Names].
2. products Table: Inventory item registry. Key columns: [Index, Product Name].
3. budgets Table: 2017 financial target limits mapped to specific products. Key columns: [Product Name, 2017 Budgets].
4. region Table: Extensive regional demographics and locations. Key columns: [id, name, county, state_code, state, Region, population, median_income].
5. sales Table: The main transaction ledger. Key columns: [OrderNumber, OrderDate, Customer Name Index, Channel, Currency Code, Delivery Region Index, Product Description Index, Order Quantity, Unit Price, Line Total, Total Unit Cost].
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
    # Pull precise table naming directly from active engine session
    ALL_TABLES = db.get_usable_table_names()
except Exception as e:
    st.error(f"Critical Database Connection Failure: {e}")
    st.stop()

# --- Multi-Agent Architecture Engine ---
@st.cache_resource
def init_agents():
    # Production models based on official Groq migration paths
    LIGHT_MODEL = "openai/gpt-oss-20b"   # Standard Groq model format (Update if using custom)
    HEAVY_MODEL = "openai/gpt-oss-120b"  # Standard Groq model format (Update if using custom)
    
    llm_light = ChatGroq(model=LIGHT_MODEL, temperature=0)
    llm_heavy = ChatGroq(model=HEAVY_MODEL, temperature=0)
    
    # ----------------------------------------------------
    # AGENT 1: The Guard Dog (Hardened Router)
    # ----------------------------------------------------
    router_template = """You are a strict security and route classification agent.
    Analyze the user's input phrase. You must decide if it is purely casual chitchat (greetings like 'hi', 'how are you', 'tell me a joke') OR if it mentions, requests, or targets structural/analytical information about the connected database or its tables (e.g. 'tell me about my database', 'what tables do I have?', 'find the max sales').
    
    CRITICAL RULE: If the user refers to "database", "tables", "schema", or asks a question matching business data tracking, "is_db_query" MUST be true.
    
    Respond ONLY with a JSON object matching this structure:
    {{
        "is_db_query": true or false,
        "casual_response": "Write a friendly greeting ONLY if is_db_query is false, otherwise leave blank string"
    }}
    
    User Input: {question}
    Response (JSON only):"""
    router_prompt = ChatPromptTemplate.from_template(router_template)
    router_chain = router_prompt | llm_light | JsonOutputParser()

    # ----------------------------------------------------
    # AGENT 2: The Table Extractor
    # ----------------------------------------------------
    extractor_template = """You are an indexing database administrator assistant. Look at the user's query and the active system directory.
    Output which explicit tables are needed to satisfy this question. If they are asking about the overall database information itself or multiple structures, return all relevant tables.
    
    System Directory Map:
    {db_directory}
    
    User Question: {question}
    
    Respond ONLY with a JSON object matching this structure:
    {{
        "relevant_tables": ["table1", "table2"]
    }}
    If no structural tables are matches, return an empty array [].
    Response (JSON only):"""
    extractor_prompt = ChatPromptTemplate.from_template(extractor_template)
    extractor_chain = extractor_prompt | llm_light | JsonOutputParser()

    # ----------------------------------------------------
    # AGENT 3: Deterministic SQL Engineering Engine
    # ----------------------------------------------------
    sql_template = """Based on the exact table schemas verified below, write an accurate, valid executable MySQL query to answer the question.
    - Always use clear explicitly defined JOIN paths based on the keys shown.
    - Return ONLY the raw SQL code string. 
    - Absolutely DO NOT wrap output in markdown blocks like ```sql or include text explanations.
    
    Table Schema Context:
    {schema}
    
    User Question: {question}
    SQL Query:"""
    sql_prompt = ChatPromptTemplate.from_template(sql_template)
    sql_chain = sql_prompt | llm_heavy.bind(stop=["\nSQLResult:"]) | StrOutputParser()
    
    # ----------------------------------------------------
    # AGENT 4: Final Insight Synthesizer
    # ----------------------------------------------------
    response_template = """You are the master data analysis layer. Your objective is to formulate a precise, accurate answer based strictly on the query context provided below.
    - If raw database results are provided, use them to explicitly answer the metrics.
    - If the user was asking about the structural layout of their database, summarize the database directory metadata provided.
    - Never give a generic description of what a database is unless explicitly asked for a generic textbook definition. Speak directly about this specific database.
    - If results are empty, state clearly that no records matched that filter within the database tables.

    Database Directory Blueprint:
    {db_directory}

    User Question: {question}
    SQL Query Executed: {query}
    Raw Database Result Data: {result}
    
    Natural Language Answer:"""
    response_prompt = ChatPromptTemplate.from_template(response_template)
    response_chain = response_prompt | llm_heavy | StrOutputParser()
    
    return router_chain, extractor_chain, sql_chain, response_chain

router_chain, extractor_chain, sql_chain, response_chain = init_agents()

def execute_query(sql_query):
    clean_sql = sql_query.strip().replace("```sql", "").replace("```", "").strip()
    if not clean_sql or clean_sql.lower().startswith("select") is False:
        return "No executable query generated."
    try:
        return db.run(clean_sql)
    except Exception as e:
        return f"Database Execution Error: {str(e)}"

# --- UI Session History Rendering ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "sql" in msg and msg["sql"]:
            with st.expander("🛠️ Production Logs & Execution Parameters"):
                st.text(f"Validated Tables Targeted: {msg.get('tables_used', 'None')}")
                st.code(msg["sql"], language="sql")
                st.text("Raw Matrix Output:")
                st.write(msg["raw_result"])

# --- Main Dynamic Application Pipeline ---
if question := st.chat_input("Query transactions, products, regions or targets..."):
    with st.chat_message("user"):
        st.write(question)
    st.session_state.messages.append({"role": "user", "content": question})
    
    with st.chat_message("assistant"):
        try:
            # STEP 1: Route Inspection
            with st.spinner("Analyzing request intent..."):
                route_decision = router_chain.invoke({"question": question})
            
            # Case A: Pure Out-Of-Bounds Casual Conversation
            if not route_decision.get("is_db_query", False):
                casual_reply = route_decision.get("casual_response", "Hello! I am connected to your transactional database. How can I help you extract insights today?")
                st.write(casual_reply)
                st.session_state.messages.append({"role": "assistant", "content": casual_reply})
            
            # Case B: Execution Pipeline for Database Insights
            else:
                # STEP 2: Extract and Sanitize Target Tables
                with st.spinner("Isolating structural tables..."):
                    extraction_result = extractor_chain.invoke({
                        "question": question, 
                        "db_directory": DATABASE_DIRECTORY
                    })
                    selected_tables = extraction_result.get("relevant_tables", [])
                
                # Defensively align text case variants to match physical database names precisely
                validated_tables = []
                for table in selected_tables:
                    match = next((t for t in ALL_TABLES if t.lower() == table.lower()), None)
                    if match:
                        validated_tables.append(match)
                
                # Determine context scope based on user seeking specific metrics vs metadata overview
                is_metadata_query = any(word in question.lower() for word in ["about database", "what tables", "show database", "schema", "tables do i have"])
                
                generated_sql = ""
                raw_data = ""
                
                if is_metadata_query:
                    # CASE 1: User wants an overview of the structural layout itself
                    filtered_schema = DATABASE_DIRECTORY
                    raw_data = "User requested structural configuration metadata overview."
                else:
                    # CASE 2: Specific data query execution path (Text-to-SQL)
                    if validated_tables:
                        filtered_schema = db.get_table_info(table_names=validated_tables)
                    else:
                        filtered_schema = db.get_table_info() # Fallback to prevent data starvation
                
                # STEP 3: Formulate and Execute SQL Command
                with st.spinner("Compiling database SQL script..."):
                    if not is_metadata_query:
                        generated_sql = sql_chain.invoke({
                            "schema": filtered_schema,
                            "question": question
                        })
                        raw_data = execute_query(generated_sql)
                    
                    # Render technical log telemetry metrics
                    if generated_sql:
                        with st.expander("🛠️ Production Logs & Execution Parameters"):
                            st.text(f"Validated Tables Targeted: {', '.join(validated_tables) if validated_tables else 'Fallback (All)'}")
                            st.code(generated_sql, language="sql")
                            st.text("Raw Matrix Output:")
                            st.write(raw_data)
                
                # STEP 4: Absolute Deterministic Synthesis
                with st.spinner("Synthesizing clear insight response..."):
                    final_answer = response_chain.invoke({
                        "db_directory": DATABASE_DIRECTORY,
                        "question": question,
                        "query": generated_sql if generated_sql else "Metadata Structural Request (No SQL Run)",
                        "result": raw_data
                    })
                    st.write(final_answer)
                    
                    # Save records state to preserve session runtime history integrity
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": final_answer,
                        "sql": generated_sql,
                        "raw_result": raw_data,
                        "tables_used": ', '.join(validated_tables) if validated_tables else 'None/Overview'
                    })
                    
        except Exception as err:
            st.error(f"Critical System Core Runtime Exception: {err}")
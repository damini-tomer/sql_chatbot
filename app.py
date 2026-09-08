import os
import streamlit as st
from langchain_groq import ChatGroq 
from langchain_community.utilities import SQLDatabase 
from langchain_core.prompts import ChatPromptTemplate 
from langchain_core.output_parsers import StrOutputParser 
from langchain_core.runnables import RunnablePassthrough 

# --- Secure Credentials Retrieval ---
# Streamlit reads these from .streamlit/secrets.toml locally, or from Cloud settings in production
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
DB_PASSWORD = st.secrets["DB_PASSWORD"]

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Database AI Assistant", page_icon="💬", layout="centered")
st.title("💬 Database AI Chatbot")
st.caption("Ask your MySQL database questions in natural language")

# --- Database Connection Initialization ---
@st.cache_resource
def init_database():
    host = 'localhost'
    port = '3306'
    username = 'root'
    database_schema = 'text_to_sql1'
    # Password injected securely from secrets
    mysql_uri = f"mysql+pymysql://{username}:{DB_PASSWORD}@{host}:{port}/{database_schema}"
    return SQLDatabase.from_uri(mysql_uri, sample_rows_in_table_info=2)

try:
    db = init_database()
except Exception as e:
    st.error(f"Failed to connect to the database: {e}")
    st.stop()

# --- Model & Chain Setup ---
@st.cache_resource
def init_chains():
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

    sql_template = """Based on the table schema below, write a SQL query that answers the user's question. 
Only provide the SQL query. Do not include any markdown formatting (like ```sql), explanations, or line breaks.

Table Schema: {schema}
Question: {question}
SQL Query:"""
    sql_prompt = ChatPromptTemplate.from_template(sql_template)

    response_template = """You are a helpful assistant analyzer. Based on the user's question, the SQL query executed, and the raw data returned from the database, write a clear and concise response in plain, natural language.

User Question: {question}
SQL Query Executed: {query}
Raw Database Result: {result}

Natural Language Answer:"""
    response_prompt = ChatPromptTemplate.from_template(response_template)

    def get_schema(_):
        return db.get_table_info()

    sql_chain = (
        RunnablePassthrough.assign(schema=get_schema) 
        | sql_prompt 
        | llm.bind(stop=["\nSQLResult:"]) 
        | StrOutputParser()
    )

    return sql_chain, response_prompt, llm

sql_chain, response_prompt, llm = init_chains()

def execute_query(inputs):
    clean_sql = inputs["query"].strip().replace("```sql", "").replace("```", "").strip()
    try:
        return db.run(clean_sql)
    except Exception as e:
        return f"Execution Error: {str(e)}"

# --- Chat History State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history on rerun
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "sql" in msg:
            with st.expander("🛠️ View Executed Query Details"):
                st.code(msg["sql"], language="sql")
                st.text("Raw Result:")
                st.write(msg["raw_result"])

# --- Chat Interface Execution ---
if question := st.chat_input("Ask something about your data..."):
    
    # 1. Display user message in chat container
    with st.chat_message("user"):
        st.write(question)
    st.session_state.messages.append({"role": "user", "content": question})

    # 2. Generate response block
    with st.chat_message("assistant"):
        with st.spinner("Querying database..."):
            try:
                intermediate_pipeline = (
                    RunnablePassthrough.assign(query=sql_chain) 
                    | RunnablePassthrough.assign(result=execute_query)
                )
                
                # Fetch SQL and DB responses
                data_context = intermediate_pipeline.invoke({"question": question})
                generated_sql = data_context["query"]
                raw_data = data_context["result"]
                
                # Render expanding technical blocks
                with st.expander("🛠️ View Executed Query Details"):
                    st.code(generated_sql, language="sql")
                    st.text("Raw Result:")
                    st.write(raw_data)
                
                # Generate final narrative 
                final_answer = (response_prompt | llm | StrOutputParser()).invoke(data_context)
                st.write(final_answer)
                
                # Save data package into state memory
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_answer,
                    "sql": generated_sql,
                    "raw_result": raw_data
                })
                
            except Exception as err:
                error_msg = f"An unexpected error occurred: {err}"
                st.error(error_msg)

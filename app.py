import streamlit as st
import sqlalchemy
from sqlalchemy import create_engine
import time

# Page Configuration
st.set_page_config(
    page_title="Jewelry ERP System",
    page_icon="💎",
    layout="wide"
)

# Title
st.title("💎 Jewelry ERP System")

# Database Connection
st.subheader("System Status")

def check_db_connection():
    # Update this connection string to match your docker-compose settings
    # user:password@host:port/database
    db_connection_str = 'mysql+pymysql://root:dbpassword@127.0.0.1:3306/jewelry_db'
    
    try:
        engine = create_engine(db_connection_str)
        connection = engine.connect()
        st.success("✅ Database Connected: MariaDB 10.11")
        connection.close()
    except Exception as e:
        st.error(f"❌ Database Connection Failed: {e}")
        st.info("Make sure the docker containers are running: 'docker-compose up -d'")

# Check status
with st.spinner('Checking database connection...'):
    time.sleep(1) # Simulate check time
    check_db_connection()

st.divider()
st.write("Welcome to the Jewelry ERP System.")

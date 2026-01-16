#Filename: utils/db_two_connections.py
# Filename: utils/full_connection_suite.py
# Purpose: A single script to test and demonstrate the two different database 
#          connection methods and prove the necessity of the SSL parameter.

import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv

def test_direct_psycopg2_connection():
    """Tests the direct, low-level psycopg2 connection."""
    print("--- 1. Testing Direct Connection (psycopg2) ---")
    try:
        conn_string = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        conn = psycopg2.connect(conn_string)
        print("✅ SUCCESS: Direct connection works. Credentials are correct.")
        conn.close()
    except Exception as e:
        print(f"🛑 UNEXPECTED FAILURE: Direct connection failed. Error: {e}")
    print("-" * 40)


def test_sqlalchemy_connection():
    """Tests the SQLAlchemy connection, which LangChain uses."""
    print("--- 2. Testing ORM Connection (SQLAlchemy) ---")
    
    # Test A: Without the SSL parameter (This is expected to fail)
    print("\n[Test A] SQLAlchemy connection WITHOUT '?sslmode=require'...")
    try:
        db_uri_fail = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}".format(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        engine_fail = create_engine(db_uri_fail)
        conn_fail = engine_fail.connect()
        print("🛑 UNEXPECTED SUCCESS: Connection without SSL worked.")
        conn_fail.close()
    except Exception as e:
        print(f"⚠️ EXPECTED FAILURE: As predicted, the connection failed without SSL. Error: {e}")

    # Test B: With the SSL parameter (This is expected to succeed)
    print("\n[Test B] SQLAlchemy connection WITH '?sslmode=require'...")
    try:
        db_uri_success = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require".format(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        engine_success = create_engine(db_uri_success)
        conn_success = engine_success.connect()
        print("✅ SUCCESS: SQLAlchemy connection with SSL parameter works!")
        conn_success.close()
    except Exception as e:
        print(f"🛑 UNEXPECTED FAILURE: Connection with SSL failed. Error: {e}")
    print("-" * 40)


if __name__ == "__main__":
    load_dotenv()
    test_direct_psycopg2_connection()
    test_sqlalchemy_connection()
##--end-of-file --

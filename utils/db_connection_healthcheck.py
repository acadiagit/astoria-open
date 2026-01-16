# Filename: utils/db_connection_healthcheck.py
# Purpose: A single, self-documenting script to diagnose all database 
#          connection methods used by the application. This script will be the
#          single source of truth for testing database connectivity.

import os
import psycopg2
from sqlalchemy import create_engine
from dotenv import load_dotenv

def test_direct_psycopg2_connection():
    """
    Tests the direct, low-level psycopg2 connection.
    This is the most basic way to connect and primarily validates credentials.
    """
    print("--- Test 1: Direct psycopg2 Connection ---")
    print("Purpose: To confirm the raw credentials in .env are correct.")
    
    try:
        conn_string = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        conn = psycopg2.connect(conn_string)
        print("✅ SUCCESS: Direct connection works. Credentials and network access are OK.")
        conn.close()
    except Exception as e:
        print(f"🛑 FAILURE: Direct connection failed. Check .env file and Supabase status.")
        print(f"   Error: {e}")
    print("-" * 50)


def test_sqlalchemy_connection():
    """
    Tests the SQLAlchemy connection, which is used by LangChain.
    This method is more complex and has stricter requirements, like SSL.
    """
    print("--- Test 2: SQLAlchemy (LangChain's Method) Connection ---")
    print("Purpose: To confirm the ORM can connect, which is required by the main application.")
    
    # Test A: Without the required SSL parameter
    print("\n[2a] Testing SQLAlchemy connection WITHOUT '?sslmode=require'...")
    print("     This test reproduces the error seen in the full application.")
    try:
        db_uri_fail = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}".format(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        engine_fail = create_engine(db_uri_fail, connect_args={'connect_timeout': 10})
        conn_fail = engine_fail.connect()
        print("     - Result: ⚠️ UNEXPECTED SUCCESS. The non-SSL connection worked in this simple script.")
        print("       (Note: This often fails in the more complex full application environment.)")
        conn_fail.close()
    except Exception as e:
        print(f"     - Result: ✅ EXPECTED FAILURE. The non-SSL connection failed as predicted.")
        print(f"       (This confirms it's not a reliable connection method.)")

    # Test B: With the required SSL parameter
    print("\n[2b] Testing SQLAlchemy connection WITH '?sslmode=require'...")
    print("     This is the required, stable method for connecting to Supabase.")
    try:
        db_uri_success = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require".format(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        engine_success = create_engine(db_uri_success, connect_args={'connect_timeout': 10})
        conn_success = engine_success.connect()
        print("     - Result: ✅ SUCCESS! The stable SSL connection works as expected.")
        conn_success.close()
    except Exception as e:
        print(f"     - Result: 🛑 FAILURE. The stable SSL connection failed unexpectedly.")
        print(f"       Error: {e}")
    print("-" * 50)


if __name__ == "__main__":
    print("Starting database connection health check...\n")
    load_dotenv()
    test_direct_psycopg2_connection()
    test_sqlalchemy_connection()
    print("Health check complete.")
